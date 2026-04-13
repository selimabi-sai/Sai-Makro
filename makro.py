#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tek giris noktasi:
- Lokal CSV guncelleme
- TUİK fallback guncelleme
- Dashboard acma
- Tam otomatik deploy/push akisi
- Legacy pipeline cagirma
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
VENV_DIR = SCRIPT_DIR / ".venv"
VENV_PYTHON = VENV_DIR / "bin" / "python"
REQUIREMENTS_FILE = SCRIPT_DIR / "requirements.txt"

MODULE_SCRIPTS = {
    "enflasyon": "guncelle_enflasyon.py",
    "tufe": "guncelle_tufe.py",
    "ufe": "guncelle_ufe.py",
    "ysa": "guncelle_ysa.py",
    "konut": "guncelle_konut.py",
    "kredi_karti": "guncelle_kredi_karti.py",
}

BOOTSTRAP_MODULES = {
    "update": ("pandas", "evds"),
    "guncelle": ("pandas", "evds"),
    "fallback": ("pandas", "openpyxl", "xlrd"),
    "dashboard": ("streamlit", "pandas", "numpy", "plotly"),
    "legacy_indir": ("pandas", "evds"),
    "legacy_kesif": ("pandas", "evds"),
    "legacy_yukle": ("pandas", "evds", "google.oauth2", "google_auth_oauthlib", "googleapiclient"),
    "legacy_tam": ("pandas", "evds", "google.oauth2", "google_auth_oauthlib", "googleapiclient"),
}


def run(cmd: list[str], cwd: Path | None = None) -> int:
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    completed = subprocess.run(cmd, cwd=str(cwd or SCRIPT_DIR))
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed.returncode


