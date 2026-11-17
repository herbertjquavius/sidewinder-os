#!/usr/bin/env bash
# Daily save backups, self-updating GE-Proton, battery care, the tuned browser, sounds and cursor
set -euo pipefail
SLUG=$1
B=/ctx/branding

# Game save backups with Ludusavi, every day, into Game Save Backups in the home folder
cat > "/usr/lib/systemd/user/$SLUG-save-backup.service" <<'EOF'
[Unit]
Description=Back up game saves

[Service]
Type=oneshot
Nice=19
IOSchedulingClass=idle
ExecCondition=/usr/bin/flatpak info com.github.mtkennerly.ludusavi
ExecStart=/usr/bin/flatpak run com.github.mtkennerly.ludusavi backup --force --path "%h/Game Save Backups"
EOF
cat > "/usr/lib/systemd/user/$SLUG-save-backup.timer" <<'EOF'
[Unit]
Description=Back up game saves every day

[Timer]
OnBootSec=20min
OnCalendar=daily
RandomizedDelaySec=30min
Persistent=true

[Install]
WantedBy=timers.target
EOF

# GE-Proton: newest version into Steam every week, keeps the two newest
cat > "/usr/libexec/$SLUG-ge-proton" <<'EOF'
#!/usr/bin/env bash
# Downloads the newest GE-Proton for Steam if it isn't there yet
set -euo pipefail
dir="$HOME/.var/app/com.valvesoftware.Steam/data/Steam/compatibilitytools.d"
mkdir -p "$dir"
url=$(curl -fsSL https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/latest \
    | python3 -c 'import json,sys; print([a["browser_download_url"] for a in json.load(sys.stdin)["assets"] if a["name"].endswith(".tar.gz")][0])')
name=$(basename "$url" .tar.gz)
[ -d "$dir/$name" ] && exit 0
curl -fsSL "$url" | tar -xz -C "$dir"
ls -1d "$dir"/GE-Proton* | sort -V | head -n -2 | xargs -r rm -rf
EOF
chmod 0755 "/usr/libexec/$SLUG-ge-proton"
cat > "/usr/lib/systemd/user/$SLUG-ge-proton.service" <<EOF
[Unit]
Description=Keep GE-Proton up to date
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
Nice=19
ExecCondition=/usr/bin/flatpak info com.valvesoftware.Steam
ExecStart=/usr/libexec/$SLUG-ge-proton
EOF
cat > "/usr/lib/systemd/user/$SLUG-ge-proton.timer" <<'EOF'
[Unit]
Description=Check for a new GE-Proton every week

[Timer]
OnBootSec=10min
OnCalendar=weekly
RandomizedDelaySec=1h
Persistent=true

[Install]
WantedBy=timers.target
EOF
systemctl --global enable "$SLUG-save-backup.timer" "$SLUG-ge-proton.timer"

# Battery care: stop charging at 80% when turned on in the welcome app, if the laptop supports it
cat > "/usr/libexec/$SLUG-battery" <<EOF
#!/usr/bin/env bash
# Applies the saved battery limit, 80 when on, 100 when off
limit=100
[ "\$(cat /etc/$SLUG/battery-limit 2>/dev/null)" = "on" ] && limit=80
for f in /sys/class/power_supply/BAT*/charge_control_end_threshold; do
    [ -w "\$f" ] && echo "\$limit" > "\$f"
done
exit 0
EOF
chmod 0755 "/usr/libexec/$SLUG-battery"
cat > "/usr/lib/systemd/system/$SLUG-battery.service" <<EOF
[Unit]
Description=Apply the battery charge limit

[Service]
Type=oneshot
ExecStart=/usr/libexec/$SLUG-battery

[Install]
WantedBy=multi-user.target
EOF
systemctl enable "$SLUG-battery.service"

# Browser: Firefox with no YouTube ads, our start page, no nags
mkdir -p /etc/firefox/policies "/usr/share/$SLUG/startpage"
cp -r "$B/startpage/." "/usr/share/$SLUG/startpage/"
cat > /etc/firefox/policies/policies.json <<EOF
{
  "policies": {
    "DisableTelemetry": true,
    "DisablePocket": true,
    "DontCheckDefaultBrowser": true,
    "OverrideFirstRunPage": "",
    "OverridePostUpdatePage": "",
    "Homepage": {
      "URL": "file:///usr/share/$SLUG/startpage/index.html",
      "StartPage": "homepage",
      "Locked": false
    },
    "FirefoxHome": {
      "SponsoredTopSites": false,
      "SponsoredPocket": false,
      "Pocket": false,
      "Locked": false
    },
    "UserMessaging": {
      "WhatsNew": false,
      "ExtensionRecommendations": false,
      "FeatureRecommendations": false,
      "MoreFromMozilla": false,
      "SkipOnboarding": true
    },
    "ExtensionSettings": {
      "uBlock0@raymondhill.net": {
        "installation_mode": "normal_installed",
        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
      }
    },
    "Preferences": {
      "media.ffmpeg.vaapi.enabled": { "Value": true, "Status": "default" },
      "browser.newtabpage.activity-stream.showSponsored": { "Value": false, "Status": "default" },
      "browser.newtabpage.activity-stream.showSponsoredTopSites": { "Value": false, "Status": "default" }
    }
  }
}
EOF

# Shorts button: opens YouTube Shorts in a new window
for s in 48 96 192; do
    install -Dm644 "$B/icons/${s}x${s}/$SLUG-shorts.png" "/usr/share/icons/hicolor/${s}x${s}/apps/$SLUG-shorts.png"
done
cat > "/usr/share/applications/$SLUG-shorts.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Shorts
Comment=YouTube Shorts in Firefox
Exec=firefox --new-window https://www.youtube.com/shorts
Icon=$SLUG-shorts
Categories=Network;AudioVideo;
EOF

# Cockpit sounds and pixel cursor as the defaults
cp -r "$B/sounds/$SLUG" /usr/share/sounds/
cp -a "$B/cursors/$SLUG-cursors" /usr/share/icons/
printf '\n[Sounds]\nTheme=%s\n' "$SLUG" >> /etc/xdg/kdeglobals
printf '\n[Mouse]\ncursorTheme=%s-cursors\n' "$SLUG" >> /etc/xdg/kcminputrc
