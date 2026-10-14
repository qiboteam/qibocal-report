use std::process::Command;

/// The commit this launcher is built from, so that the `qibocal-report` it
/// installs is the one whose command line it knows how to drive.
///
/// The build machine says so through `QIBOCAL_BUILD_COMMIT`; a local build
/// asks git. Without either, the launcher falls back to the main branch.
fn build_commit() -> Option<String> {
    println!("cargo:rerun-if-env-changed=QIBOCAL_BUILD_COMMIT");
    if let Some(commit) = std::env::var("QIBOCAL_BUILD_COMMIT")
        .ok()
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
    {
        return Some(commit);
    }
    let output = Command::new("git").args(["rev-parse", "HEAD"]).output().ok()?;
    if !output.status.success() {
        return None;
    }
    let commit = String::from_utf8_lossy(&output.stdout).trim().to_string();
    (!commit.is_empty()).then_some(commit)
}

fn main() {
    if let Some(commit) = build_commit() {
        println!("cargo:rustc-env=QIBOCAL_BUILD_COMMIT={commit}");
    }
    tauri_build::build()
}
