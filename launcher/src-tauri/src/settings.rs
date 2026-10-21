//! Read and write the configuration files shared with the `qibocal` CLI.
//!
//! The layout mirrors `qibocal_report.config.get_config_dir`, so the launcher
//! and the command line always see the same servers, notebook connections and
//! authentication database.

use std::fs;
use std::path::{Path, PathBuf};

use serde::Serialize;
use serde_json::{Map, Value};

/// Files the launcher knows about, with the description shown in the interface.
const KNOWN_FILES: [(&str, &str); 6] = [
    ("servers.json", "Registered report servers"),
    ("notebooks.json", "Saved notebook connections"),
    ("remotes.json", "Remote execution connections, shared with qibocal-widgets"),
    ("agent-hosts.json", "Agent configurations kept here for other machines"),
    ("auth.json", "Users, invitations and signing keys"),
    ("launcher.json", "Launcher preferences"),
];

/// The format of each file this version of the launcher reads and writes.
///
/// Every file is an object carrying a `version`; `servers.json` keeps its
/// entries under `servers`, `notebooks.json` and `remotes.json` under
/// `connections`, `agent-hosts.json` under `hosts`, the other two next to the
/// version. A file without a version, or with another one, is not ours: it is
/// ignored, never overwritten, and listed in Configuration as it is, for a
/// migration by hand — there is no automatic one.
pub const CONFIG_VERSION: u64 = 1;

/// What a file on disk is, as far as the version goes.
#[derive(Clone, Copy, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Compatibility {
    /// The version the file declares; none for a file without one, or absent.
    pub version: Option<u64>,
    pub expected: u64,
    /// A file that is absent, empty or not JSON is compatible: nothing to keep.
    pub compatible: bool,
}

/// The version a document declares, if any.
fn declared_version(value: &Value) -> Option<u64> {
    value.as_object()?.get("version")?.as_u64()
}

fn compatibility(value: Option<&Value>) -> Compatibility {
    let version = value.and_then(declared_version);
    Compatibility {
        version,
        expected: CONFIG_VERSION,
        compatible: value.is_none() || version == Some(CONFIG_VERSION),
    }
}

/// The error a write into an incompatible file answers with.
fn incompatible(name: &str, found: Option<u64>) -> String {
    let declared = match found {
        Some(found) => format!("format {found}"),
        None => "no format version".to_string(),
    };
    format!(
        "{name} was written by another version of Qibocal ({declared}; this one reads {CONFIG_VERSION}). \
         It is left as it is until migrated by hand, in Configuration."
    )
}

/// Read a known file, answering nothing for one of another version.
///
/// `Err` is a file that cannot be read or parsed; an incompatible one is
/// not an error, it is simply not there for this version of the launcher.
fn read_compatible(path: &Path) -> Result<Option<Value>, String> {
    let value = read_json(path)?;
    Ok(match compatibility(value.as_ref()).compatible {
        true => value,
        false => None,
    })
}

/// Refuse to replace a file of another version, or of none: that is a
/// migration's job.
fn guard_write(name: &str, path: &Path) -> Result<(), String> {
    let found = read_json(path).ok().flatten();
    let state = compatibility(found.as_ref());
    match state.compatible {
        true => Ok(()),
        false => Err(incompatible(name, state.version)),
    }
}

/// The entries of a compatible document: under `key` in its object.
fn entries_of(value: Value, key: &str) -> Value {
    match value {
        Value::Object(mut object) => object.remove(key).unwrap_or(Value::Null),
        _ => Value::Null,
    }
}

fn versioned(key: &str, entries: Value) -> Value {
    let mut object = Map::new();
    object.insert("version".to_string(), Value::from(CONFIG_VERSION));
    object.insert(key.to_string(), entries);
    Value::Object(object)
}

pub fn config_dir() -> PathBuf {
    if let Some(custom) = non_empty_env("QIBOCAL_REPORT_CONFIG_DIR") {
        return PathBuf::from(custom);
    }
    let root = non_empty_env("XDG_CONFIG_HOME")
        .map(PathBuf::from)
        .or_else(|| dirs::home_dir().map(|home| home.join(".config")))
        .unwrap_or_else(|| PathBuf::from(".config"));
    root.join("qibocal")
}

fn non_empty_env(name: &str) -> Option<String> {
    std::env::var(name).ok().filter(|value| !value.is_empty())
}

