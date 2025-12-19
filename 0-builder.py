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
APPIMAGETOOL = ASSETS_DIR / "appimagetool-940-x86_64.AppImage"
ICON_PATH = ASSETS_DIR / "sm64coopdx.png"

DESKTOP_TEMPLATE = """[Desktop Entry]
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
    """Otorga permisos rwxr-xr-x (755)"""
    if path.exists():
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
        "AppImage + Mods Package Generator (go-appimage)",
        border_style="green"
    ))

    release = get_latest_linux_release()
    if not release:
        console.print("[bold red]✖ No se encontró ninguna versión de Linux[/bold red]")
        sys.exit(1)

    version = release["version"]
    appdir = Path.cwd() / "AppDir"
    appdir_absolute = appdir.resolve()

    console.print(f"[green]✔ Versión detectada:[/green] [bold]{version}[/bold]")

    # Limpiar AppDir si existe
    if appdir.exists():
        shutil.rmtree(appdir)
    
    # Crear estructura FHS completa
    console.print("[dim]Creando estructura de directorios...[/dim]")
    (appdir / "usr/bin").mkdir(parents=True)
    (appdir / "usr/lib").mkdir(parents=True)
    (appdir / "usr/share/applications").mkdir(parents=True)
    (appdir / "usr/share/icons/hicolor/256x256/apps").mkdir(parents=True)
    
    # Crear archivo .desktop
    desktop_path = appdir / "usr/share/applications/sm64coopdx.desktop"
    desktop_path.write_text(DESKTOP_TEMPLATE)
    
    # Copiar icono
    if ICON_PATH.exists():
        shutil.copy(ICON_PATH, appdir / "usr/share/icons/hicolor/256x256/apps/sm64coopdx.png")
    else:
        console.print("[bold red]✖ Error: No se encontró sm64coopdx.png en assets[/bold red]")
        sys.exit(1)

    # Descargar y extraer
    zip_name = Path(release["name"])
    if not zip_name.exists():
        download(release["url"], zip_name)
    
    extract_dir = Path("_temp_extract")
    if extract_dir.exists(): 
        shutil.rmtree(extract_dir)
    extract_dir.mkdir()

    extract_with_progress(zip_name, extract_dir)

    mods_zip_name = f"mods-{version}"
    
    # Mover archivos a la estructura correcta
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("Procesando archivos")

        for item in extract_dir.iterdir():
            if item.name == "sm64coopdx":
                shutil.move(str(item), str(appdir / "usr/bin/sm64coopdx"))
            elif "libdiscord_game_sdk" in item.name:
                shutil.move(str(item), str(appdir / "usr/lib/libdiscord_game_sdk.so"))
            elif item.name in ["lang", "palettes"]:
                dest = appdir / "usr/bin" / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(item), str(dest))
            elif item.name == "mods":
                shutil.make_archive(mods_zip_name, 'zip', item)

    # Aplicar permisos al binario
    console.print("[dim]Aplicando permisos...[/dim]")
    make_executable(appdir / "usr/bin/sm64coopdx")
    
    discord_lib = appdir / "usr/lib/libdiscord_game_sdk.so"
    if discord_lib.exists():
        make_executable(discord_lib)

    # Limpiar archivos temporales
    shutil.rmtree(extract_dir)
    if zip_name.exists(): 
        zip_name.unlink()

    # Verificar appimagetool
    if not APPIMAGETOOL.exists():
        console.print("[bold red]✖ No se encontró appimagetool-940-x86_64.AppImage[/bold red]")
        sys.exit(1)

    make_executable(APPIMAGETOOL)

    # PASO 1: Deploy (genera AppRun y estructura)
    console.print("\n[bold cyan]📦 Paso 1: Generando estructura AppImage (deploy)...[/bold cyan]")
    
    desktop_file_path = appdir_absolute / "usr/share/applications/sm64coopdx.desktop"
    
    result_deploy = subprocess.run(
        [str(APPIMAGETOOL), "deploy", str(desktop_file_path)],
        capture_output=True,
        text=True
    )
    
    if result_deploy.returncode != 0:
        console.print("[bold red]Falló el deploy:[/bold red]")
        console.print(result_deploy.stderr)
        sys.exit(1)
    
    console.print("[green]✔ Deploy completado[/green]")

    # PASO 2: Build (construye la AppImage)
    console.print("\n[bold cyan]📦 Paso 2: Construyendo AppImage...[/bold cyan]")
    
    # Nombre final deseado
    final_output_name = f"Sm64CoopDX-{version}-x86_64.AppImage"

    result_build = subprocess.run(
        [str(APPIMAGETOOL), str(appdir_absolute)],
        env={**os.environ, "ARCH": "x86_64"},
        capture_output=True,
        text=True
    )
    
    if result_build.returncode != 0:
        console.print("[bold red]Falló la construcción:[/bold red]")
        console.print(result_build.stderr)
        sys.exit(1)

    # ---------------------------------------------------------
    # LÓGICA DE RENOMBRADO AUTOMÁTICO
    # ---------------------------------------------------------
    
    # Escaneamos el directorio actual buscando archivos .AppImage
    # Excluimos el builder (APPIMAGETOOL) y buscamos el generado
    found_appimage = None
    
    # Lista de todos los archivos AppImage en el directorio actual
    current_files = list(Path(".").glob("*.AppImage"))
    
    for f in current_files:
        # Ignorar la herramienta constructora
        if f.name == APPIMAGETOOL.name:
            continue
        # Ignorar si por alguna razón ya existe el archivo final
        if f.name == final_output_name:
            found_appimage = f
            break
        
        # Asumimos que cualquier otro AppImage es el generado
        # (Idealmente en un entorno de CI limpio, solo habrá uno nuevo)
        found_appimage = f
        break

    if found_appimage:
        if found_appimage.name != final_output_name:
            console.print(f"[dim]Renombrando: {found_appimage.name} -> {final_output_name}[/dim]")
            # Si ya existe el destino, lo borramos para evitar error
            if Path(final_output_name).exists():
                Path(final_output_name).unlink()
            found_appimage.rename(final_output_name)
        else:
            console.print(f"[dim]El archivo ya tiene el nombre correcto.[/dim]")
    else:
        console.print("[bold red]⚠ Advertencia: No se pudo identificar el archivo AppImage generado para renombrarlo.[/bold red]")

    # ---------------------------------------------------------

    # Limpiar
    shutil.rmtree(appdir)
    
    console.print(f"\n[bold green]✔ Finalizado:[/bold green] {final_output_name} y {mods_zip_name}.zip")
    console.print(f"[dim]AppImage compatible con FUSE 2 y FUSE 3[/dim]")

if __name__ == "__main__":
    main()