def can_import(python_bin: str, module_name: str) -> bool:
    probe = (
        "import importlib.util, sys; "
        "raise SystemExit(0 if importlib.util.find_spec(sys.argv[1]) else 1)"
    )
    completed = subprocess.run(
        [python_bin, "-c", probe, module_name],
        cwd=str(SCRIPT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def create_venv() -> None:
    if VENV_PYTHON.exists():
        return
    print(f"\n>>> Sanal ortam olusturuluyor: {VENV_DIR}", flush=True)
    completed = subprocess.run(
        [sys.executable, "-m", "venv", str(VENV_DIR)],
        cwd=str(SCRIPT_DIR),
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def install_requirements(python_bin: str) -> None:
    if not REQUIREMENTS_FILE.exists():
        raise SystemExit(f"requirements.txt bulunamadi: {REQUIREMENTS_FILE}")
    run([python_bin, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])


def resolve_runtime_python(required_modules: tuple[str, ...] = ()) -> str:
    if VENV_PYTHON.exists():
        python_bin = str(VENV_PYTHON)
        missing = [mod for mod in required_modules if not can_import(python_bin, mod)]
        if missing:
            print(f"\n>>> Eksik paketler bulundu: {', '.join(missing)}", flush=True)
            install_requirements(python_bin)
        return python_bin

    if required_modules and all(can_import(sys.executable, mod) for mod in required_modules):
        return sys.executable

    if not required_modules:
        return sys.executable

    create_venv()
    python_bin = str(VENV_PYTHON)
    if required_modules:
        print("\n>>> Gerekli paketler kuruluyor", flush=True)
        install_requirements(python_bin)
    return python_bin


def run_python(
    script_name: str,
    extra_args: list[str] | None = None,
    required_modules: tuple[str, ...] = (),
) -> int:
    python_bin = resolve_runtime_python(required_modules)
    script_path = SCRIPT_DIR / script_name
    cmd = [python_bin, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)
    return run(cmd)


def run_local_update(selected: list[str]) -> int:
    required = BOOTSTRAP_MODULES["update"]
    for modul in selected:
        run_python(MODULE_SCRIPTS[modul], required_modules=required)

    fallback_targets = [modul for modul in selected if modul in {"tufe", "ufe"}]
    if fallback_targets:
        if len(fallback_targets) == 2:
            only = "both"
        else:
            only = fallback_targets[0]
        run_python(
            "guncelle_tuik_fiyat_fallback.py",
            ["--only", only],
            required_modules=BOOTSTRAP_MODULES["fallback"],
        )
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    if args.only or args.local_only:
        selected = args.only or list(MODULE_SCRIPTS.keys())
        return run_local_update(selected)

    extra_args: list[str] = []
    if args.no_push:
        extra_args.append("--no-push")
    if args.message:
        extra_args.extend(["--message", args.message])
    return run_python("sai_makro_otomatik_guncelle.py", extra_args)


def cmd_fallback(args: argparse.Namespace) -> int:
    extra_args: list[str] = ["--only", args.only]
    if args.dry_run:
        extra_args.append("--dry-run")
    if args.data_dir:
        extra_args.extend(["--data-dir", args.data_dir])
    return run_python(
        "guncelle_tuik_fiyat_fallback.py",
        extra_args,
        required_modules=BOOTSTRAP_MODULES["fallback"],
    )


def cmd_dashboard(args: argparse.Namespace) -> int:
    python_bin = resolve_runtime_python(BOOTSTRAP_MODULES["dashboard"])
    cmd = [
        python_bin,
        "-m",
        "streamlit",
        "run",
        str(SCRIPT_DIR / "sai_makro_dashboard.py"),
        "--server.port",
        str(args.port),
        "--server.address",
        args.host,
    ]
    if args.headless:
        cmd.extend(["--server.headless", "true"])
    return run(cmd)


def cmd_auto(args: argparse.Namespace) -> int:
    extra_args: list[str] = []
    if args.no_push:
        extra_args.append("--no-push")
    if args.message:
        extra_args.extend(["--message", args.message])
    return run_python("sai_makro_otomatik_guncelle.py", extra_args)


def cmd_legacy(args: argparse.Namespace) -> int:
    extra_args = [args.komut]
    if args.modul:
        extra_args.append("--modul")
        extra_args.extend(args.modul)
    required = BOOTSTRAP_MODULES[f"legacy_{args.komut}"]
    return run_python("sai_makro_veri.py", extra_args, required_modules=required)


def cmd_tuik_insaat(args: argparse.Namespace) -> int:
    extra_args = ["--start-year", str(args.start_year)]
    if args.out_dir:
        extra_args.extend(["--out-dir", args.out_dir])
    if args.overwrite:
        extra_args.append("--overwrite")
    return run_python("indir_tuik_insaat_excelleri.py", extra_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sai Makro tek giris noktasi")
    subparsers = parser.add_subparsers(dest="command", required=True)

    update_parser = subparsers.add_parser(
        "update",
        aliases=["guncelle"],
        help="Varsayilan olarak tam guncelleme + deploy/push akisini calistir",
    )
    update_parser.add_argument(
        "--only",
        nargs="+",
        choices=list(MODULE_SCRIPTS.keys()),
        help="Sadece secilen modulleri lokal olarak calistir",
    )
    update_parser.add_argument(
        "--local-only",
        action="store_true",
        help="Deploy/push yapmadan tum modulleri sadece lokal guncelle",
    )
    update_parser.add_argument(
        "--no-push",
        action="store_true",
        help="Deploy ve commit yap ama push etme",
    )
    update_parser.add_argument(
        "--message",
        help="Deploy commit mesaji",
    )
    update_parser.set_defaults(func=cmd_update)

    fallback_parser = subparsers.add_parser(
        "fallback",
        help="TUİK fallback fiyat guncellemesini calistir",
    )
    fallback_parser.add_argument(
        "--only",
        choices=("tufe", "ufe", "both"),
        default="both",
        help="Hangi fallback akisi calissin",
    )
    fallback_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dosya yazmadan farki goster",
    )
    fallback_parser.add_argument(
        "--data-dir",
        help="Varsayilan makro_data klasoru yerine farkli hedef kullan",
    )
    fallback_parser.set_defaults(func=cmd_fallback)

    dashboard_parser = subparsers.add_parser(
        "dashboard",
        help="Streamlit dashboard ac",
    )
    dashboard_parser.add_argument(
        "--port",
        type=int,
        default=8503,
        help="Streamlit portu",
    )
    dashboard_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Streamlit bind adresi",
    )
    dashboard_parser.add_argument(
        "--headless",
        action="store_true",
        help="Tarayici acmadan headless baslat",
    )
    dashboard_parser.set_defaults(func=cmd_dashboard)

    auto_parser = subparsers.add_parser(
        "auto",
        aliases=["otomatik"],
        help="Tam otomatik guncelleme + deploy/push akisini calistir",
    )
    auto_parser.add_argument(
        "--no-push",
        action="store_true",
        help="Commit olustur ama push etme",
    )
    auto_parser.add_argument(
        "--message",
        help="Commit mesaji",
    )
    auto_parser.set_defaults(func=cmd_auto)

    legacy_parser = subparsers.add_parser(
        "legacy",
        help="Eski all-in-one pipeline komutlarini cagirmak icin",
    )
    legacy_parser.add_argument(
        "komut",
        choices=("tam", "kesif", "indir", "yukle"),
        help="Legacy pipeline komutu",
    )
    legacy_parser.add_argument(
        "--modul",
        nargs="+",
        choices=("ysa", "enflasyon", "konut"),
        help="Legacy pipeline icin modul listesi",
    )
    legacy_parser.set_defaults(func=cmd_legacy)

    tuik_insaat_parser = subparsers.add_parser(
        "tuik-insaat",
        help="TUİK insaat Excel arsiv indirmesini calistir",
    )
    tuik_insaat_parser.add_argument(
        "--start-year",
        type=int,
        default=2015,
        help="Baslangic yili",
    )
    tuik_insaat_parser.add_argument(
        "--out-dir",
        help="Hedef klasor",
    )
    tuik_insaat_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Mevcut dosyalari tekrar indir",
    )
    tuik_insaat_parser.set_defaults(func=cmd_tuik_insaat)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
