//! Supervise the long-running `qibocal` processes started from the interface.
//!
//! Every managed process keeps a bounded log, streams its output to the
//! interface through events, and is terminated gracefully when the launcher
//! quits so notebook tunnels and report servers never outlive the window.

use std::collections::HashMap;
use std::io::{BufRead, BufReader, Read};
use std::path::PathBuf;
use std::process::{Child, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Emitter, Manager, State};

use crate::qibocal;

/// Lines kept per process: enough to diagnose a failed start, bounded for memory.
const LOG_LIMIT: usize = 2000;
const POLL_INTERVAL: Duration = Duration::from_millis(400);
const STOP_GRACE: Duration = Duration::from_secs(6);

pub const LOG_EVENT: &str = "launcher://log";
pub const PROCESS_EVENT: &str = "launcher://process";

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ProcessInfo {
    pub id: String,
    /// `server` or `notebook`, used to pick the interface affordances.
    pub kind: String,
    pub label: String,
    pub detail: String,
    pub command: Vec<String>,
    pub url: Option<String>,
    /// `running`, `stopping`, `exited` or `failed`.
    pub status: String,
    pub exit_code: Option<i32>,
    pub started_at: u64,
}

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct LogEvent {
    id: String,
    line: String,
}

struct Entry {
    info: ProcessInfo,
    log: Vec<String>,
    child: Option<Child>,
}

#[derive(Default)]
pub struct Supervisor {
    entries: Mutex<HashMap<String, Entry>>,
    counter: AtomicU64,
}

fn now_millis() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|elapsed| elapsed.as_millis() as u64)
        .unwrap_or(0)
}

/// Pick the first absolute URL in a line, as printed by the notebook launcher.
pub fn extract_url(line: &str) -> Option<String> {
    let start = line.find("http://").or_else(|| line.find("https://"))?;
    let rest = &line[start..];
    let end = rest
        .find(|character: char| character.is_whitespace() || "\"'<>()[]".contains(character))
        .unwrap_or(rest.len());
    let url = rest[..end].trim_end_matches(['.', ',', ';', ':']);
    if url.len() > "http://".len() {
        Some(url.to_string())
    } else {
        None
    }
}

impl Supervisor {
    fn next_id(&self) -> String {
        format!("process-{}", self.counter.fetch_add(1, Ordering::SeqCst) + 1)
    }

    fn snapshot(&self, id: &str) -> Option<ProcessInfo> {
        let entries = self.entries.lock().ok()?;
        entries.get(id).map(|entry| entry.info.clone())
    }

    pub fn list(&self) -> Vec<ProcessInfo> {
        let Ok(entries) = self.entries.lock() else {
            return Vec::new();
        };
        let mut processes: Vec<ProcessInfo> =
            entries.values().map(|entry| entry.info.clone()).collect();
        processes.sort_by_key(|process| process.started_at);
        processes
    }

    pub fn log(&self, id: &str) -> Vec<String> {
        let Ok(entries) = self.entries.lock() else {
            return Vec::new();
        };
        entries
            .get(id)
            .map(|entry| entry.log.clone())
            .unwrap_or_default()
    }

    fn record(&self, app: &AppHandle, id: &str, line: String, detect_url: bool) {
        let mut changed = None;
        if let Ok(mut entries) = self.entries.lock() {
            let Some(entry) = entries.get_mut(id) else {
                return;
            };
            if entry.log.len() >= LOG_LIMIT {
                entry.log.remove(0);
            }
            entry.log.push(line.clone());
            if detect_url && entry.info.url.is_none() {
                if let Some(url) = extract_url(&line) {
                    entry.info.url = Some(url);
                    changed = Some(entry.info.clone());
                }
            }
        }
        let _ = app.emit(
            LOG_EVENT,
            LogEvent {
                id: id.to_string(),
                line,
            },
        );
        if let Some(info) = changed {
            let _ = app.emit(PROCESS_EVENT, info);
        }
    }

    fn finish(&self, app: &AppHandle, id: &str, code: Option<i32>) {
        let mut changed = None;
        if let Ok(mut entries) = self.entries.lock() {
            if let Some(entry) = entries.get_mut(id) {
                entry.child = None;
                entry.info.exit_code = code;
                entry.info.status = match code {
                    Some(0) | None => "exited".to_string(),
                    Some(_) => "failed".to_string(),
                };
                changed = Some(entry.info.clone());
            }
        }
        if let Some(info) = changed {
            let _ = app.emit(PROCESS_EVENT, info);
        }
    }

