import os
import sys
import zipfile
import shutil
import requests
import subprocess
import stat
import time
from pathlib import Path
from typing import Optional, Dict

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
    """Obtiene la ruta a recursos empaquetados o locales"""
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
        console.print(f"[dim]✓ Permisos aplicados a {path.name}[/dim]")

def download(url: str, out: Path, max_retries: int = 3):
    """Descarga un archivo con reintentos"""
    for attempt in range(max_retries):
        try:
            # Obtener tamaño del archivo
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
                task = progress.add_task(
                    f"Descargando {out.name} (intento {attempt + 1}/{max_retries})", 
                    total=total_size if total_size > 0 else None
                )
                
                r = requests.get(url, stream=True, timeout=30)
                r.raise_for_status()
                
                with open(out, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))
            
            console.print(f"[green]✔ Descarga completada: {out.name}[/green]")
            return  # Éxito, salir
            
        except Exception as e:
            console.print(f"[yellow]⚠ Error en intento {attempt + 1}: {e}[/yellow]")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Backoff exponencial
                console.print(f"[dim]Reintentando en {wait_time}s...[/dim]")
                time.sleep(wait_time)
                if out.exists():
                    out.unlink()  # Limpiar descarga parcial
            else:
                console.print(f"[bold red]✖ Error al descargar después de {max_retries} intentos[/bold red]")
                raise

def extract_with_progress(zip_path: Path, extract_dir: Path):
    """Extrae un archivo ZIP con barra de progreso"""
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
    console.print(f"[green]✔ Extracción completada: {len(files)} archivos[/green]")

def get_latest_linux_release() -> Optional[Dict[str, str]]:
    """Obtiene la última versión disponible para Linux"""
    try:
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
    except requests.RequestException as e:
        console.print(f"[bold red]✖ Error al conectar con GitHub: {e}[/bold red]")
        return None
    
    return None

def cleanup(*paths: Path):
    """Limpia archivos y directorios temporales"""
    for path in paths:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
                console.print(f"[dim]✓ Directorio eliminado: {path}[/dim]")
            else:
                path.unlink()
                console.print(f"[dim]✓ Archivo eliminado: {path}[/dim]")

# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():
    console.print(Panel.fit(
        "[bold green]SM64 Co-op Deluxe Builder[/bold green]\n"
        "AppImage + Mods Package Generator (go-appimage)",
        border_style="green"
    ))

    # Variables de limpieza
    appdir = Path.cwd() / "AppDir"
    extract_dir = Path("_temp_extract")
    zip_file = None
    
    try:
        # Validar assets
        if not APPIMAGETOOL.exists():
            console.print(f"[bold red]✖ No se encontró {APPIMAGETOOL.name}[/bold red]")
            console.print(f"[dim]Esperado en: {APPIMAGETOOL}[/dim]")
            sys.exit(1)
        
        if not ICON_PATH.exists():
            console.print(f"[bold red]✖ No se encontró sm64coopdx.png en assets[/bold red]")
            console.print(f"[dim]Esperado en: {ICON_PATH}[/dim]")
            sys.exit(1)
        
        # Obtener última versión
        console.print("[cyan]Consultando última versión...[/cyan]")
        release = get_latest_linux_release()
        
        if not release:
            console.print("[bold red]✖ No se encontró ninguna versión de Linux[/bold red]")
            sys.exit(1)

        version = release["version"]
        console.print(f"[green]✔ Versión detectada:[/green] [bold]{version}[/bold]")

        # Limpiar AppDir si existe
        if appdir.exists():
            console.print("[dim]Limpiando AppDir anterior...[/dim]")
            shutil.rmtree(appdir)
        
        # Crear estructura FHS
        console.print("[cyan]Creando estructura de directorios...[/cyan]")
        (appdir / "usr/bin").mkdir(parents=True)
        (appdir / "usr/lib").mkdir(parents=True)
        (appdir / "usr/share/applications").mkdir(parents=True)
        (appdir / "usr/share/icons/hicolor/256x256/apps").mkdir(parents=True)
        
        # Crear archivo .desktop
        desktop_path = appdir / "usr/share/applications/sm64coopdx.desktop"
        desktop_path.write_text(DESKTOP_TEMPLATE)
        console.print(f"[dim]✓ Archivo .desktop creado[/dim]")
        
        # Copiar icono
        shutil.copy(ICON_PATH, appdir / "usr/share/icons/hicolor/256x256/apps/sm64coopdx.png")
        console.print(f"[dim]✓ Icono copiado[/dim]")

        # Descargar y extraer
        zip_file = Path(release["name"])
        if not zip_file.exists():
            download(release["url"], zip_file)
        else:
            console.print(f"[yellow]⚠ Usando archivo existente: {zip_file}[/yellow]")
        
        if extract_dir.exists(): 
            shutil.rmtree(extract_dir)
        extract_dir.mkdir()

        extract_with_progress(zip_file, extract_dir)

        # Nombre del archivo de mods (CON extensión)
        mods_zip_name = f"mods-{version}"
        
        # Mover archivos a la estructura correcta
        console.print("[cyan]Procesando archivos...[/cyan]")
        
        files_moved = 0
        for item in extract_dir.iterdir():
            if item.name == "sm64coopdx":
                shutil.move(str(item), str(appdir / "usr/bin/sm64coopdx"))
                console.print(f"[dim]✓ Binario movido[/dim]")
                files_moved += 1
            elif "libdiscord_game_sdk" in item.name:
                shutil.move(str(item), str(appdir / "usr/lib/libdiscord_game_sdk.so"))
                console.print(f"[dim]✓ Librería Discord movida[/dim]")
                files_moved += 1
            elif item.name in ["lang", "palettes"]:
                dest = appdir / "usr/bin" / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(item), str(dest))
                console.print(f"[dim]✓ Directorio {item.name} movido[/dim]")
                files_moved += 1
            elif item.name == "mods":
                shutil.make_archive(mods_zip_name, 'zip', item)
                console.print(f"[dim]✓ Mods empaquetados[/dim]")
                files_moved += 1

        if files_moved == 0:
            console.print("[bold red]✖ No se movieron archivos. Verifica la estructura del ZIP.[/bold red]")
            sys.exit(1)

        console.print(f"[green]✔ {files_moved} componentes procesados[/green]")

        # Aplicar permisos
        console.print("[cyan]Aplicando permisos...[/cyan]")
        make_executable(appdir / "usr/bin/sm64coopdx")
        
        discord_lib = appdir / "usr/lib/libdiscord_game_sdk.so"
        if discord_lib.exists():
            # Las librerías NO necesitan permisos de ejecución normalmente
            # pero por si acaso se mantiene la lógica original
            discord_lib.chmod(0o755)

        # Limpiar temporales
        console.print("[cyan]Limpiando archivos temporales...[/cyan]")
        cleanup(extract_dir, zip_file)

        # Hacer ejecutable appimagetool
        make_executable(APPIMAGETOOL)

        # PASO 1: Deploy
        console.print("\n[bold cyan]📦 Paso 1: Generando estructura AppImage (deploy)...[/bold cyan]")
        
        appdir_absolute = appdir.resolve()
        desktop_file_path = appdir_absolute / "usr/share/applications/sm64coopdx.desktop"
        
        result_deploy = subprocess.run(
            [str(APPIMAGETOOL), "deploy", str(desktop_file_path)],
            capture_output=True,
            text=True
        )
        
        if result_deploy.returncode != 0:
            console.print("[bold red]✖ Falló el deploy:[/bold red]")
            console.print(result_deploy.stderr)
            sys.exit(1)
        
        console.print("[green]✔ Deploy completado[/green]")

        # PASO 2: Build
        console.print("\n[bold cyan]📦 Paso 2: Construyendo AppImage...[/bold cyan]")
        
        final_output_name = f"Sm64CoopDX-{version}-x86_64.AppImage"

        result_build = subprocess.run(
            [str(APPIMAGETOOL), str(appdir_absolute)],
            env={**os.environ, "ARCH": "x86_64"},
            capture_output=True,
            text=True
        )
        
        if result_build.returncode != 0:
            console.print("[bold red]✖ Falló la construcción:[/bold red]")
            console.print(result_build.stderr)
            sys.exit(1)

        console.print("[green]✔ AppImage construida[/green]")

        # Renombrado inteligente
        console.print("\n[cyan]Verificando archivo generado...[/cyan]")
        
        # Buscar AppImage generada (excluyendo el tool)
        generated_appimages = [
            f for f in Path(".").glob("*.AppImage")
            if f.name != APPIMAGETOOL.name and f.stat().st_mtime > time.time() - 60
        ]
        
        if not generated_appimages:
            console.print("[bold red]✖ No se encontró el AppImage generado[/bold red]")
            sys.exit(1)
        
        # Tomar el más reciente
        found_appimage = max(generated_appimages, key=lambda f: f.stat().st_mtime)
        
        if found_appimage.name != final_output_name:
            console.print(f"[dim]Renombrando: {found_appimage.name} → {final_output_name}[/dim]")
            if Path(final_output_name).exists():
                Path(final_output_name).unlink()
            found_appimage.rename(final_output_name)
        else:
            console.print(f"[dim]El archivo ya tiene el nombre correcto[/dim]")

        # Verificar archivo final
        final_path = Path(final_output_name)
        if not final_path.exists():
            console.print(f"[bold red]✖ No se encontró {final_output_name}[/bold red]")
            sys.exit(1)

        # Limpiar AppDir
        cleanup(appdir)
        
        # Resumen final
        console.print("\n" + "="*60)
        console.print(f"[bold green]✔ BUILD EXITOSO[/bold green]")
        console.print("="*60)
        console.print(f"[bold]AppImage:[/bold] {final_output_name}")
        console.print(f"[bold]Tamaño:[/bold] {final_path.stat().st_size / (1024*1024):.2f} MB")
        console.print(f"[bold]Mods:[/bold] {mods_zip_name}.zip")
        console.print(f"[dim]Compatible con FUSE 2 y FUSE 3[/dim]")
        console.print("="*60)

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Proceso interrumpido por el usuario[/yellow]")
        cleanup(appdir, extract_dir, zip_file)
        sys.exit(130)
    
    except Exception as e:
        console.print(f"\n[bold red]✖ Error inesperado: {e}[/bold red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        cleanup(appdir, extract_dir, zip_file)
        sys.exit(1)

if __name__ == "__main__":
    main()