fn config_file(name: &str) -> Result<PathBuf, String> {
    if !KNOWN_FILES.iter().any(|(known, _)| *known == name) {
        return Err(format!("Unknown configuration file '{name}'."));
    }
    Ok(config_dir().join(name))
}

pub fn read_json(path: &Path) -> Result<Option<Value>, String> {
    match fs::read_to_string(path) {
        Ok(contents) if contents.trim().is_empty() => Ok(None),
        Ok(contents) => serde_json::from_str(&contents)
            .map(Some)
            .map_err(|error| format!("Could not parse '{}': {error}", path.display())),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(error) => Err(format!("Could not read '{}': {error}", path.display())),
    }
}

/// Replace the file in one step, so a crash never leaves a truncated config.
pub fn write_json(path: &Path, value: &Value) -> Result<(), String> {
    replace_json(path, value, false)
}

/// The same, for the owner's eyes only: `auth.json` holds the signing keys.
fn write_private_json(path: &Path, value: &Value) -> Result<(), String> {
    replace_json(path, value, true)
}

fn replace_json(path: &Path, value: &Value, private: bool) -> Result<(), String> {
    let parent = path
        .parent()
        .ok_or_else(|| format!("Invalid configuration path '{}'.", path.display()))?;
    let created = match private {
        true => create_private_dir(parent),
        false => fs::create_dir_all(parent),
    };
    created.map_err(|error| format!("Could not create '{}': {error}", parent.display()))?;
    let serialized = serde_json::to_string_pretty(value)
        .map_err(|error| format!("Could not serialize configuration: {error}"))?;
    let temporary = parent.join(format!(
        ".{}.{}.tmp",
        path.file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("config"),
        std::process::id()
    ));
    let contents = format!("{serialized}\n");
    let written = match private {
        true => write_private(&temporary, &contents),
        false => fs::write(&temporary, &contents),
    };
    written.map_err(|error| format!("Could not write '{}': {error}", temporary.display()))?;
    fs::rename(&temporary, path).map_err(|error| {
        let _ = fs::remove_file(&temporary);
        format!("Could not update '{}': {error}", path.display())
    })
}

/// A directory only its owner can enter, when it has to be created.
#[cfg(unix)]
fn create_private_dir(path: &Path) -> std::io::Result<()> {
    use std::os::unix::fs::DirBuilderExt;
    fs::DirBuilder::new().recursive(true).mode(0o700).create(path)
}

#[cfg(not(unix))]
fn create_private_dir(path: &Path) -> std::io::Result<()> {
    fs::create_dir_all(path)
}

/// A file only its owner can read, from its first byte: the temporary
/// carries the mode into the rename.
#[cfg(unix)]
fn write_private(path: &Path, contents: &str) -> std::io::Result<()> {
    use std::io::Write;
    use std::os::unix::fs::{OpenOptionsExt, PermissionsExt};
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .mode(0o600)
        .open(path)?;
    // A temporary left over by a crash keeps its own mode: set it again.
    file.set_permissions(fs::Permissions::from_mode(0o600))?;
    file.write_all(contents.as_bytes())
}

#[cfg(not(unix))]
fn write_private(path: &Path, contents: &str) -> std::io::Result<()> {
    fs::write(path, contents)
}

#[derive(Serialize)]
pub struct ConfigEntry {
    pub name: String,
    pub path: String,
    pub description: String,
    pub exists: bool,
    pub size: u64,
    /// The version the file declares, and whether this launcher reads it.
    pub version: Option<u64>,
    pub expected: u64,
    pub compatible: bool,
}

#[tauri::command]
pub fn config_entries() -> Vec<ConfigEntry> {
    let directory = config_dir();
    KNOWN_FILES
        .iter()
        .map(|(name, description)| {
            let path = directory.join(name);
            let metadata = fs::metadata(&path).ok();
            let state = compatibility(read_json(&path).ok().flatten().as_ref());
            ConfigEntry {
                name: (*name).to_string(),
                path: path.display().to_string(),
                description: (*description).to_string(),
                exists: metadata.is_some(),
                size: metadata.map(|data| data.len()).unwrap_or(0),
                version: state.version,
                expected: state.expected,
                compatible: state.compatible,
            }
        })
        .collect()
}

#[tauri::command]
pub fn config_directory() -> String {
    config_dir().display().to_string()
}

