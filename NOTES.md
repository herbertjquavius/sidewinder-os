# Project
Sidewinder: plug-and-play gaming Linux distro for an RTX 3050 hybrid laptop

# Files
distro.env - Distro name, the one place to rename
branding/make.py - Renders all branding into branding/out (python3 make.py)
branding/sprites.py - Palette, F-16 pixel art, 5x7 pixel font
branding/font.py - Builds the pixel font as a TTF
branding/templates/ - Login screen (SDDM), KDE global theme + splash, wallpaper package, GRUB theme
branding/preview_qml.py - Renders login and splash offscreen into out/preview-2.png
Containerfile - Renders branding, then builds the system image on Kinoite
build/build.sh - Installs branding and settings inside the image
Justfile - just build / disk / iso / test
tests/vm-boot.sh - Boots the test disk headless, screenshot every 10s
tests/shots.py - Passes only if our login screen shows up
.github/workflows/build.yml - Build, VM test, publish to GHCR only if test passes; ISO on manual run
welcome/welcome.py - Welcome app (PySide6): update, fix problems, game mode, go back, forums, terminal
build/kernel.sh - CachyOS kernel swap, NVIDIA akmod build + signing, kernel signing, LAVD, sysctl
keys/sidewinder-mok.pem - Public half of the Secure Boot key (private half only in the MOK_KEY secret)
build/extras.sh - Save backups, GE-Proton, battery care, Firefox backup setup, Radar install, sounds, cursor and icons
browser/ - Radar, our own browser (radar.py, PySide6 Qt WebEngine), blocklist.txt, youtube.js ad skipper
branding/icons.py - Pixel icon theme (folders, trash, terminal, settings, store, files)
build/gaming.sh - Gaming apps (Flatpak, first boot), controller rules, charger-based power profiles, background updates
welcome/helper.sh - Root tasks for the welcome app via pkexec (bootc upgrade/rollback, restart network)

# Done
- Branding v1: logo (SVG + PNG), wordmark, wallpaper (1080p/1440p/4K), Plymouth boot splash
- Branding v2: F-16 jets (brother's favorite), flat airfield lights, own pixel font (TTF + GRUB pf2),
  SDDM login, KDE color scheme, KDE global theme + startup splash, GRUB boot menu theme

- Phase 1 files written: image build, CI, VM boot test, ISO build (not run yet)
- Welcome app v1, shows once on first login, then lives in the app menu (actions untested until a real install)
- Gaming defaults: Steam, Heroic, Lutris, ProtonUp-Qt, MangoHud, gamemode; controller rules;
  performance on charger, power saver on battery; updates download twice a day, never auto-reboot

- Phase 3 started: CachyOS kernel (COPR bieszczaders), NVIDIA open modules via negativo17 akmods,
  kernel + modules signed with our MOK key (GitHub secret MOK_KEY, public cert in keys/), scx_lavd --autopower, sysctl tweaks

- Phase 4: welcome app About/credits, first-boot app status, os-release links, LICENSE (MIT) + CREDITS.md,
  VM test types the password and screenshots the desktop; kernel layer split (Containerfile.kernel, kernel.yml, daily)
- Phase 5: owner wanted a distro WIKI: GitHub Wiki (10 pages, source in docs/wiki/, pages added via browser since the wiki git is not pushable from here). Discussions also set up (free):
  Game Compatibility Reports, Showcase, Feedback and Bugs; forms in .github/DISCUSSION_TEMPLATE;
  rules (#1) and welcome (#2) posted and pinned. Default extra categories still there until owner OKs removing

- "Worth wiping for" features: daily save backups (Ludusavi user timer), self-updating GE-Proton (weekly user timer),
  jet HUD toggle (MangoHud via Steam flatpak override), TV mode (Steam Big Picture), battery care 80% limit,
  Discord + OBS, cockpit sound theme (branding/sounds.py), pixel cursor (branding/cursor.py),
  tuned Firefox (policies: uBlock, start page, no nags) + Shorts launcher. All in build/extras.sh, welcome app has 8 buttons

- Pixel icon theme, set as default
- Radar browser: everyday browser (not entertainment-focused per owner), editable shortcut start page, ad/tracker blocking, game mode freezes background tabs, default for links; `radar --shorts` tall window kept for the Shorts panel button; Firefox stays as backup

- Installer: installer/ (kickstart asks only for the drive, queues the MOK key with password = slug, puts the GRUB theme on /boot via user.cfg, bootc switch to ghcr), product.img for the installer look; iso.yml builds it after each good build and tests a full install under Secure Boot (screens on ci-iso branch, ISO as artifact)
- docs/laptop-test.md: checklist for the real laptop test

# Next
- Status 2026-11-17: system image builds and passes the VM boot/login test (build.yml green). Last desktop shot showed KDE Welcome Center popping up and Dolphin with a Breeze icon; fixed (plasma-welcome removed, icon aliases) in commit after 736b475, not yet seen in screenshots
- ISO: base image lacks fedora.repo/fedora-updates.repo and the Fedora GPG key; build.sh now adds both (repos fixed run 44214966049, key fix pending)
- After the ISO passes iso.yml (screens on ci-iso branch): check installer look, MOK blue screen steps, boot menu theme, first boot; then owner does docs/laptop-test.md
- Dispatch workflows with REST: gh api -X POST repos/herbertjquavius/sidewinder-os/actions/workflows/iso.yml/dispatches -f ref=main (gh workflow run fails, GraphQL blocked)
- Owner must make the GHCR package public so installed laptops can update
- Benchmarks: bench run results on ci-bench branch, write docs/kernel.md
- Later: wiki pages for new features (Radar, HUD, saves, TV mode, battery care), fastfetch logo, image signing (cosign)
- Keep token use low: check CI rarely, no screenshots unless needed

# Decisions
- Own distro, not a Bazzite reskin: base on Fedora Kinoite via Universal Blue's thin kinoite-main (codecs, hardware fixes)
- Builds and tests run in GitHub Actions only (workspace has no KVM or registry access, owner PC is off limits)
- ISO and test disk made with bootc-image-builder
- Steam as Flatpak for now (no extra repos needed); switch to RPM Steam if hybrid GPU switching misbehaves on the laptop
- Fedora 44+ uses Plasma Login Manager (no custom themes), so the image swaps in SDDM to keep our login screen
- First boot runs Fedora's Plasma Setup wizard (makes the user account, shows "Powered by Sidewinder"); keep it, reskinned by replacing Plasma's Next wallpaper (the only one it reads) and system default colors.
  VM test boots twice: once into the wizard (screenshots only), once with a systemd credential drop-in that skips it, to check login
- CI pushes VM screenshots + serial log to the ci-screens branch (artifact downloads are blocked from the workspace)
- Kernel: CachyOS kernel (BORE, sched_ext, CachyOS patches) built for Fedora
- Nobara-style gaming tweaks and packages on top
- We build the NVIDIA driver for our kernel ourselves; needs a one-time Secure Boot key screen at install
- All branding generated by script so renaming is one variable
- Name: Sidewinder (owner's pick: snake + the F-16 wingtip missile). Viper/ViperOS taken; no Sidewinder distro found
- Plymouth script untested until the Phase 1 VM boot