    pub fn spawn(
        &self,
        app: &AppHandle,
        kind: &str,
        label: String,
        detail: String,
        arguments: Vec<String>,
        working_directory: Option<PathBuf>,
        url: Option<String>,
    ) -> Result<ProcessInfo, String> {
        let program = qibocal::executable()?;
        let mut command = qibocal::command(&program);
        command
            .args(&arguments)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        if let Some(directory) = working_directory {
            command.current_dir(directory);
        }
        let mut child = command
            .spawn()
            .map_err(|error| format!("Could not start '{}': {error}", program.display()))?;

        let stdout = child.stdout.take();
        let stderr = child.stderr.take();
        let id = self.next_id();
        let detect_url = url.is_none();
        let info = ProcessInfo {
            id: id.clone(),
            kind: kind.to_string(),
            label,
            detail,
            command: std::iter::once(program.display().to_string())
                .chain(arguments)
                .collect(),
            url,
            status: "running".to_string(),
            exit_code: None,
            started_at: now_millis(),
        };

        if let Ok(mut entries) = self.entries.lock() {
            entries.insert(
                id.clone(),
                Entry {
                    info: info.clone(),
                    log: Vec::new(),
                    child: Some(child),
                },
            );
        } else {
            return Err("The process supervisor is unavailable.".to_string());
        }

        if let Some(stream) = stdout {
            pump(app.clone(), id.clone(), stream, detect_url);
        }
        if let Some(stream) = stderr {
            pump(app.clone(), id.clone(), stream, detect_url);
        }
        monitor(app.clone(), id);

        let _ = app.emit(PROCESS_EVENT, info.clone());
        Ok(info)
    }

