// Keep the Windows release build free of a console window behind the interface.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    qibocamp_lib::run()
}
