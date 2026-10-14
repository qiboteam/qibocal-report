//! Locate the `qibocal` command line and run its short-lived subcommands.
//!
//! Desktop applications started from a launcher do not inherit the shell
//! `PATH`, so a plain lookup is not enough: the preferred interpreter can be
//! stored in `launcher.json`, and a list of usual virtual environment layouts
//! is probed before giving up.

use std::net::TcpListener;
use std::path::{Path, PathBuf};
use std::process::Command;

use serde::Serialize;
use serde_json::{json, Value};

use crate::settings;

#[derive(Serialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct Environment {
    /// Absolute path of the resolved interpreter, when one was found.
    pub executable: Option<String>,
    /// How it was found: `preference`, `environment`, `path` or `well-known`.
    pub source: Option<String>,
    pub version: Option<String>,
    pub config_directory: String,
    /// Locations that were probed, to make a missing installation diagnosable.
    pub searched: Vec<String>,
}

fn program_names() -> Vec<&'static str> {
    if cfg!(windows) {
        vec!["qibocal.exe", "qibocal.cmd", "qibocal.bat"]
    } else {
        vec!["qibocal"]
    }
}

fn is_executable(path: &Path) -> bool {
    path.is_file()
}

/// Accept either the interpreter itself or the virtual environment holding it.
pub fn normalize_candidate(path: &Path) -> Option<PathBuf> {
    if is_executable(path) {
        return Some(path.to_path_buf());
    }
    if path.is_dir() {
        for directory in [path.join("bin"), path.join("Scripts"), path.to_path_buf()] {
            for name in program_names() {
                let candidate = directory.join(name);
                if is_executable(&candidate) {
                    return Some(candidate);
                }
            }
        }
    }
    None
}

fn well_known_candidates() -> Vec<PathBuf> {
    let mut candidates = Vec::new();
    if let Some(home) = dirs::home_dir() {
        for relative in [
            ".local/bin",
            ".local/pipx/venvs/qibocal-report/bin",
            ".local/pipx/venvs/qibocal/bin",
            ".venv/bin",
            "venv/bin",
            "qibocal/.venv/bin",
            "AppData/Roaming/Python/Scripts",
            ".local/pipx/venvs/qibocal-report/Scripts",
        ] {
            candidates.push(home.join(relative));
        }
    }
    for absolute in ["/usr/local/bin", "/opt/homebrew/bin", "/usr/bin"] {
        candidates.push(PathBuf::from(absolute));
    }
    if let Ok(current) = std::env::current_dir() {
        candidates.push(current.join(".venv/bin"));
        candidates.push(current.join(".venv/Scripts"));
    }
    candidates
}

/// Resolve the interpreter, reporting every location that was inspected.
pub fn resolve() -> (Option<(PathBuf, String)>, Vec<String>) {
    let mut searched = Vec::new();

    let preference = settings::launcher_preferences()
        .get("executable")
        .and_then(Value::as_str)
        .map(PathBuf::from);
    if let Some(path) = preference {
        searched.push(path.display().to_string());
        if let Some(resolved) = normalize_candidate(&path) {
            return (Some((resolved, "preference".to_string())), searched);
        }
    }

    if let Some(value) = std::env::var("QIBOCAL_EXECUTABLE")
        .ok()
        .filter(|value| !value.is_empty())
    {
        let path = PathBuf::from(value);
        searched.push(path.display().to_string());
        if let Some(resolved) = normalize_candidate(&path) {
            return (Some((resolved, "environment".to_string())), searched);
        }
    }

    for directory in std::env::split_paths(&std::env::var_os("PATH").unwrap_or_default()) {
        for name in program_names() {
            let candidate = directory.join(name);
            if is_executable(&candidate) {
                return (Some((candidate, "path".to_string())), searched);
            }
        }
    }

    for directory in well_known_candidates() {
        for name in program_names() {
            let candidate = directory.join(name);
            searched.push(candidate.display().to_string());
            if is_executable(&candidate) {
                return (Some((candidate, "well-known".to_string())), searched);
            }
        }
    }

    (None, searched)
}

pub fn executable() -> Result<PathBuf, String> {
    resolve()
        .0
        .map(|(path, _)| path)
        .ok_or_else(|| {
            "No 'qibocal' command line was found. Install qibocal-report, or select the \
             interpreter in the Configuration section."
                .to_string()
        })
}