    /// Ask the process to stop, leaving it time to clean up tunnels and workers.
    pub fn stop(&self, id: &str) -> Result<(), String> {
        let pid = {
            let mut entries = self
                .entries
                .lock()
                .map_err(|_| "The process supervisor is unavailable.".to_string())?;
            let entry = entries
                .get_mut(id)
                .ok_or_else(|| format!("Process '{id}' is not managed by the launcher."))?;
            match entry.child.as_ref() {
                Some(child) => {
                    entry.info.status = "stopping".to_string();
                    child.id()
                }
                None => return Ok(()),
            }
        };

        terminate(pid);

        let deadline = SystemTime::now() + STOP_GRACE;
        loop {
            std::thread::sleep(Duration::from_millis(100));
            let finished = {
                let Ok(mut entries) = self.entries.lock() else {
                    return Ok(());
                };
                match entries.get_mut(id).and_then(|entry| entry.child.as_mut()) {
                    Some(child) => matches!(child.try_wait(), Ok(Some(_)) | Err(_)),
                    None => true,
                }
            };
            if finished {
                return Ok(());
            }
            if SystemTime::now() >= deadline {
                break;
            }
        }

        if let Ok(mut entries) = self.entries.lock() {
            if let Some(child) = entries.get_mut(id).and_then(|entry| entry.child.as_mut()) {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
        Ok(())
    }

    pub fn forget(&self, id: &str) -> Result<(), String> {
        let mut entries = self
            .entries
            .lock()
            .map_err(|_| "The process supervisor is unavailable.".to_string())?;
        match entries.get(id) {
            Some(entry) if entry.child.is_some() => {
                Err("Stop the process before removing it from the list.".to_string())
            }
            _ => {
                entries.remove(id);
                Ok(())
            }
        }
    }

    /// Terminate every managed process, used when the launcher quits.
    pub fn shutdown(&self) {
        let running: Vec<String> = {
            let Ok(entries) = self.entries.lock() else {
                return;
            };
            entries
                .iter()
                .filter(|(_, entry)| entry.child.is_some())
                .map(|(id, _)| id.clone())
                .collect()
        };
        for id in running {
            let _ = self.stop(&id);
        }
    }
}

#[cfg(unix)]
fn terminate(pid: u32) {
    // SIGTERM lets the CLI close SSH tunnels and remote notebook workers.
    unsafe {
        libc::kill(pid as i32, libc::SIGTERM);
    }
}

#[cfg(windows)]
fn terminate(pid: u32) {
    let _ = std::process::Command::new("taskkill")
        .args(["/PID", &pid.to_string(), "/T", "/F"])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();
}

fn pump<R: Read + Send + 'static>(app: AppHandle, id: String, stream: R, detect_url: bool) {
    std::thread::spawn(move || {
        let reader = BufReader::new(stream);
        for line in reader.lines() {
            let Ok(line) = line else { break };
            let supervisor = app.state::<Supervisor>();
            supervisor.record(&app, &id, line, detect_url);
        }
    });
}

fn monitor(app: AppHandle, id: String) {
    std::thread::spawn(move || loop {
        std::thread::sleep(POLL_INTERVAL);
        let supervisor = app.state::<Supervisor>();
        let status = {
            let Ok(mut entries) = supervisor.entries.lock() else {
                return;
            };
            match entries.get_mut(&id) {
                Some(entry) => match entry.child.as_mut() {
                    Some(child) => child.try_wait(),
                    None => return,
                },
                None => return,
            }
        };
        match status {
            Ok(Some(exit)) => {
                supervisor.finish(&app, &id, exit.code());
                return;
            }
            Ok(None) => {}
            Err(_) => {
                supervisor.finish(&app, &id, None);
                return;
            }
        }
    });
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ServerOptions {
    /// `server`, `dev` or `client`.
    pub mode: String,
    pub directory: Option<String>,
    pub host: String,
    pub port: u16,
    pub auth: bool,
    pub frontend_port: Option<u16>,
}

#[tauri::command]
pub fn start_server(
    app: AppHandle,
    supervisor: State<Supervisor>,
    options: ServerOptions,
) -> Result<ProcessInfo, String> {
    let mut arguments = vec!["report".to_string(), options.mode.clone()];
    let mut working_directory = None;
    match options.mode.as_str() {
        "server" | "dev" => {
            let directory = options
                .directory
                .clone()
                .filter(|value| !value.trim().is_empty())
                .ok_or_else(|| "Choose the directory holding the calibration runs.".to_string())?;
            let path = PathBuf::from(&directory);
            if !path.is_dir() {
                return Err(format!("'{directory}' is not a directory."));
            }
            working_directory = Some(path);
            arguments.push(directory);
        }
        "client" => {}
        other => return Err(format!("Unknown server mode '{other}'.")),
    }
    arguments.push("--host".to_string());
    arguments.push(options.host.clone());
    arguments.push("--port".to_string());
    arguments.push(options.port.to_string());
    if options.mode != "client" {
        arguments.push(if options.auth { "--auth" } else { "--no-auth" }.to_string());
    }
    if options.mode == "dev" {
        if let Some(port) = options.frontend_port {
            arguments.push("--frontend-port".to_string());
            arguments.push(port.to_string());
        }
    }

    let url = format!("http://{}:{}", options.host, options.port);
    let detail = options
        .directory
        .clone()
        .unwrap_or_else(|| "Multi-server client".to_string());
    supervisor.spawn(
        &app,
        "server",
        url.clone(),
        detail,
        arguments,
        working_directory,
        Some(url),
    )
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct NotebookOptions {
    pub connection: Option<String>,
    pub ssh: Option<String>,
    pub queue: Option<String>,
    pub slurm: Option<String>,
    pub workdir: Option<String>,
    pub venv: Option<String>,
    pub marimo: Option<bool>,
    pub timeout: Option<f64>,
    pub subnet: Option<String>,
}

fn push_text(arguments: &mut Vec<String>, flag: &str, value: Option<String>) {
    if let Some(value) = value.map(|value| value.trim().to_string()) {
        if !value.is_empty() {
            arguments.push(flag.to_string());
            arguments.push(value);
        }
    }
}

#[tauri::command]
pub fn start_notebook(
    app: AppHandle,
    supervisor: State<Supervisor>,
    options: NotebookOptions,
) -> Result<ProcessInfo, String> {
    let mut arguments = vec!["notebook".to_string(), "connect".to_string()];
    let connection = options
        .connection
        .clone()
        .map(|name| name.trim().to_string())
        .filter(|name| !name.is_empty());
    if let Some(name) = connection.clone() {
        arguments.push(name);
    }
    push_text(&mut arguments, "--ssh", options.ssh.clone());
    push_text(&mut arguments, "--queue", options.queue);
    push_text(&mut arguments, "--slurm", options.slurm);
    push_text(&mut arguments, "--workdir", options.workdir);
    push_text(&mut arguments, "--venv", options.venv);
    push_text(&mut arguments, "--subnet", options.subnet);
    if let Some(marimo) = options.marimo {
        arguments.push(if marimo { "--marimo" } else { "--jupyter" }.to_string());
    }
    if let Some(timeout) = options.timeout {
        arguments.push("--timeout".to_string());
        arguments.push(format!("{timeout}"));
    }
    // The launcher opens the URL itself, once the session reports it.
    arguments.push("--no-interactive".to_string());

    let label = connection.unwrap_or_else(|| {
        if options.marimo.unwrap_or(false) {
            "Marimo".to_string()
        } else {
            "JupyterLab".to_string()
        }
    });
    let detail = options
        .ssh
        .clone()
        .map(|ssh| format!("ssh {ssh}"))
        .unwrap_or_else(|| "local session".to_string());
    supervisor.spawn(&app, "notebook", label, detail, arguments, None, None)
}

#[tauri::command]
pub fn processes(supervisor: State<Supervisor>) -> Vec<ProcessInfo> {
    supervisor.list()
}

#[tauri::command]
pub fn process_log(supervisor: State<Supervisor>, id: String) -> Vec<String> {
    supervisor.log(&id)
}

#[tauri::command]
pub fn stop_process(supervisor: State<Supervisor>, id: String) -> Result<Option<ProcessInfo>, String> {
    supervisor.stop(&id)?;
    Ok(supervisor.snapshot(&id))
}

#[tauri::command]
pub fn forget_process(supervisor: State<Supervisor>, id: String) -> Result<(), String> {
    supervisor.forget(&id)
}
