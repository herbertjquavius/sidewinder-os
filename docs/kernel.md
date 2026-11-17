# Sidewinder kernel and performance changes

Every change Sidewinder makes on top of Fedora Kinoite to get more out of games, and why.
All of it lives in `build/kernel.sh` (plus the power profile switch in `build/gaming.sh`).

## Kernel: CachyOS instead of Fedora's

- Package `kernel-cachyos` from the CachyOS team's Fedora repo (COPR `bieszczaders/kernel-cachyos`).
- Uses the BORE scheduler, which favors short bursts of work (input, rendering, audio) over long background jobs, so the game stays smooth while something else runs.
- Built for x86-64-v3 CPUs (anything from roughly 2015 onward, including every RTX 3050 laptop).
- Supports sched_ext, so a scheduler can be swapped in without changing the kernel (see LAVD below).

## Scheduler: LAVD on top

- `scx_lavd` from `scx-scheds`, started at boot by `scx_loader`.
- LAVD (Latency-criticality Aware Virtual Deadline) works out which tasks other tasks are waiting on, like a game's main and render threads, and runs those first.
- Started with `--autopower`, so it follows the power profile: full speed on the charger, saves battery when unplugged.
- If it ever misbehaves, the kernel falls back to BORE by itself.

## NVIDIA driver

- negativo17's NVIDIA packages, open kernel modules (the right choice for RTX 20 series and newer).
- The module is built for the CachyOS kernel at image build time, so nothing compiles on the laptop.
- `nvidia-drm.modeset=1` and `fbdev=1` for a proper Wayland desktop, nouveau blocked.
- Suspend, resume and hibernate helpers enabled so games survive closing the lid.
- On hybrid laptops (Intel or AMD graphics plus NVIDIA), Steam and its games run on the NVIDIA card.

## Secure Boot

- The kernel and NVIDIA module are signed with Sidewinder's own key (`keys/sidewinder-mok.pem` is the public half; the private half is only a GitHub secret).
- The installer enrolls the key, and the first boot asks once to confirm it (blue screen, one-time password).

## Small tweaks

| Setting | Value | Why |
|---|---|---|
| `kernel.split_lock_mitigate` | 0 | Some games trip split lock detection, and the default slows them down on purpose |
| `vm.max_map_count` | 2147483642 | Big games map a lot of memory, same value as SteamOS |
| Power profile | performance on charger, power-saver on battery | Switches by itself when the charger is plugged in or pulled out |

## Benchmarks

Run in a VM by the `bench` workflow: task switching speed (`hackbench`) and how long tasks wait to run while every CPU is busy (`cyclictest` under `stress-ng`).
A VM has no real graphics card, so these show responsiveness, not FPS. Real game numbers come from the laptop test.

_Results go here after the first run._
