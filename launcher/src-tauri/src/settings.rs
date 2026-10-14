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
const KNOWN_FILES: [(&str, &str); 4] = [
    ("servers.json", "Registered report servers"),
    ("notebooks.json", "Saved notebook connections"),
    ("auth.json", "Users, invitations and signing keys"),
    ("launcher.json", "Launcher preferences"),
];

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
    let parent = path
        .parent()
        .ok_or_else(|| format!("Invalid configuration path '{}'.", path.display()))?;
    fs::create_dir_all(parent)
        .map_err(|error| format!("Could not create '{}': {error}", parent.display()))?;
    let serialized = serde_json::to_string_pretty(value)
        .map_err(|error| format!("Could not serialize configuration: {error}"))?;
    let temporary = parent.join(format!(
        ".{}.{}.tmp",
        path.file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("config"),
        std::process::id()
    ));
    fs::write(&temporary, format!("{serialized}\n"))
        .map_err(|error| format!("Could not write '{}': {error}", temporary.display()))?;
    fs::rename(&temporary, path).map_err(|error| {
        let _ = fs::remove_file(&temporary);
        format!("Could not update '{}': {error}", path.display())
    })
}

#[derive(Serialize)]
pub struct ConfigEntry {
    pub name: String,
    pub path: String,
    pub description: String,
    pub exists: bool,
    pub size: u64,
}

#[tauri::command]
pub fn config_entries() -> Vec<ConfigEntry> {
    let directory = config_dir();
    KNOWN_FILES
        .iter()
        .map(|(name, description)| {
            let path = directory.join(name);
            let metadata = fs::metadata(&path).ok();
            ConfigEntry {
                name: (*name).to_string(),
                path: path.display().to_string(),
                description: (*description).to_string(),
                exists: metadata.is_some(),
                size: metadata.map(|data| data.len()).unwrap_or(0),
            }
        })
        .collect()
}

#[tauri::command]
pub fn config_directory() -> String {
    config_dir().display().to_string()
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
    Ok(match read_json(&path)? {
        Some(Value::Array(servers)) => servers,
        // `qibocal` historically also accepted `{"servers": [...]}`.
        Some(Value::Object(mut wrapper)) => match wrapper.remove("servers") {
            Some(Value::Array(servers)) => servers,
            _ => Vec::new(),
        },
        _ => Vec::new(),
    })
}

#[tauri::command]
pub fn save_servers(servers: Vec<Value>) -> Result<Vec<Value>, String> {
    let path = config_file("servers.json")?;
    write_json(&path, &Value::Array(servers.clone()))?;
    Ok(servers)
}

#[tauri::command]
pub fn list_notebooks() -> Result<Map<String, Value>, String> {
    let path = config_file("notebooks.json")?;
    match read_json(&path)? {
        Some(Value::Object(connections)) => Ok(connections),
        Some(_) => Err(format!(
            "'{}' must contain a connection-name object.",
            path.display()
        )),
        None => Ok(Map::new()),
    }
}

#[tauri::command]
pub fn save_notebook(name: String, options: Value) -> Result<Map<String, Value>, String> {
    if name.trim().is_empty() {
        return Err("Connection name must not be empty.".to_string());
    }
    if !options.is_object() {
        return Err("Notebook options must be an object.".to_string());
    }
    let mut connections = list_notebooks()?;
    connections.insert(name, options);
    write_json(
        &config_file("notebooks.json")?,
        &Value::Object(connections.clone()),
    )?;
    Ok(connections)
}

#[tauri::command]
pub fn remove_notebook(name: String) -> Result<Map<String, Value>, String> {
    let mut connections = list_notebooks()?;
    if connections.remove(&name).is_none() {
        return Err(format!("Notebook connection '{name}' is not registered."));
    }
    write_json(
        &config_file("notebooks.json")?,
        &Value::Object(connections.clone()),
    )?;
    Ok(connections)
}

pub fn launcher_preferences() -> Map<String, Value> {
    match config_file("launcher.json").and_then(|path| read_json(&path)) {
        Ok(Some(Value::Object(preferences))) => preferences,
        _ => Map::new(),
    }
}

pub fn store_launcher_preferences(preferences: Map<String, Value>) -> Result<(), String> {
    write_json(
        &config_file("launcher.json")?,
        &Value::Object(preferences),
    )
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
