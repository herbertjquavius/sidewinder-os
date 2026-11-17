# @NAME@ installer. Everything is answered here except which drive to erase
lang en_US.UTF-8
keyboard us
timezone America/New_York --utc
reboot

%post --erroronfail
# Updates come from the published image, not the USB stick
bootc switch --mutate-in-place --transport registry @IMAGE@
%end

%post
SLUG=@SLUG@
CERT=/usr/share/$SLUG/mok/$SLUG-mok.der

# Secure Boot: queue our key, the blue screen after the first restart asks to enroll it
if [ -d /sys/firmware/efi ] && [ -f "$CERT" ] && command -v mokutil >/dev/null; then
    mountpoint -q /sys/firmware/efi/efivars || mount -t efivarfs efivarfs /sys/firmware/efi/efivars || true
    mokutil --generate-hash="$SLUG" > /tmp/mok-hash
    mokutil --timeout -1 || true
    mokutil --import "$CERT" --hash-file /tmp/mok-hash && echo "Secure Boot key queued" || echo "Secure Boot key not queued"
    rm -f /tmp/mok-hash
fi

# Boot menu theme on the boot partition, loaded through user.cfg
for B in /boot /sysroot/boot; do
    [ -d "$B/grub2" ] || continue
    mkdir -p "$B/grub2/themes"
    rm -rf "$B/grub2/themes/$SLUG"
    cp -r "/usr/share/$SLUG/grub-theme" "$B/grub2/themes/$SLUG"
    cat >> "$B/grub2/user.cfg" <<EOF
# $SLUG boot menu look
if loadfont \$prefix/themes/$SLUG/pixel-24.pf2; then
  insmod all_video
  insmod gfxterm
  insmod png
  set gfxmode=auto
  terminal_output gfxterm
  set theme=\$prefix/themes/$SLUG/theme.txt
  export theme
fi
EOF
    echo "Boot menu theme installed in $B"
    break
done
%end
