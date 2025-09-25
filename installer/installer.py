#!/usr/bin/env python3
import os, sys, tempfile, shutil, zipfile, logging, requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

# CONFIG
RELEASE_URI = "https://github.com/yourname/your-repo/releases/latest/download/your_mod.zip"
HW2_HOGAN_PATH = Path("Packages") / "Microsoft.HoganThreshold_8wekyb3d8bbwe" / "LocalState"
VERSION = "1_11_2931_2"
TIMEOUT = 10

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def get_local_state_dir() -> Path:
    appdata = os.environ.get("LOCALAPPDATA")
    if not appdata:
        raise RuntimeError("LOCALAPPDATA environment variable missing")
    return Path(appdata) / HW2_HOGAN_PATH

def local_pkg_dir(local_state: Path, version: str) -> Path:
    return local_state / "GTS" / f"{version}_active"

def pkg_path(local_state: Path, version: str) -> Path:
    return local_pkg_dir(local_state, version) / "maethrillian.pkg"

def manifest_path(local_state: Path, version: str) -> Path:
    return local_pkg_dir(local_state, version) / f"{version}_file_manifest.xml"

def download_release_to_temp(uri: str, timeout: int = TIMEOUT) -> Path:
    logging.info("Downloading release...")
    resp = requests.get(uri, stream=True, timeout=timeout)
    resp.raise_for_status()
    td = Path(tempfile.mkdtemp())
    out = td / "release.zip"
    with out.open("wb") as fh:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                fh.write(chunk)
    logging.info("Downloaded to %s", out)
    return out

def read_published_utc(manifest_file: Path) -> Optional[int]:
    if not manifest_file.exists():
        return None
    try:
        tree = ET.parse(manifest_file)
        return int(tree.getroot().get("published_utc"))
    except Exception:
        logging.exception("Failed to parse manifest %s", manifest_file)
        return None

def read_published_utc_from_zip(zip_path: Path) -> Optional[int]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name.endswith("_file_manifest.xml") or name.endswith(".xml"):
                with zf.open(name) as fh:
                    try:
                        root = ET.fromstring(fh.read())
                        return int(root.get("published_utc"))
                    except Exception:
                        continue
    return None

def safe_extract_zip(zip_path: Path, dest: Path):
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            target = (dest / member).resolve()
            if not str(target).startswith(str(dest.resolve())):
                raise Exception("Unsafe zip member: %s" % member)
        zf.extractall(path=dest)

def atomic_install(zip_path: Path, target_dir: Path):
    logging.info("Installing to %s", target_dir)
    tmp_dir = Path(tempfile.mkdtemp())
    backup_dir = None
    try:
        safe_extract_zip(zip_path, tmp_dir)
        if target_dir.exists():
            backup_dir = target_dir.with_suffix(".bak")
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            target_dir.rename(backup_dir)
        tmp_dir.rename(target_dir)
        if backup_dir and backup_dir.exists():
            shutil.rmtree(backup_dir)
        logging.info("Install complete")
    except Exception:
        logging.exception("Install failed")
        # try restore
        if backup_dir and backup_dir.exists() and not target_dir.exists():
            backup_dir.rename(target_dir)
        raise
    finally:
        # cleanup any remaining tmp
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)

def uninstall(target_dir: Path):
    if target_dir.exists():
        shutil.rmtree(target_dir)
        logging.info("Uninstalled %s", target_dir)
    else:
        logging.info("Nothing to uninstall at %s", target_dir)

def status(local_state: Path, version: str, zip_path: Optional[Path] = None) -> str:
    target = local_pkg_dir(local_state, version)
    if not target.exists():
        return "Mod not installed"
    if not pkg_path(local_state, version).exists() or not manifest_path(local_state, version).exists():
        return "Installed but files missing or corrupted"
    local_time = read_published_utc(manifest_path(local_state, version))
    remote_time = read_published_utc_from_zip(zip_path) if zip_path else None
    if remote_time and local_time and remote_time > local_time:
        return "Outdated"
    return "Installed and up to date"

def main():
    local_state = get_local_state_dir()
    logging.info("LocalState dir: %s", local_state)
    tmp_zip = None
    try:
        tmp_zip = download_release_to_temp(RELEASE_URI)
    except Exception as e:
        logging.error("Could not download release: %s", e)

    while True:
        print("\n(I)nstall  (U)ninstall  (S)tatus  (Q)uit")
        cmd = input("Choice: ").lower().strip()
        if cmd == "i":
            if tmp_zip is None:
                try:
                    tmp_zip = download_release_to_temp(RELEASE_URI)
                except Exception as e:
                    print("Download failed:", e); continue
            try:
                atomic_install(tmp_zip, local_pkg_dir(local_state, VERSION))
                print("Installed.")
            except Exception as e:
                print("Install failed:", e)
        elif cmd == "u":
            uninstall(local_pkg_dir(local_state, VERSION))
        elif cmd == "s":
            st = status(local_state, VERSION, zip_path=tmp_zip)
            print(st)
        elif cmd == "q":
            break
        else:
            print("Unknown command")

if __name__ == "__main__":
    main()
