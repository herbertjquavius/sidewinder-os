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
    -e "/^(LOGO|DEFAULT_HOSTNAME|VARIANT|VARIANT_ID|HOME_URL|SUPPORT_URL|BUG_REPORT_URL|DOCUMENTATION_URL)=/d" \
    /usr/lib/os-release
cat >> /usr/lib/os-release <<EOF
LOGO=$SLUG
DEFAULT_HOSTNAME="$SLUG"
VARIANT="Gaming"
VARIANT_ID=$SLUG
HOME_URL="$HOME_URL"
SUPPORT_URL="$FORUM_URL"
BUG_REPORT_URL="$BUG_URL"
EOF

# Logo icons
for s in 48 96 192; do
    install -Dm644 "$B/logo-$s.png" "/usr/share/icons/hicolor/${s}x${s}/apps/$SLUG.png"
done
install -Dm644 "$B/logo.svg" "/usr/share/icons/hicolor/scalable/apps/$SLUG.svg"

# Pixel font
install -Dm644 "$B/fonts/$SLUG-pixel.ttf" "/usr/share/fonts/$SLUG/$SLUG-pixel.ttf"

# Wallpaper, colors and desktop look
cp -r "$B/wallpapers/"* /usr/share/wallpapers/
install -Dm644 "$B/color-schemes/$CS.colors" "/usr/share/color-schemes/$CS.colors"
cp -r "$B/plasma/look-and-feel/org.$SLUG.desktop" /usr/share/plasma/look-and-feel/

# Our look is the default for every new user
grep -rl '^LookAndFeelPackage=' /etc/xdg /usr/share/kde-settings 2>/dev/null \
    | xargs -r sed -i "s|^LookAndFeelPackage=.*|LookAndFeelPackage=org.$SLUG.desktop|"
if ! grep -qs '^LookAndFeelPackage=' /etc/xdg/kdeglobals; then
    printf '\n[KDE]\nLookAndFeelPackage=org.%s.desktop\n' "$SLUG" >> /etc/xdg/kdeglobals
fi

# Lock screen uses our wallpaper
cat >> /etc/xdg/kscreenlockerrc <<EOF

[Greeter][Wallpaper][org.kde.image][General]
Image=file:///usr/share/wallpapers/$SLUG/
EOF

# Green HUD terminal as the default Konsole profile
install -Dm644 "$B/konsole/$SLUG.colorscheme" "/usr/share/konsole/$SLUG.colorscheme"
install -Dm644 "$B/konsole/$SLUG.profile" "/usr/share/konsole/$SLUG.profile"
printf '\n[Desktop Entry]\nDefaultProfile=%s.profile\n' "$SLUG" >> /etc/xdg/konsolerc

# Our colors as the system default, used by the first-boot wizard and every new user
cat "$B/color-schemes/$CS.colors" >> /etc/xdg/kdeglobals
printf '\n[General]\nAccentColor=92,255,122\n' >> /etc/xdg/kdeglobals

# Login screen
# Fedora 44+ ships Plasma Login Manager, which can't use custom themes, so swap in SDDM
dnf -y install sddm sddm-wayland-plasma
systemctl disable plasmalogin.service 2>/dev/null || true
systemctl enable --force sddm.service
cp -r "$B/sddm/$SLUG" /usr/share/sddm/themes/
mkdir -p /etc/sddm.conf.d
printf '[Theme]\nCurrent=%s\n' "$SLUG" > "/etc/sddm.conf.d/50-$SLUG-theme.conf"
if [ -f /etc/sddm.conf ]; then
    sed -i -E "s|^Current=.*|Current=$SLUG|" /etc/sddm.conf
fi

# Boot menu theme, the installer copies it to the boot partition
mkdir -p "/usr/share/$SLUG"
cp -r "$B/grub/$SLUG" "/usr/share/$SLUG/grub-theme"
# Installer art, copied into the install USB by installer/make-iso.sh
cp -r "$B/installer" "/usr/share/$SLUG/installer"
# Lets the installer queue our Secure Boot key
dnf -y install mokutil

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
sed "s/SLUGDIR/$SLUG/g" /ctx/welcome/helper.sh > "/usr/libexec/$SLUG-welcome-helper"
chmod 0755 "/usr/libexec/$SLUG-welcome-helper"
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

