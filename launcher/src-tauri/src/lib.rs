//! Qibocal: a thin desktop shell around the `qibocal` command line.
//!
//! The Rust side only does what a browser cannot: find the interpreter, read
//! and write the shared configuration files, and supervise long-running
//! processes. Everything else lives in the web interface.

mod process;
mod qibocal;
mod settings;

use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

use tauri::utils::config::WindowConfig;
use tauri::webview::{NewWindowResponse, WebviewWindowBuilder};
use tauri::{AppHandle, Manager, Url, WebviewUrl, WebviewWindow};

/// The main window's configuration: every other window is cut from it.
const MAIN_WINDOW: &str = "main";

/// How many windows were opened besides the main one: their labels count up.
static OPENED: AtomicU64 = AtomicU64::new(0);

/// Whether an address is one of this application's own pages.
///
/// The pages are served under the `tauri` scheme on macOS and Linux, under
/// `http://tauri.localhost` on Windows, and from the Vite server while
/// developing; anything else is the outside world.
fn is_own_page(url: &Url) -> bool {
    match url.scheme() {
        "tauri" => true,
        "http" | "https" => {
            url.host_str() == Some("tauri.localhost")
                || (cfg!(debug_assertions)
                    && matches!(url.host_str(), Some("localhost") | Some("127.0.0.1")))
        }
        _ => false,
    }
}

/// A window of the application on one of its pages, cut from the main
/// window's configuration, and opening further windows the same way.
fn open_window(app: &AppHandle, template: &WindowConfig, url: Url) -> tauri::Result<WebviewWindow> {
    let label = format!("window-{}", OPENED.fetch_add(1, Ordering::SeqCst) + 1);
    // Our own pages are opened as the application opens them — by their
    // path under the application's origin — and taken to the exact address,
    // hash and all, once the window exists; the Vite server's are external.
    let own = url.scheme() == "tauri" || url.host_str() == Some("tauri.localhost");
    let target = if own {
        WebviewUrl::App(PathBuf::from(url.path().trim_start_matches('/')))
    } else {
        WebviewUrl::External(url.clone())
    };
    let handle = app.clone();
    let config = template.clone();
    let mut builder = WebviewWindowBuilder::new(app, label, target)
        .title(&template.title)
        .inner_size(template.width, template.height)
        .resizable(template.resizable)
        .on_new_window(move |url, _features| new_window(&handle, &config, url));
    if let (Some(width), Some(height)) = (template.min_width, template.min_height) {
        builder = builder.min_inner_size(width, height);
    }
    if let Some(color) = template.background_color {
        builder = builder.background_color(color);
    }
    #[cfg(target_os = "macos")]
    {
        builder = builder
            .title_bar_style(template.title_bar_style)
            .hidden_title(template.hidden_title);
    }
    let window = builder.build()?;
    if own && (url.fragment().is_some() || url.query().is_some()) {
        window.navigate(url)?;
    }
    Ok(window)
}

/// What becomes of a request for a new window — `window.open`, or "Open
/// Link in New Window" in the context menu: one of our pages opens in a
/// window of ours, with the same geometry; anything else goes to the
/// browser, as the links that leave the application do.
fn new_window(app: &AppHandle, template: &WindowConfig, url: Url) -> NewWindowResponse<tauri::Wry> {
    if is_own_page(&url) {
        // Built once this callback has returned, not handed back from it: a
        // window returned here must share the caller's webview configuration
        // on macOS, and WebKit aborts the application when it does not. The
        // request itself is denied; ours opens a moment later.
        let handle = app.clone();
        let config = template.clone();
        let _ = app.run_on_main_thread(move || {
            let _ = open_window(&handle, &config, url);
        });
    } else {
        let _ = tauri_plugin_opener::open_url(url.as_str(), None::<&str>);
    }
    NewWindowResponse::Deny
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            app.manage(process::Supervisor::default());
            // The main window is built here rather than from the configuration
            // alone (`"create": false` there), so that requests for new
            // windows — ours, or the context menu's — are handled.
            let template = app
                .config()
                .app
                .windows
                .iter()
                .find(|window| window.label == MAIN_WINDOW)
                .cloned()
                .expect("the main window is configured");
            let handle = app.handle().clone();
            let config = template.clone();
            WebviewWindowBuilder::from_config(app.handle(), &template)?
                .on_new_window(move |url, _features| new_window(&handle, &config, url))
                .build()?;
            Ok(())
        })
        // Closing the last window while something runs: stop it first, then
        // go. Any other window simply closes.
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                let app = window.app_handle();
                if app.webview_windows().len() > 1 {
                    return;
                }
                if !app.state::<process::Supervisor>().request_close(app) {
                    api.prevent_close();
                }
            }
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
            process::quit,
        ])
        .build(tauri::generate_context!())
        .expect("could not start the Qibocal launcher")
        .run(|app, event| match event {
            // Quitting the application is the window closing, with the same
            // wait; `code` is set by the launcher's own exit, which is final.
            tauri::RunEvent::ExitRequested { api, code: None, .. } => {
                if !app.state::<process::Supervisor>().request_close(app) {
                    api.prevent_exit();
                }
            }
            // Never leave report servers or notebook tunnels behind.
            tauri::RunEvent::Exit => {
                app.state::<process::Supervisor>().shutdown();
            }
            _ => {}
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