/// One configuration file, as the editor sees it.
#[derive(Serialize)]
pub struct ConfigDocument {
    pub name: String,
    pub path: String,
    pub exists: bool,
    /// The file verbatim, pretty-printed when it holds JSON, empty when absent.
    pub text: String,
}

fn document(name: &str, path: &Path) -> Result<ConfigDocument, String> {
    // A file that is not valid JSON comes back verbatim rather than as an
    // error: editing it as text is the only way to repair it from here.
    let text = match fs::read_to_string(path) {
        Ok(contents) => match serde_json::from_str::<Value>(&contents) {
            Ok(value) => serde_json::to_string_pretty(&value)
                .map_err(|error| format!("Could not format '{}': {error}", path.display()))?,
            Err(_) => contents,
        },
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => String::new(),
        Err(error) => {
            return Err(format!("Could not read '{}': {error}", path.display()));
        }
    };
    Ok(ConfigDocument {
        name: name.to_string(),
        path: path.display().to_string(),
        exists: path.exists(),
        text,
    })
}

#[tauri::command]
pub fn read_config_file(name: String) -> Result<ConfigDocument, String> {
    let path = config_file(&name)?;
    document(&name, &path)
}

/// Replace a configuration file, refusing anything that is not valid JSON.
///
/// The parser message is passed on as it is: it names the line and the column,
/// which is what an editor needs to point at the mistake.
#[tauri::command]
pub fn write_config_file(name: String, text: String) -> Result<ConfigDocument, String> {
    let path = config_file(&name)?;
    let value: Value = serde_json::from_str(&text)
        .map_err(|error| format!("'{name}' must contain valid JSON: {error}"))?;
    match name.as_str() {
        "auth.json" => write_private_json(&path, &value)?,
        _ => write_json(&path, &value)?,
    }
    document(&name, &path)
}

#[tauri::command]
pub fn remove_config_entries(names: Vec<String>) -> Result<Vec<String>, String> {
    let mut removed = Vec::new();
    for name in names {
        let path = config_file(&name)?;
        match fs::remove_file(&path) {
            Ok(()) => removed.push(path.display().to_string()),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
            Err(error) => return Err(format!("Could not remove '{}': {error}", path.display())),
        }
    }
    Ok(removed)
}

#[tauri::command]
pub fn list_servers() -> Result<Vec<Value>, String> {
    let path = config_file("servers.json")?;
    Ok(match read_compatible(&path)?.map(|value| entries_of(value, "servers")) {
        Some(Value::Array(servers)) => servers,
        _ => Vec::new(),
    })
}

#[tauri::command]
pub fn save_servers(servers: Vec<Value>) -> Result<Vec<Value>, String> {
    let path = config_file("servers.json")?;
    guard_write("servers.json", &path)?;
    write_json(&path, &versioned("servers", Value::Array(servers.clone())))?;
    Ok(servers)
}

/// The named connections of a file that keeps them under `connections`:
/// `notebooks.json`, and `remotes.json`, which qibocal-widgets reads.
fn list_connections(file: &str) -> Result<Map<String, Value>, String> {
    let path = config_file(file)?;
    match read_compatible(&path)?.map(|value| entries_of(value, "connections")) {
        Some(Value::Object(connections)) => Ok(connections),
        Some(_) => Err(format!(
            "'{}' must contain a connection-name object.",
            path.display()
        )),
        None => Ok(Map::new()),
    }
}

fn write_connections(file: &str, connections: &Map<String, Value>) -> Result<(), String> {
    let path = config_file(file)?;
    guard_write(file, &path)?;
    write_json(&path, &versioned("connections", Value::Object(connections.clone())))
}

fn save_connection(file: &str, name: String, options: Value) -> Result<Map<String, Value>, String> {
    if name.trim().is_empty() {
        return Err("Connection name must not be empty.".to_string());
    }
    if !options.is_object() {
        return Err("Connection options must be an object.".to_string());
    }
    let mut connections = list_connections(file)?;
    connections.insert(name, options);
    write_connections(file, &connections)?;
    Ok(connections)
}

fn remove_connection(file: &str, name: String) -> Result<Map<String, Value>, String> {
    let mut connections = list_connections(file)?;
    if connections.remove(&name).is_none() {
        return Err(format!("Connection '{name}' is not registered in {file}."));
    }
    write_connections(file, &connections)?;
    Ok(connections)
}

