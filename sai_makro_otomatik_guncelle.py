#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sai Makro tam guncelleme akisi:
1. Lokal veri scriptlerini calistirir.
2. Guncel CSV'leri deploy worktree'ye kopyalar.
3. Sadece veri dosyalarini commit eder.
4. SSH ile origin/main'e push eder.

Kullanim:
    python3 sai_makro_otomatik_guncelle.py
    python3 sai_makro_otomatik_guncelle.py --no-push
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent
DEPLOY_DIR = Path(os.environ.get("SAI_MAKRO_DEPLOY_DIR", "/tmp/makro_deploy"))
WINDOWS_PYTHON = os.environ.get(
    "SAI_MAKRO_WINDOWS_PYTHON",
    r"C:\Users\PDS\AppData\Local\Programs\Python\Python312\python.exe",
)

DATA_FILES = [
    "enflasyon.csv",
    "tufe.csv",
    "ufe.csv",
    "ysa.csv",
    "konut.csv",
    "kredi_karti.csv",
]
CODE_FILES = [
    ".gitignore",
    "config.py",
    "guncelle_enflasyon.py",
    "guncelle_konut.py",
    "guncelle_kredi_karti.py",
    "guncelle_tufe.py",
    "guncelle_tuik_fiyat_fallback.py",
    "guncelle_ufe.py",
    "guncelle_ysa.py",
    "makro.py",
    "requirements.txt",
    "sai_makro_dashboard.py",
    "sai_makro_guncelle.cmd",
    "sai_makro_otomatik_guncelle.py",
    "veri_kaynak_onceligi.py",
]
SYNC_PATHS = [f"makro_data/{name}" for name in DATA_FILES] + CODE_FILES

UPDATE_STEPS = [
    ("Enflasyon", ["guncelle_enflasyon.py"]),
    ("TUFE", ["guncelle_tufe.py"]),
    ("UFE", ["guncelle_ufe.py"]),
    ("TUİK Fallback", ["guncelle_tuik_fiyat_fallback.py", "--only", "both"]),
    ("YSA", ["guncelle_ysa.py"]),
    ("Konut", ["guncelle_konut.py"]),
    ("Kredi Karti", ["guncelle_kredi_karti.py"]),
]


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run(cmd: list[str], cwd: Path | None = None) -> str:
    log("KOMUT: " + " ".join(cmd))
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.stdout:
        print(proc.stdout, end="", flush=True)
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr, flush=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Komut basarisiz oldu ({proc.returncode}): {' '.join(cmd)}")
    return proc.stdout.strip()


def to_windows_path(path: Path) -> str:
    raw = str(path)
    if raw.startswith("/mnt/") and len(raw) > 6:
        drive = raw[5].upper()
        rest = raw[6:].replace("/", "\\")
        return f"{drive}:{rest}"
    raise ValueError(f"Windows yoluna cevrilemiyor: {path}")


def ps_quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def run_windows_python(args: list[str], cwd: Path) -> None:
    cmd = [
        "powershell.exe",
        "-Command",
        "& "
        + ps_quote(WINDOWS_PYTHON)
        + " "
        + " ".join(ps_quote(a) for a in args),
    ]
    run(cmd, cwd=cwd)


def normalize_origin_to_ssh(repo_dir: Path) -> None:
    origin = run(["git", "-C", str(repo_dir), "remote", "get-url", "origin"])
    prefix = "https://github.com/"
    if origin.startswith(prefix):
        ssh_url = "git@github.com:" + origin[len(prefix) :]
        run(["git", "-C", str(repo_dir), "remote", "set-url", "origin", ssh_url])


def ensure_deploy_worktree() -> None:
    normalize_origin_to_ssh(REPO_DIR)
    run(["git", "-C", str(REPO_DIR), "fetch", "origin"])
    run(["git", "-C", str(REPO_DIR), "worktree", "prune"])

    if (DEPLOY_DIR / ".git").exists():
        normalize_origin_to_ssh(DEPLOY_DIR)
        run(["git", "-C", str(DEPLOY_DIR), "fetch", "origin"])
        run(["git", "-C", str(DEPLOY_DIR), "reset", "--hard", "origin/main"])
        run(["git", "-C", str(DEPLOY_DIR), "clean", "-fd"])
        return

    if DEPLOY_DIR.exists():
        raise RuntimeError(f"Deploy klasoru var ama worktree degil: {DEPLOY_DIR}")

    run(
        [
            "git",
            "-C",
            str(REPO_DIR),
            "worktree",
            "add",
            "-B",
            "codex/sai-makro-release",
            str(DEPLOY_DIR),
            "origin/main",
        ]
    )
    normalize_origin_to_ssh(DEPLOY_DIR)


def run_update_steps() -> None:
    repo_win = to_windows_path(REPO_DIR)
    for label, step in UPDATE_STEPS:
        script_win = repo_win + "\\" + step[0]
        extra_args = step[1:]
        log(f"ADIM BASLADI: {label}")
        run_windows_python(["-u", script_win, *extra_args], cwd=REPO_DIR)
        log(f"ADIM TAMAMLANDI: {label}")


def copy_sync_files() -> None:
    for rel_path in SYNC_PATHS:
        src = REPO_DIR / rel_path
        dst = DEPLOY_DIR / rel_path
        if not src.exists():
            raise FileNotFoundError(f"Veri dosyasi bulunamadi: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        log(f"Kopyalandi: {rel_path}")


def changed_sync_files() -> list[str]:
    out = run(["git", "-C", str(DEPLOY_DIR), "status", "--porcelain", "--", *SYNC_PATHS])
    return [line[3:] for line in out.splitlines() if line.strip()]


def latest_dates() -> dict[str, str]:
    result = {}
    for name in DATA_FILES:
        csv_path = REPO_DIR / "makro_data" / name
        with csv_path.open("r", encoding="utf-8", errors="replace") as f:
            lines = [line.strip() for line in f if line.strip()]
        result[name] = lines[-1].split(",")[0] if len(lines) >= 2 else "BOS"
    return result


def commit_and_push(no_push: bool, commit_message: str) -> None:
    changes = changed_sync_files()
    if not changes:
        log("Veri farki yok. Commit ve push atlandi.")
        return

    run(["git", "-C", str(DEPLOY_DIR), "add", *SYNC_PATHS])
    run(["git", "-C", str(DEPLOY_DIR), "commit", "-m", commit_message])

    if no_push:
        log("no-push aktif. Commit olustu, push atlandi.")
        return

    run(["git", "-C", str(DEPLOY_DIR), "push", "origin", "HEAD:main"])
    short_hash = run(["git", "-C", str(DEPLOY_DIR), "rev-parse", "--short", "HEAD"])
    log(f"Push tamamlandi. Commit: {short_hash}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sai Makro otomatik guncelleme")
    parser.add_argument("--no-push", action="store_true", help="Commit olustur ama push etme")
    parser.add_argument(
        "--message",
        default="Refresh macro data snapshots",
        help="Commit mesaji",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    log("Sai Makro otomatik guncelleme basladi.")
    log(f"Repo: {REPO_DIR}")
    log(f"Deploy worktree: {DEPLOY_DIR}")

    ensure_deploy_worktree()
    run_update_steps()
    copy_sync_files()

    for name, tarih in latest_dates().items():
        log(f"Son veri tarihi | {name}: {tarih}")

    commit_and_push(args.no_push, args.message)
    log("Tum adimlar tamamlandi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
