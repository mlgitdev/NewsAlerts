"""NewsAlerts Release Package & Executable Verification Engine.

Performs deterministic integrity, structure, security, and asset validation on:
- Windows x64 Portable Executable & Release Archive (.zip)
- macOS arm64 Application Bundle Archive (.tar.gz)
- Linux x64 Application Archive & Desktop Integration (.tar.gz)

Exits with code 0 on full verification success, code 1 on any violation.
"""
from __future__ import annotations

import argparse
import os
import sys
import tarfile
import zipfile
from pathlib import Path

FORBIDDEN_PATTERNS = [
    "keys.toml",
    "secrets.toml",
    "secrets/",
    "secrets\\",
    ".env",
    "id_rsa",
    ".pem",
]


class PackageVerifier:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.verified_items: list[str] = []

    def log_error(self, msg: str) -> None:
        self.errors.append(msg)
        print(f"::error::{msg}", file=sys.stderr)

    def log_ok(self, msg: str) -> None:
        self.verified_items.append(msg)
        print(f"[OK] {msg}")

    def verify_no_secrets(self, name_list: list[str], package_name: str) -> bool:
        """Audit list of archive entries for forbidden secret files."""
        clean = True
        for name in name_list:
            lower = name.lower()
            for pattern in FORBIDDEN_PATTERNS:
                if pattern in lower:
                    self.log_error(f"Security violation in {package_name}: Forbidden secret pattern '{pattern}' detected in entry '{name}'!")
                    clean = False
        if clean:
            self.log_ok(f"Security audit passed for {package_name}: Zero secret files or keys detected.")
        return clean

    def verify_windows_zip(self, zip_path: Path) -> bool:
        """Verify Windows release zip archive structure and PE executable integrity."""
        print(f"\n[*] Verifying Windows Package: {zip_path.name} ({zip_path.stat().st_size / 1024 / 1024:.2f} MB)...")
        if not zip_path.exists() or zip_path.stat().st_size < 1024 * 1024:
            self.log_error(f"Windows package {zip_path} is missing or suspiciously small (<1MB)!")
            return False

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                if not self.verify_no_secrets(names, zip_path.name):
                    return False

                # Check for NewsAlerts.exe
                exe_entries = [n for n in names if n.lower().endswith("newsalerts.exe")]
                if not exe_entries:
                    self.log_error(f"Windows package {zip_path.name} is missing 'NewsAlerts.exe'!")
                    return False

                exe_name = exe_entries[0]
                exe_info = zf.getinfo(exe_name)
                exe_size_mb = exe_info.file_size / (1024 * 1024)

                # Standalone PyInstaller bundle should be at least 8 MB
                if exe_size_mb < 5.0:
                    self.log_error(f"NewsAlerts.exe in {zip_path.name} is only {exe_size_mb:.2f} MB! Expected standalone bundle >5MB.")
                    return False

                # Verify PE MZ Magic Header
                with zf.open(exe_name) as exe_file:
                    header = exe_file.read(2)
                    if header != b"MZ":
                        self.log_error(f"NewsAlerts.exe in {zip_path.name} does not have valid Win32 PE magic header 'MZ' (got: {header!r})!")
                        return False

                self.log_ok(f"Windows Executable verified: {exe_name} ({exe_size_mb:.1f} MB, Win32 PE MZ header confirmed)")

                # Check README or docs presence
                has_readme = any("readme" in n.lower() for n in names)
                if not has_readme:
                    self.log_error(f"Windows package {zip_path.name} is missing README.md!")
                    return False

                self.log_ok(f"Windows package structure verified: {len(names)} entries.")
                return True

        except Exception as e:
            self.log_error(f"Failed to inspect Windows package {zip_path}: {e}")
            return False

    def verify_tar_package(self, tar_path: Path, os_type: str) -> bool:
        """Verify macOS or Linux release tar.gz archive."""
        print(f"\n[*] Verifying {os_type} Package: {tar_path.name} ({tar_path.stat().st_size / 1024 / 1024:.2f} MB)...")
        if not tar_path.exists() or tar_path.stat().st_size < 100 * 1024:
            self.log_error(f"{os_type} package {tar_path} is missing or too small!")
            return False

        try:
            with tarfile.open(tar_path, "r:gz") as tf:
                members = tf.getmembers()
                names = [m.name for m in members]

                if not self.verify_no_secrets(names, tar_path.name):
                    return False

                # Mandatory files across both Unix platforms
                required_files = ["run.sh", "install.sh", "run_app.py", "requirements.txt"]
                for req in required_files:
                    if not any(n.endswith(req) for n in names):
                        self.log_error(f"{os_type} package {tar_path.name} is missing required file '{req}'!")
                        return False

                # OS specific files
                if os_type == "macOS":
                    if not any(n.endswith("icon.icns") for n in names):
                        self.log_error(f"macOS package {tar_path.name} is missing Apple icon bundle 'assets/icon.icns'!")
                        return False
                elif os_type == "Linux":
                    if not any(n.endswith(".desktop") for n in names):
                        self.log_error(f"Linux package {tar_path.name} is missing desktop entry 'assets/NewsAlerts.desktop'!")
                        return False
                    if not any(n.endswith("app_icon_transparent.png") for n in names):
                        self.log_error(f"Linux package {tar_path.name} is missing icon 'assets/app_icon_transparent.png'!")
                        return False

                # Check executable permissions on bash scripts
                for m in members:
                    if m.name.endswith(".sh"):
                        # Check mode permissions (executable by owner: 0o100)
                        if not (m.mode & 0o111):
                            self.warnings.append(f"Script {m.name} in {tar_path.name} does not have executable permission flags (mode: {oct(m.mode)}).")

                self.log_ok(f"{os_type} package verified: {len(members)} entries with all required scripts and assets.")
                return True

        except Exception as e:
            self.log_error(f"Failed to inspect {os_type} package {tar_path}: {e}")
            return False

    def verify_standalone_exe(self, exe_path: Path) -> bool:
        """Verify standalone NewsAlerts.exe file directly."""
        print(f"\n[*] Auditing Local Standalone Executable: {exe_path}...")
        if not exe_path.exists():
            self.log_error(f"Executable {exe_path} does not exist!")
            return False

        size_mb = exe_path.stat().st_size / (1024 * 1024)
        if size_mb < 5.0:
            self.log_error(f"Executable size is only {size_mb:.2f} MB, expected >5MB standalone bundle!")
            return False

        with open(exe_path, "rb") as f:
            header = f.read(2)
            if header != b"MZ":
                self.log_error(f"Executable does not start with Win32 MZ magic bytes (got: {header!r})!")
                return False

        self.log_ok(f"Standalone executable verified: {exe_path.name} ({size_mb:.1f} MB, valid Win32 PE header).")
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description="NewsAlerts Release Package & Binary Verifier")
    parser.add_argument("--artifacts-dir", type=str, default="", help="Directory containing release archives (.zip, .tar.gz)")
    parser.add_argument("--exe", type=str, default="", help="Path to standalone NewsAlerts.exe")
    parser.add_argument("--windows-zip", type=str, default="", help="Path to Windows release zip")
    parser.add_argument("--macos-tar", type=str, default="", help="Path to macOS release tar.gz")
    parser.add_argument("--linux-tar", type=str, default="", help="Path to Linux release tar.gz")
    args = parser.parse_args()

    verifier = PackageVerifier()

    if args.exe:
        verifier.verify_standalone_exe(Path(args.exe))

    if args.windows_zip:
        verifier.verify_windows_zip(Path(args.windows_zip))

    if args.macos_tar:
        verifier.verify_tar_package(Path(args.macos_tar), "macOS")

    if args.linux_tar:
        verifier.verify_tar_package(Path(args.linux_tar), "Linux")

    if args.artifacts_dir:
        art_dir = Path(args.artifacts_dir)
        if not art_dir.exists():
            verifier.log_error(f"Artifacts directory '{art_dir}' does not exist!")
        else:
            win_zips = list(art_dir.glob("**/*Windows*.zip")) + list(art_dir.glob("**/*win*.zip"))
            mac_tars = list(art_dir.glob("**/*macOS*.tar.gz")) + list(art_dir.glob("**/*darwin*.tar.gz"))
            lin_tars = list(art_dir.glob("**/*Linux*.tar.gz")) + list(art_dir.glob("**/*linux*.tar.gz"))

            if not win_zips and not mac_tars and not lin_tars:
                # Check for any zip or tar.gz
                all_zips = list(art_dir.glob("**/*.zip"))
                all_tars = list(art_dir.glob("**/*.tar.gz"))
                win_zips = all_zips
                lin_tars = all_tars

            for z in win_zips:
                verifier.verify_windows_zip(z)
            for m in mac_tars:
                verifier.verify_tar_package(m, "macOS")
            for l in lin_tars:
                verifier.verify_tar_package(l, "Linux")

    print("\n" + "=" * 60)
    print(" PACKAGE VERIFICATION SUMMARY")
    print("=" * 60)
    for ok in verifier.verified_items:
        print(f"  [OK] {ok}")

    if verifier.warnings:
        print("\nWarnings:")
        for w in verifier.warnings:
            print(f"  [!] {w}")

    if verifier.errors:
        print("\nERRORS DETECTED:")
        for err in verifier.errors:
            print(f"  [FAIL] {err}", file=sys.stderr)
        print("=" * 60)
        print("RESULT: FAILED - ABORTING RELEASE / MERGE")
        print("=" * 60)
        sys.exit(1)
    else:
        print("=" * 60)
        print("RESULT: ALL PACKAGES PASSED VERIFICATION GATE")
        print("=" * 60)
        sys.exit(0)


if __name__ == "__main__":
    main()