#[tauri::command]
pub fn list_notebooks() -> Result<Map<String, Value>, String> {
    list_connections("notebooks.json")
}

#[tauri::command]
pub fn save_notebook(name: String, options: Value) -> Result<Map<String, Value>, String> {
    save_connection("notebooks.json", name, options)
}

#[tauri::command]
pub fn remove_notebook(name: String) -> Result<Map<String, Value>, String> {
    remove_connection("notebooks.json", name)
}

/// qibocal-agent's own `agents.json`, found as it finds it. It is its own —
/// strictly validated, unknown keys an error — so it is read and written as
/// it is, without the version the launcher's own files carry, and listed
/// apart from them.
pub fn agent_config_path() -> PathBuf {
    if let Some(custom) = non_empty_env("QIBOCAL_AGENTS_CONFIG_DIR") {
        return PathBuf::from(custom).join("agents.json");
    }
    let root = non_empty_env("XDG_CONFIG_HOME")
        .map(PathBuf::from)
        .or_else(|| dirs::home_dir().map(|home| home.join(".config")))
        .unwrap_or_else(|| PathBuf::from(".config"));
    root.join("qibocal").join("agents.json")
}

#[derive(Serialize)]
pub struct AgentDocument {
    pub path: String,
    pub document: Value,
}

#[tauri::command]
pub fn read_agents() -> Result<AgentDocument, String> {
    let path = agent_config_path();
    let document = match read_json(&path)? {
        Some(Value::Object(object)) => Value::Object(object),
        Some(_) => return Err(format!("'{}' does not hold a JSON object.", path.display())),
        None => Value::Object(Map::new()),
    };
    Ok(AgentDocument { path: path.display().to_string(), document })
}

#[tauri::command]
pub fn write_agents(document: Value) -> Result<AgentDocument, String> {
    if !document.is_object() {
        return Err("The agent configuration must be a JSON object.".to_string());
    }
    let path = agent_config_path();
    write_json(&path, &document)?;
    Ok(AgentDocument { path: path.display().to_string(), document })
}

/// The agent configurations kept here for other machines, by SSH destination.
#[tauri::command]
pub fn list_agent_hosts() -> Result<Map<String, Value>, String> {
    let path = config_file("agent-hosts.json")?;
    match read_compatible(&path)?.map(|value| entries_of(value, "hosts")) {
        Some(Value::Object(hosts)) => Ok(hosts),
        Some(_) => Err(format!("'{}' must contain a host-name object.", path.display())),
        None => Ok(Map::new()),
    }
}

#[tauri::command]
pub fn save_agent_hosts(hosts: Map<String, Value>) -> Result<Map<String, Value>, String> {
    let path = config_file("agent-hosts.json")?;
    guard_write("agent-hosts.json", &path)?;
    write_json(&path, &versioned("hosts", Value::Object(hosts.clone())))?;
    Ok(hosts)
}

/// The remote execution connections of qibocal-widgets' `Remote` plugin.
#[tauri::command]
pub fn list_remotes() -> Result<Map<String, Value>, String> {
    list_connections("remotes.json")
}

#[tauri::command]
pub fn save_remote(name: String, options: Value) -> Result<Map<String, Value>, String> {
    save_connection("remotes.json", name, options)
}

#[tauri::command]
pub fn remove_remote(name: String) -> Result<Map<String, Value>, String> {
    remove_connection("remotes.json", name)
}

/// The preferences, the version they were written under left out.
pub fn launcher_preferences() -> Map<String, Value> {
    match config_file("launcher.json").and_then(|path| read_compatible(&path)) {
        Ok(Some(Value::Object(mut preferences))) => {
            preferences.remove("version");
            preferences
        }
        _ => Map::new(),
    }
}

pub fn store_launcher_preferences(mut preferences: Map<String, Value>) -> Result<(), String> {
    let path = config_file("launcher.json")?;
    guard_write("launcher.json", &path)?;
    preferences.insert("version".to_string(), Value::from(CONFIG_VERSION));
    write_json(&path, &Value::Object(preferences))
}

#[tauri::command]
pub fn preferences() -> Map<String, Value> {
    launcher_preferences()
}

#[tauri::command]
pub fn save_preferences(settings: Map<String, Value>) -> Result<Map<String, Value>, String> {
    store_launcher_preferences(settings.clone())?;
    Ok(settings)
}
