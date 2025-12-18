# Unofficial Sm64CoopDx AppImage

![AppImage Sm64CoopDx](.img/portada.jpg)

| Component | Version | Download Link |
|-----------|---------|---------------|
| Sm64CoopDx.AppImage | 1.4 | [Sm64CoopDx.AppImage](https://github.com/retired64/Sm64coopdx.AppImage/releases/tag/v1.4) |


## Base ROM Required

> [!CAUTION]
> **You must provide your own legal ROM:**

```
~/.local/share/sm64coopdx/baserom.us.z64
```

The game won't start without this file.

---

> [!TIP]
> FUSE 2 Required This AppImage requires **FUSE 2** (`libfuse.so.2`). Most modern distros use FUSE 3 by default. Usually debian-based distributions As ubuntu for example in my case **Ubuntu 24.04.3 Noble Numbat** I do not require any type of lib fuse2 installation to run it

**Common error:**
```
dlopen(): libfuse.so.2: cannot open shared object file
```

**Fix:** Install FUSE 2 compatibility layer:
```bash
# Fedora
dnf install fuse fuse-libs
```

[Full installation guide](https://github.com/AppImage/AppImageKit/wiki/FUSE)

### Uncommon cases 
- ​The game won’t open, but you’ll be released by a bug that will say something like:

````
error while loading shared libraries: libSDL2-2.0.so.0: canning open object file...
````
### For window handling and control (SDL2)

````
sudo apt install libsdl2-2.0-0
````

### For graphics (GLEW)

````
sudo apt install libglew2.2 # (Number may vary depending on your Linux version)
````

## License

Educational project. SM64 Coop Deluxe belong to their respective authors.
**Users must provide their own legally obtained ROM.**

**Built by:** Retired64
**Credits:** See the full [credits and acknowledgments](./CREDITS.md) for the development team.
