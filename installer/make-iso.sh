#!/usr/bin/env bash
# Builds the install ISO with our kickstart and installer look; TEST=1 also makes a copy that installs by itself
set -euo pipefail
IMAGE=$1
BIB=$2
cd "$(dirname "$0")/.."
. ./distro.env
SLUG=$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
W=output/installer
rm -rf "$W" output/bootiso
mkdir -p "$W" output

# Kickstart goes into the builder config, the Users step is off because first boot makes the account
{
    echo "[customizations.installer.kickstart]"
    echo "contents = '''"
    sed "s|@SLUG@|$SLUG|g; s|@IMAGE@|$IMAGE|g; s|@NAME@|$NAME|g" installer/kickstart.ks
    echo "'''"
    echo
    echo "[customizations.installer.modules]"
    echo 'disable = ["org.fedoraproject.Anaconda.Modules.Users"]'
} > "$W/config.toml"

# Package sources the builder will use for the installer, shown in the log
podman run --rm "$IMAGE" sh -c 'grep -E "^(ID|VERSION_ID)=" /etc/os-release; for f in /etc/yum.repos.d/*.repo; do echo "$f: $(grep -c "^enabled=1" "$f") enabled"; done'

podman run --rm --privileged --pull=newer \
    --security-opt label=type:unconfined_t \
    -v ./output:/output \
    -v "./$W/config.toml:/config.toml:ro" \
    -v /var/lib/containers/storage:/var/lib/containers/storage \
    "$BIB" --type anaconda-iso --rootfs btrfs --log-level debug "$IMAGE"
ISO=output/bootiso/install.iso

# Installer look: name, pictures and colors, packed as product.img which the installer loads from the USB
P="$W/product"
mkdir -p "$P/pixmaps" "$P/usr/share/anaconda/pixmaps" "$P/run/install/product" "$P/etc/anaconda/conf.d"
CID=$(podman create "$IMAGE" true)
podman cp "$CID:/usr/share/$SLUG/installer/." "$P/pixmaps/"
podman rm "$CID" >/dev/null
cp "$P/pixmaps/"*.png "$P/usr/share/anaconda/pixmaps/"
cp -r "$P/pixmaps" "$P/run/install/product/"
sed "s|@PIX@|/usr/share/anaconda/pixmaps|g" installer/anaconda-gtk.css > "$P/usr/share/anaconda/pixmaps/$SLUG.css"
sed "s|@PIX@|/run/install/product/pixmaps|g" installer/anaconda-gtk.css > "$P/anaconda-gtk.css"
cp "$P/anaconda-gtk.css" "$P/run/install/product/anaconda-gtk.css"
printf '[User Interface]\ncustom_stylesheet = /usr/share/anaconda/pixmaps/%s.css\n' "$SLUG" > "$P/etc/anaconda/conf.d/99-$SLUG.conf"
xorriso -osirrox on -indev "$ISO" -extract /.treeinfo "$W/treeinfo" 2>/dev/null || true
VER=$(sed -n 's/^version *= *//p' "$W/treeinfo" 2>/dev/null | head -1) || true
printf '[Main]\nProduct=%s\nVersion=%s\nBugURL=%s\nIsFinal=True\nUUID=%s.x86_64\nVariant=\n' \
    "$NAME" "${VER:-1}" "$BUG_URL" "$(date +%Y%m%d%H%M)" > "$P/.buildstamp"
(cd "$P" && find . | cpio --quiet -o -H newc | gzip -9) > "$W/product.img"

OUT="output/bootiso/$SLUG.iso"
xorriso -indev "$ISO" -outdev "$OUT" -map "$W/product.img" /images/product.img -boot_image any replay
command -v implantisomd5 >/dev/null && implantisomd5 --force "$OUT" >/dev/null || true

# Test copy: same ISO, but the kickstart also erases the VM disk without asking
if [ "${TEST:-0}" = 1 ]; then
    for f in $(xorriso -indev "$OUT" -ls '/*.ks' 2>/dev/null | tr -d "'"); do
        xorriso -osirrox on -indev "$OUT" -extract "$f" "$W/ks" 2>/dev/null
        grep -q "$NAME installer" "$W/ks" && KS=$f && break
    done
    echo "Kickstart on the ISO: ${KS:?not found}"
    cat installer/test.ks >> "$W/ks"
    xorriso -indev "$OUT" -outdev output/bootiso/test.iso -map "$W/ks" "$KS" -boot_image any replay
fi
rm -f "$ISO"
chmod -R a+r output/bootiso
ls -la output/bootiso
