#!/usr/bin/env bash
# Puts our branding and settings into the system image
set -euo pipefail

source /ctx/distro.env
SLUG=$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
CS=$(echo "$NAME" | sed -E 's/[^A-Za-z0-9_]//g')
B=/ctx/branding

# Script plugin for our boot splash
dnf -y install plymouth-plugin-script

# Name and logo in os-release
sed -i -E \
    -e "s|^NAME=.*|NAME=\"$NAME\"|" \
    -e "s|^PRETTY_NAME=.*|PRETTY_NAME=\"$NAME\"|" \
    -e "/^(LOGO|DEFAULT_HOSTNAME|VARIANT|VARIANT_ID)=/d" \
    /usr/lib/os-release
cat >> /usr/lib/os-release <<EOF
LOGO=$SLUG
DEFAULT_HOSTNAME="$SLUG"
VARIANT="Gaming"
VARIANT_ID=$SLUG
EOF

# Logo icons
for s in 48 96 192; do
    install -Dm644 "$B/logo-$s.png" "/usr/share/icons/hicolor/${s}x${s}/apps/$SLUG.png"
done
install -Dm644 "$B/logo.svg" "/usr/share/icons/hicolor/scalable/apps/$SLUG.svg"

# Pixel font
install -Dm644 "$B/fonts/$SLUG-pixel.ttf" "/usr/share/fonts/$SLUG/$SLUG-pixel.ttf"

# Wallpaper, colors and desktop look
cp -r "$B/wallpapers/$SLUG" /usr/share/wallpapers/
install -Dm644 "$B/color-schemes/$CS.colors" "/usr/share/color-schemes/$CS.colors"
cp -r "$B/plasma/look-and-feel/org.$SLUG.desktop" /usr/share/plasma/look-and-feel/

# Our look is the default for every new user
grep -rl '^LookAndFeelPackage=' /etc/xdg /usr/share/kde-settings 2>/dev/null \
    | xargs -r sed -i "s|^LookAndFeelPackage=.*|LookAndFeelPackage=org.$SLUG.desktop|"
if ! grep -qs '^LookAndFeelPackage=' /etc/xdg/kdeglobals; then
    printf '\n[KDE]\nLookAndFeelPackage=org.%s.desktop\n' "$SLUG" >> /etc/xdg/kdeglobals
fi

# Login screen
if [ -d /usr/share/sddm/themes ]; then
    cp -r "$B/sddm/$SLUG" /usr/share/sddm/themes/
    mkdir -p /etc/sddm.conf.d
    printf '[Theme]\nCurrent=%s\n' "$SLUG" > "/etc/sddm.conf.d/50-$SLUG-theme.conf"
    if [ -f /etc/sddm.conf ]; then
        sed -i -E "s|^Current=.*|Current=$SLUG|" /etc/sddm.conf
    fi
else
    echo "No SDDM found, login screen theme skipped" >&2
fi

# Boot menu theme, kept ready until it is wired into the bootloader
mkdir -p "/usr/share/$SLUG"
cp -r "$B/grub/$SLUG" "/usr/share/$SLUG/grub-theme"

# Boot splash
cp -r "$B/plymouth/$SLUG" /usr/share/plymouth/themes/
mkdir -p /etc/plymouth
printf '[Daemon]\nTheme=%s\n' "$SLUG" > /etc/plymouth/plymouthd.conf
mkdir -p /usr/lib/bootc/kargs.d
printf 'kargs = ["rhgb", "quiet", "splash"]\n' > "/usr/lib/bootc/kargs.d/10-$SLUG-splash.toml"

# Rebuild the initramfs so the splash is in it
KVER=$(ls /usr/lib/modules | sort -V | tail -n1)
dracut --no-hostonly --kver "$KVER" --reproducible --zstd --add ostree -f "/usr/lib/modules/$KVER/initramfs.img"
chmod 0600 "/usr/lib/modules/$KVER/initramfs.img"

# Welcome app
dnf -y install python3-pyside6
install -Dm644 /ctx/distro.env "/usr/share/$SLUG/distro.env"
install -Dm644 /ctx/welcome/welcome.py "/usr/share/$SLUG/welcome/welcome.py"
install -Dm755 /ctx/welcome/helper.sh "/usr/libexec/$SLUG-welcome-helper"
cat > "/usr/share/polkit-1/actions/org.$SLUG.welcome.policy" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <action id="org.$SLUG.welcome.helper">
    <description>Update or repair the system</description>
    <message>Type your password to update or repair the system</message>
    <defaults>
      <allow_any>no</allow_any>
      <allow_inactive>no</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/libexec/$SLUG-welcome-helper</annotate>
  </action>
</policyconfig>
EOF

# Menu entry, plus one autostart that only shows on first login
desktop() {
    cat > "$1" <<EOF
[Desktop Entry]
Type=Application
Name=$NAME Welcome
Comment=Update, fix problems and game mode
Exec=python3 /usr/share/$SLUG/welcome/welcome.py $2
Icon=$SLUG
Categories=System;Settings;
EOF
}
desktop "/usr/share/applications/$SLUG-welcome.desktop" ""
mkdir -p /etc/xdg/autostart
desktop "/etc/xdg/autostart/$SLUG-welcome.desktop" "--first-run"

# Clean up
dnf clean all
rm -rf /var/cache/* /var/log/* /tmp/*
