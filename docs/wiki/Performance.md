# Performance

## The simple stuff
1. **Plug in the charger.** On battery, Sidewinder saves power and games run slower. On the charger, it goes full power by itself.
2. **GAME MODE** in the welcome app forces full power right now.
3. **Close other apps**, especially web browsers.
4. **Lower the game's settings** or use FSR/DLSS if the game has it.

## What Sidewinder does for you
- **CachyOS kernel**: the core of the system, tuned to keep games smooth while other stuff runs.
- **LAVD scheduler**: decides what the processor works on next, and puts the game first.
- **NVIDIA driver** built in, and games run on the NVIDIA card automatically on laptops that have two graphics chips.
- A couple of settings some games need, already set.

The full details and benchmarks are on the project page in `docs/kernel.md`.

## See your FPS
Steam: right-click the game → Properties → Launch options → `mangohud %command%`
