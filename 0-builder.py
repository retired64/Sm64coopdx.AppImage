import os
import sys
import zipfile
import shutil
import requests
import subprocess
import stat
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
    SpinnerColumn
)

console = Console()

def resource_path(relative: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative
    return Path(relative)

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
REPO = "coop-deluxe/sm64coopdx"
API = f"https://api.github.com/repos/{REPO}/releases"

ASSETS_DIR = resource_path("assets")
APPIMAGETOOL = ASSETS_DIR / "appimagetool-x86_64.AppImage"
ICON_PATH = ASSETS_DIR / "sm64coopdx.png" 

APPRUN_CONTENT = """#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin/:${HERE}/usr/sbin/:${HERE}/usr/games/:${HERE}/bin/:${HERE}/sbin/${PATH:+:$PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib/:${HERE}/usr/lib/i386-linux-gnu/:${HERE}/usr/lib/x86_64-linux-gnu/:${HERE}/usr/lib32/:${HERE}/usr/lib64/:${HERE}/lib/:${HERE}/lib/i386-linux-gnu/:${HERE}/lib/x86_64-linux-gnu/:${HERE}/lib32/:${HERE}/lib64/${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
EXEC="${HERE}/sm64coopdx"
exec "${EXEC}" "$@"
"""

DESKTOP_TEMPLATE = """[Desktop Entry]
Version={version}
Type=Application
Name=SM64 Co-op Deluxe
GenericName=Multiplayer Platformer
Comment=Online multiplayer project for the Super Mario 64 PC port
TryExec=sm64coopdx
Exec=sm64coopdx %U
Icon=sm64coopdx
Terminal=false
StartupNotify=true
Categories=Game;ActionGame;AdventureGame;
Keywords=mario;super mario;sm64;nintendo;platformer;multiplayer;coop;
MimeType=x-scheme-handler/sm64coopdx;
"""

# -------------------------------------------------
# UTILS
# -------------------------------------------------

def make_executable(path: Path):
    """Otorga permisos rwxr-xr-x (755) corrigiendo las constantes de stat"""
    if path.exists():
        # Corregido: stat.S_IXUSR, stat.S_IXGRP, stat.S_IXOTH en MAYÚSCULAS
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def download(url: str, out: Path):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        total_size = int(response.headers.get('content-length', 0))
    except:
        total_size = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(complete_style="green", finished_style="bold green"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"Descargando {out.name}", total=total_size if total_size > 0 else None)
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))

def extract_with_progress(zip_path: Path, extract_dir: Path):
    with zipfile.ZipFile(zip_path, "r") as z:
        files = z.infolist()
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(complete_style="green", finished_style="bold green"),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Extrayendo archivos", total=len(files))
            for file in files:
                z.extract(file, extract_dir)
                progress.update(task, advance=1)

def get_latest_linux_release():
    r = requests.get(API, timeout=10)
    r.raise_for_status()
    for release in r.json():
        for asset in release.get("assets", []):
            name = asset["name"].lower()
            if "linux" in name and name.endswith(".zip"):
                return {
                    "version": release["tag_name"].lstrip("v"),
                    "url": asset["browser_download_url"],
                    "name": asset["name"]
                }
    return None

# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():
    console.print(Panel.fit(
        "[bold green]SM64 Co-op Deluxe Builder[/bold green]\n"
        "AppImage + Mods Package Generator",
        border_style="green"
    ))

    release = get_latest_linux_release()
    if not release:
        console.print("[bold red]✖ No se encontró ninguna versión de Linux[/bold red]")
        sys.exit(1)

    version = release["version"]
    appdir = Path.cwd() / f"sm64coopdx.AppDir"

    console.print(f"[green]✔ Versión detectada:[/green] [bold]{version}[/bold]")

    if appdir.exists():
        shutil.rmtree(appdir)
    
    appdir.mkdir(parents=True)
    (appdir / "lib").mkdir()
    
    console.print("[dim]Generando archivos de configuración...[/dim]")
    
    apprun_path = appdir / "AppRun"
    apprun_path.write_text(APPRUN_CONTENT)
    
    desktop_path = appdir / "sm64coopdx.desktop"
    desktop_path.write_text(DESKTOP_TEMPLATE.format(version=version))
    
    if ICON_PATH.exists():
        shutil.copy(ICON_PATH, appdir / "sm64coopdx.png")
    else:
        console.print("[bold red]✖ Error: No se encontró sm64coopdx.png en assets[/bold red]")
        sys.exit(1)

    zip_name = Path(release["name"])
    if not zip_name.exists():
        download(release["url"], zip_name)
    
    extract_dir = Path("_temp_extract")
    if extract_dir.exists(): shutil.rmtree(extract_dir)
    extract_dir.mkdir()

    extract_with_progress(zip_name, extract_dir)

    mods_zip_name = f"mods-{version}"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("Procesando archivos")

        for item in extract_dir.iterdir():
            if item.name == "sm64coopdx":
                shutil.move(str(item), str(appdir / "sm64coopdx"))
            elif "libdiscord_game_sdk" in item.name:
                shutil.move(str(item), str(appdir / "lib/libdiscord_game_sdk.so"))
            elif item.name in ["lang", "palettes"]:
                if (appdir / item.name).exists():
                    shutil.rmtree(appdir / item.name)
                shutil.move(str(item), str(appdir / item.name))
            elif item.name == "mods":
                shutil.make_archive(mods_zip_name, 'zip', item)

    console.print("[dim]Aplicando permisos...[/dim]")
    make_executable(apprun_path)
    make_executable(desktop_path)
    make_executable(appdir / "sm64coopdx")
    
    discord_lib = appdir / "lib/libdiscord_game_sdk.so"
    if discord_lib.exists():
        make_executable(discord_lib)

    shutil.rmtree(extract_dir)
    if zip_name.exists(): zip_name.unlink()

    console.print("\n[bold cyan]📦 Construyendo AppImage...[/bold cyan]")
    
    if not APPIMAGETOOL.exists():
        console.print("[bold red]✖ No se encontró appimagetool[/bold red]")
        sys.exit(1)

    make_executable(APPIMAGETOOL)
    output_image = f"Sm64CoopDX-{version}-x86_64.AppImage"

    result = subprocess.run(
        [str(APPIMAGETOOL), str(appdir), output_image],
        env={**os.environ, "ARCH": "x86_64"},
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        console.print("[bold red]Falló la construcción:[/bold red]")
        console.print(result.stderr)
        sys.exit(1)

    shutil.rmtree(appdir)
    console.print(f"\n[bold green]✔ Finalizado:[/bold green] {output_image} y {mods_zip_name}.zip")

if __name__ == "__main__":
    main()
