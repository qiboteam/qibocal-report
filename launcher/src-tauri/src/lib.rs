//! Qibocal: a thin desktop shell around the `qibocal` command line.
//!
//! The Rust side only does what a browser cannot: find the interpreter, read
//! and write the shared configuration files, and supervise long-running
//! processes. Everything else lives in the web interface.

mod process;
mod qibocal;
mod settings;

use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            app.manage(process::Supervisor::default());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            qibocal::environment,
            qibocal::set_executable,
            qibocal::install_qibocal,
            qibocal::free_port,
            qibocal::administrators,
            qibocal::reissue_invite,
            qibocal::platform_summary,
            settings::config_entries,
            settings::config_directory,
            settings::read_config_file,
            settings::write_config_file,
            settings::remove_config_entries,
            settings::list_servers,
            settings::save_servers,
            settings::list_notebooks,
            settings::save_notebook,
            settings::remove_notebook,
            settings::preferences,
            settings::save_preferences,
            process::start_server,
            process::start_notebook,
            process::processes,
            process::process_log,
            process::stop_process,
            process::forget_process,
        ])
        .build(tauri::generate_context!())
        .expect("could not start the Qibocal launcher")
        .run(|app, event| {
            // Never leave report servers or notebook tunnels behind.
            if let tauri::RunEvent::Exit = event {
                app.state::<process::Supervisor>().shutdown();
            }
        });
}

#[cfg(test)]
mod tests {
    use super::process::{announced_url, extract_url};

    #[test]
    fn reads_the_notebook_url_from_a_log_line() {
        assert_eq!(
            extract_url("http://localhost:8899/lab?token=abc"),
            Some("http://localhost:8899/lab?token=abc".to_string())
        );
        assert_eq!(
            extract_url("Open https://example.org/path, then sign in."),
            Some("https://example.org/path".to_string())
        );
        assert_eq!(extract_url("no address here"), None);
    }

    #[test]
    fn only_a_line_that_is_an_address_announces_one() {
        assert_eq!(
            announced_url("  http://localhost:8899/lab?token=abc  "),
            Some("http://localhost:8899/lab?token=abc".to_string())
        );
        assert_eq!(
            announced_url("\u{1b}[1;36mhttp://localhost:41234\u{1b}[0m"),
            Some("http://localhost:41234".to_string()),
            "colour codes around it do not count"
        );
        assert_eq!(announced_url("[I 10:00] Jupyter Server is running at http://10.0.0.5:8888/lab"), None);
        assert_eq!(announced_url("Connecting to SSH destination node."), None);
    }
}
