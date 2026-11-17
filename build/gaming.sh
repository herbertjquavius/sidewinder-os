#!/usr/bin/env bash
# Gaming apps, controller access, power profiles and quiet auto-updates
set -euo pipefail
SLUG=$1

# Game helpers on the system itself
dnf -y install gamemode mangohud

# Steam Input and controllers over USB or Bluetooth
cat > "/usr/lib/udev/rules.d/70-$SLUG-controllers.rules" <<'EOF'
# Virtual controller device Steam Input needs
KERNEL=="uinput", SUBSYSTEM=="misc", TAG+="uaccess", OPTIONS+="static_node=uinput"
# Valve, Sony, Nintendo, Microsoft and 8BitDo controllers
KERNEL=="hidraw*", ATTRS{idVendor}=="28de", MODE="0660", TAG+="uaccess"
KERNEL=="hidraw*", ATTRS{idVendor}=="054c", MODE="0660", TAG+="uaccess"
KERNEL=="hidraw*", ATTRS{idVendor}=="057e", MODE="0660", TAG+="uaccess"
KERNEL=="hidraw*", ATTRS{idVendor}=="045e", MODE="0660", TAG+="uaccess"
KERNEL=="hidraw*", ATTRS{idVendor}=="2dc8", MODE="0660", TAG+="uaccess"
KERNEL=="hidraw*", KERNELS=="*28DE:*", MODE="0660", TAG+="uaccess"
KERNEL=="hidraw*", KERNELS=="*054C:*", MODE="0660", TAG+="uaccess"
KERNEL=="hidraw*", KERNELS=="*057E:*", MODE="0660", TAG+="uaccess"
KERNEL=="hidraw*", KERNELS=="*045E:*", MODE="0660", TAG+="uaccess"
KERNEL=="hidraw*", KERNELS=="*2DC8:*", MODE="0660", TAG+="uaccess"
EOF

# Gaming apps from Flathub, installed once after the first boot with internet
cat > "/usr/libexec/$SLUG-flatpaks" <<EOF
#!/usr/bin/env bash
# Installs the gaming apps, retried until it works
set -euo pipefail
flatpak remote-add --if-not-exists --system flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak remote-modify --system --no-filter --enable flathub || true
flatpak install --system -y --noninteractive flathub \\
    com.valvesoftware.Steam com.heroicgameslauncher.hgl net.lutris.Lutris net.davidotek.pupgui2 \\
    com.discordapp.Discord com.obsproject.Studio com.github.mtkennerly.ludusavi
# MangoHud for Steam games, matched to Steam's runtime version
branch=\$(flatpak info --system --show-runtime com.valvesoftware.Steam | cut -d/ -f3)
flatpak install --system -y --noninteractive flathub "org.freedesktop.Platform.VulkanLayer.MangoHud//\$branch" || true
# Hybrid graphics laptops: Steam and its games run on the NVIDIA card
if lspci | grep -qi nvidia && [ "\$(lspci | grep -ciE 'vga|3d controller')" -gt 1 ]; then
    flatpak override --system --env=__NV_PRIME_RENDER_OFFLOAD=1 --env=__GLX_VENDOR_LIBRARY_NAME=nvidia \\
        --env=__VK_LAYER_NV_optimus=NVIDIA_only com.valvesoftware.Steam
fi
mkdir -p /var/lib/$SLUG
touch /var/lib/$SLUG/flatpaks-done
EOF
chmod 0755 "/usr/libexec/$SLUG-flatpaks"

cat > "/usr/lib/systemd/system/$SLUG-flatpaks.service" <<EOF
[Unit]
Description=Install gaming apps
Wants=network-online.target
After=network-online.target
ConditionPathExists=!/var/lib/$SLUG/flatpaks-done

[Service]
Type=oneshot
ExecStart=/usr/libexec/$SLUG-flatpaks
Restart=on-failure
RestartSec=120

[Install]
WantedBy=multi-user.target
EOF

# Steam starts quietly in the tray at login
mkdir -p /etc/xdg/autostart
cat > /etc/xdg/autostart/steam-silent.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Steam
Exec=sh -c "flatpak info com.valvesoftware.Steam >/dev/null 2>&1 && flatpak run com.valvesoftware.Steam -silent"
Icon=com.valvesoftware.Steam
X-GNOME-Autostart-enabled=true
EOF

# Full power on the charger, battery saver when unplugged
cat > "/usr/libexec/$SLUG-power" <<'EOF'
#!/usr/bin/env bash
# Picks the power profile from the charger state
ls /sys/class/power_supply/BAT* >/dev/null 2>&1 || exit 0
online=0
for s in /sys/class/power_supply/*; do
    case "$(cat "$s/type" 2>/dev/null)" in
        Mains|USB) [ "$(cat "$s/online" 2>/dev/null)" = "1" ] && online=1 ;;
    esac
done
if [ "$online" = 1 ]; then
    powerprofilesctl set performance
else
    powerprofilesctl set power-saver
fi
EOF
chmod 0755 "/usr/libexec/$SLUG-power"

cat > "/usr/lib/udev/rules.d/71-$SLUG-power.rules" <<EOF
# Charger plugged in or pulled out
SUBSYSTEM=="power_supply", ACTION=="change", RUN+="/usr/libexec/$SLUG-power"
EOF

cat > "/usr/lib/systemd/system/$SLUG-power.service" <<EOF
[Unit]
Description=Set power profile from charger state
After=power-profiles-daemon.service tuned-ppd.service

[Service]
Type=oneshot
ExecStart=/usr/libexec/$SLUG-power

[Install]
WantedBy=multi-user.target
EOF

# Updates download in the background, used on the next restart, never forced
cat > "/usr/lib/systemd/system/$SLUG-update.service" <<'EOF'
[Unit]
Description=Download system and app updates
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
Nice=19
IOSchedulingClass=idle
ExecStart=/usr/bin/bootc upgrade --quiet
ExecStart=/usr/bin/flatpak update --system -y --noninteractive
EOF

cat > "/usr/lib/systemd/system/$SLUG-update.timer" <<'EOF'
[Unit]
Description=Check for updates twice a day

[Timer]
OnBootSec=15min
OnUnitInactiveSec=12h
RandomizedDelaySec=30min
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Turn off other updaters so only ours runs, then enable ours
for t in bootc-fetch-apply-updates.timer rpm-ostreed-automatic.timer uupd.timer; do
    systemctl disable "$t" 2>/dev/null || true
done
systemctl enable "$SLUG-flatpaks.service" "$SLUG-power.service" "$SLUG-update.timer"
