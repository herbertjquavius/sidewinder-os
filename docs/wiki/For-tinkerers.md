# For tinkerers

Under the hood, Sidewinder is an **image-based** Fedora Kinoite system (bootc). The whole system is built as one image on GitHub, tested in a VM, and only then published. Your computer downloads it as one piece, so it can always swap back to the previous one.

## Handy commands
Open a terminal from Welcome → **TERMINAL**.

| Command | What it does |
|---|---|
| `bootc status` | Which version is running, staged and kept for going back |
| `sudo bootc upgrade` | Download the newest version now |
| `sudo bootc rollback` | Go back to the previous version (restart after) |
| `fastfetch` | System info |
| `scxctl get` or `systemctl status scx_loader` | Is the LAVD scheduler running |
| `powerprofilesctl get` | Current power profile |

## Installing things
- **Apps**: Discover or `flatpak install`. Best choice for almost everything.
- **Command line tools and dev stuff**: use a container with `distrobox` or `toolbox`, so the system stays clean.
- **System packages**: possible with `rpm-ostree install`, but it slows updates and can break them. Avoid unless you have to.

## How it's built
Everything is on the project page: the image build (`Containerfile`, `build/`), the kernel layer (`Containerfile.kernel`), branding (`branding/`), the welcome app (`welcome/`) and tests (`tests/`). `NOTES.md` is the map.
