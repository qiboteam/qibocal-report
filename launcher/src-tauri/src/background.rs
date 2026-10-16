//! The launcher in the background.
//!
//! Closing the last window hides it: the launcher keeps running, its servers
//! and sessions with it, and comes back from the tray icon, from the dock on
//! macOS, or from the next window opened. Quitting is explicit — the menu,
//! `Cmd/Ctrl+Q`, the tray — and waits for what runs, as closing did before.
//! What happens meanwhile is said with a system notification, when the
//! interface asks for one.

use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{AppHandle, Manager};
use tauri_plugin_notification::NotificationExt;

use crate::process::Supervisor;

/// How many windows are on screen: a window closed while others show simply closes.
pub fn shown_windows(app: &AppHandle) -> usize {
    app.webview_windows()
        .values()
        .filter(|window| window.is_visible().unwrap_or(false))
        .count()
}

/// Bring the windows back: every hidden one shown, the first of them focused.
pub fn show_windows(app: &AppHandle) {
    let mut first = true;
    for window in app.webview_windows().values() {
        let _ = window.show();
        let _ = window.unminimize();
        if first {
            let _ = window.set_focus();
            first = false;
        }
    }
}

/// The icon in the tray — the menu bar on macOS — with the two things it
/// offers: the windows back, and quitting.
pub fn install_tray(app: &AppHandle) -> tauri::Result<()> {
    let open = MenuItem::with_id(app, "tray-open", "Open Qibocal", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "tray-quit", "Quit Qibocal", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&open, &PredefinedMenuItem::separator(app)?, &quit])?;
    let mut tray = TrayIconBuilder::with_id("main")
        .tooltip("Qibocal")
        .menu(&menu)
        // A menu bar extra opens its menu on macOS; elsewhere a click is the window.
        .show_menu_on_left_click(cfg!(target_os = "macos"))
        .on_menu_event(|app, event| match event.id().as_ref() {
            "tray-open" => show_windows(app),
            "tray-quit" => quit_after_processes(app),
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if cfg!(target_os = "macos") {
                return;
            }
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                show_windows(tray.app_handle());
            }
        });
    if let Some(icon) = app.default_window_icon() {
        tray = tray.icon(icon.clone());
    }
    tray.build(app)?;
    Ok(())
}

/// Quit, waiting for what runs: the windows come back first, so that the
/// closing dialog — whom it waits for, and the way to force it — is seen.
fn quit_after_processes(app: &AppHandle) {
    show_windows(app);
    if app.state::<Supervisor>().request_close(app) {
        app.exit(0);
    }
}

/// `Cmd/Ctrl+Q`, the Quit item: the one way out that waits for the processes.
#[tauri::command]
pub fn request_quit(app: AppHandle) {
    quit_after_processes(&app);
}

/// A system notification: for what happens while the user is not looking —
/// a server up, a session ready, something failed, new reports — decided
/// by the interface, which knows what is on screen.
#[tauri::command]
pub fn system_notify(app: AppHandle, title: String, body: String) -> Result<(), String> {
    app.notification()
        .builder()
        .title(title)
        .body(body)
        .show()
        .map_err(|error| error.to_string())
}