# KDE's own Welcome Center would pop up on top of ours, so it stays off
rm -f /etc/xdg/autostart/org.kde.plasma-welcome.desktop /usr/share/autostart/org.kde.plasma-welcome.desktop
# Plasma still opens it on first login, so take it out
rpm -qa "plasma-welcome*" | xargs -r rpm -e --nodeps

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

# Gaming apps and defaults
/ctx/build/gaming.sh "$SLUG"
/ctx/build/extras.sh "$SLUG"

# Fastfetch shows our logo and name instead of Fedora's
dnf -y install fastfetch
mkdir -p /etc/xdg/fastfetch /usr/share/$SLUG
cat > /usr/share/$SLUG/fastfetch-logo.txt <<'LOGO'
$1        __
$1        \ \_____
$1     ###[==_____>
$1        /_/      $2S I D E W I N D E R
LOGO
cat > /etc/xdg/fastfetch/config.jsonc <<CFG
{
  "logo": { "source": "/usr/share/$SLUG/fastfetch-logo.txt", "type": "file", "color": { "1": "green", "2": "yellow" } },
  "display": { "color": "green" },
  "modules": ["title", "separator", "os", "kernel", "uptime", "cpu", "gpu", "memory", "disk", "battery"]
}
CFG

# Base image has no Fedora repo files, the ISO builder needs them
for name in fedora fedora-updates; do
    [ -f "/etc/yum.repos.d/$name.repo" ] && continue
    meta=fedora-\$releasever; [ "$name" = fedora-updates ] && meta=updates-released-f\$releasever
    cat > "/etc/yum.repos.d/$name.repo" <<EOF
[$name]
name=Fedora \$releasever - \$basearch ($name)
metalink=https://mirrors.fedoraproject.org/metalink?repo=$meta&arch=\$basearch
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-\$basearch
EOF
done

# Fedora signing key for those repos, also missing from the base image
ver=$(. /etc/os-release && echo "$VERSION_ID")
key=/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$ver-$(uname -m)
if [ ! -f "$key" ]; then
    mkdir -p /etc/pki/rpm-gpg
    found=$(find /usr/share/distribution-gpg-keys /etc/pki/rpm-gpg -name "RPM-GPG-KEY-fedora-$ver-primary" 2>/dev/null | head -1)
    if [ -n "$found" ]; then cp "$found" "$key"
    else curl -fsSL -o "$key" "https://src.fedoraproject.org/rpms/fedora-repos/raw/rawhide/f/RPM-GPG-KEY-fedora-$ver-primary"
    fi
fi

# First-boot wizard shows Plasma's Next wallpaper, so Next becomes ours
# Done last so no package install puts the stock one back
for d in images images_dark; do
    dir="/usr/share/wallpapers/Next/contents/$d"
    [ -L "$dir" ] && rm -f "$dir"
    mkdir -p "$dir"
    rm -f "$dir/"*
    cp "$B/setup/"*.png "$dir/"
done
# Fedora's build of the wizard reads wallpapers/Default (a link to Fedora's own) as .jxl, so Default becomes ours too
rm -rf /usr/share/wallpapers/Default
cp -r "/usr/share/wallpapers/$SLUG" /usr/share/wallpapers/Default
for d in images images_dark; do
    mkdir -p "/usr/share/wallpapers/Default/contents/$d"
    cp "$B/setup/"*.png "$B/setup/"*.jxl "/usr/share/wallpapers/Default/contents/$d/"
done
cmp "$B/setup/5120x2880.jxl" /usr/share/wallpapers/Default/contents/images/5120x2880.jxl

# Clean up
dnf clean all
rm -rf /var/cache/* /var/log/* /tmp/*
