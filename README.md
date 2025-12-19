# Unofficial SM64 Coop Deluxe AppImage

![AppImage Sm64CoopDx](.img/portada.jpg)

A portable, (universal fuse x86_64) Linux build for **SM64 Coop Deluxe**.
Built with **go-appimage** to ensure compatibility across modern (Arch, Fedora 40+) and traditional (Ubuntu, Debian) distributions without complex setups.

## Downloads

| File | Description | Link |
| --- | --- | --- |
| **Sm64CoopDX-x86_64.AppImage** | Main Game Executable | **[Download Latest](https://github.com/retired64/Sm64coopdx.AppImage/releases/download/v1.4/Sm64CoopDX-1.4-x86_64.AppImage)** |
| **mods.zip** | Recommended Mods Pack | **[Download Latest](https://github.com/retired64/Sm64coopdx.AppImage/releases/download/v1.4/mods-1.4.zip)** |


> [!IMPORTANT]
> **You must provide your own legally obtained ROM.**
> The game **will not start** without this file.

Place your ROM file exactly at this location:

```bash
~/.local/share/sm64coopdx/baserom.us.z64

```

*Note: You may need to create the folders if they don't exist.*


## Quick Start

1. **Download** the `.AppImage` file.
2. **Make it executable** and run:

```bash
chmod +x Sm64CoopDX-*-x86_64.AppImage
./Sm64CoopDX-*-x86_64.AppImage

```


## 🛠 Compatibility & Requirements

### FUSE Support (Universal)

> [!TIP]
> **No extra configuration needed.**
> Unlike older AppImages, this build supports both **FUSE 2** and **FUSE 3** natively.
> * Works out-of-the-box on **Ubuntu 24.04** (FUSE 3).
> * Works out-of-the-box on older systems (FUSE 2).
> 
> 

### System Dependencies

The AppImage bundles most libraries, but if you are on a very minimal installation and the game fails to open, you might need these basic packages:

**Debian / Ubuntu:**

```bash
sudo apt update
sudo apt install libsdl2-2.0-0 libglew2.2

```

**Fedora:**

```bash
sudo dnf install SDL2 glew

```

**Arch Linux:**

```bash
sudo pacman -S sdl2 glew

```

---

## Troubleshooting

If the game does not launch, run the AppImage from the terminal to see the error log:

```bash
./Sm64CoopDX-*-x86_64.AppImage

```

**Common Errors:**

* **`baserom.us.z64 not found`**: Double-check you placed the ROM in `~/.local/share/sm64coopdx/`.
* **Graphics issues**: Ensure your GPU drivers (Mesa/Nvidia) are up to date.


## License & Credits

**Educational Project.** This is an unofficial build script.
**SM64 Co-op Deluxe** belongs to the [sm64coopdx Team](https://github.com/coop-deluxe/sm64coopdx).

* **Build maintained by:** Retired64
* **Build Tool:** Custom Python script using `go-appimage`.

See the full [CREDITS.md](CREDITS.md) for the original development team.