/// Build a command that can find its own siblings (python, uvicorn, pnpm).
pub fn command(program: &Path) -> Command {
    let mut command = Command::new(program);
    if let Some(directory) = program.parent() {
        let mut entries = vec![directory.to_path_buf()];
        entries.extend(std::env::split_paths(
            &std::env::var_os("PATH").unwrap_or_default(),
        ));
        if let Ok(path) = std::env::join_paths(entries) {
            command.env("PATH", path);
        }
    }
    command.env("PYTHONUNBUFFERED", "1");
    command.env("PYTHONIOENCODING", "utf-8");
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        // CREATE_NO_WINDOW: never flash a console behind the interface.
        command.creation_flags(0x0800_0000);
    }
    command
}

/// Run a short-lived subcommand and return its standard output.
pub fn run(arguments: &[String]) -> Result<String, String> {
    let program = executable()?;
    let output = command(&program)
        .args(arguments)
        .output()
        .map_err(|error| format!("Could not run '{}': {error}", program.display()))?;
    if output.status.success() {
        return Ok(String::from_utf8_lossy(&output.stdout).into_owned());
    }
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let detail = if stderr.is_empty() { stdout } else { stderr };
    Err(if detail.is_empty() {
        format!("qibocal {} failed.", arguments.join(" "))
    } else {
        detail
    })
}

#[tauri::command]
pub fn environment() -> Environment {
    let (resolved, searched) = resolve();
    let (executable, source) = match resolved {
        Some((path, source)) => (Some(path), Some(source)),
        None => (None, None),
    };
    let version = executable.as_ref().and_then(|path| {
        command(path)
            .arg("--version")
            .output()
            .ok()
            .filter(|output| output.status.success())
            .map(|output| String::from_utf8_lossy(&output.stdout).trim().to_string())
            .filter(|version| !version.is_empty())
    });
    Environment {
        executable: executable.map(|path| path.display().to_string()),
        source,
        version,
        config_directory: settings::config_dir().display().to_string(),
        searched,
    }
}

#[tauri::command]
pub fn set_executable(path: Option<String>) -> Result<Environment, String> {
    let mut preferences = settings::launcher_preferences();
    match path.map(PathBuf::from) {
        Some(requested) => {
            let resolved = normalize_candidate(&requested).ok_or_else(|| {
                format!(
                    "No 'qibocal' command line found at '{}'.",
                    requested.display()
                )
            })?;
            preferences.insert(
                "executable".to_string(),
                Value::String(resolved.display().to_string()),
            );
        }
        None => {
            preferences.remove("executable");
        }
    }
    settings::store_launcher_preferences(preferences)?;
    Ok(environment())
}

/// Pick a port the operating system is willing to hand out right now.
#[tauri::command]
pub fn free_port() -> Result<u16, String> {
    TcpListener::bind("127.0.0.1:0")
        .and_then(|listener| listener.local_addr())
        .map(|address| address.port())
        .map_err(|error| format!("Could not reserve a local port: {error}"))
}

#[tauri::command]
pub fn administrators() -> Result<Value, String> {
    let output = run(&[
        "report".to_string(),
        "admin".to_string(),
        "list".to_string(),
        "--all".to_string(),
        "--json".to_string(),
    ])?;
    serde_json::from_str(&output)
        .map_err(|error| format!("Could not read the administrator list: {error}"))
}

#[derive(serde::Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct InviteRequest {
    pub username: Option<String>,
    pub server_url: String,
    pub expires_in_hours: i64,
}

/// Re-issue an administrator invitation for a locally managed server.
#[tauri::command]
pub fn reissue_invite(request: InviteRequest) -> Result<Value, String> {
    let mut arguments = vec![
        "report".to_string(),
        "admin".to_string(),
        "invite".to_string(),
    ];
    if let Some(username) = request
        .username
        .map(|name| name.trim().to_string())
        .filter(|name| !name.is_empty())
    {
        arguments.push(username);
    }
    arguments.push("--server-url".to_string());
    arguments.push(request.server_url);
    arguments.push("--expires-in-hours".to_string());
    arguments.push(request.expires_in_hours.to_string());
    arguments.push("--no-interactive".to_string());
    arguments.push("--json".to_string());

    let output = run(&arguments)?;
    let start = output
        .find('{')
        .ok_or_else(|| format!("Unexpected invitation output: {}", output.trim()))?;
    serde_json::from_str(&output[start..])
        .map_err(|error| format!("Could not read the generated invitation: {error}"))
}

/// Describe the launcher host, used by the interface for platform hints.
#[tauri::command]
pub fn platform_summary() -> Value {
    json!({
        "os": std::env::consts::OS,
        "arch": std::env::consts::ARCH,
        "home": dirs::home_dir().map(|path| path.display().to_string()),
    })
}
