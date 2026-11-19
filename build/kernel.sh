#!/usr/bin/env bash
# CachyOS kernel, NVIDIA driver built for it, Secure Boot signing, LAVD scheduler, gaming tweaks
set -euo pipefail
source /ctx/distro.env
SLUG=$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
FEDORA=$(rpm -E %fedora)
KEY=/run/secrets/mok_key
CERT=/ctx/keys/sidewinder-mok.pem

# Repos: CachyOS kernel and add-ons, negativo17 NVIDIA driver
for r in kernel-cachyos kernel-cachyos-addons; do
    curl -fsSL -o "/etc/yum.repos.d/$r.repo" \
        "https://copr.fedorainfracloud.org/coprs/bieszczaders/$r/repo/fedora-$FEDORA/bieszczaders-$r-fedora-$FEDORA.repo"
done
curl -fsSL -o /etc/yum.repos.d/fedora-nvidia.repo https://negativo17.org/repos/fedora-nvidia.repo

# Keep kernel install hooks quiet inside the container, the initramfs gets built at the end
hooks=/usr/lib/kernel/install.d
for h in 05-rpmostree.install 50-dracut.install; do
    if [ -f "$hooks/$h" ]; then
        mv "$hooks/$h" "$hooks/$h.off"
        printf '#!/bin/sh\nexit 0\n' > "$hooks/$h"
        chmod +x "$hooks/$h"
    fi
done

# Swap Fedora's kernel for CachyOS's
old=$(rpm -qa --qf '%{NAME}\n' | grep -E '^kernel(-core|-modules|-modules-core|-modules-extra|-devel|-devel-matched|-uki-virt)?$' || true)
[ -n "$old" ] && rpm -e --nodeps $old
rm -rf /usr/lib/modules/*
dnf -y install kernel-cachyos kernel-cachyos-devel-matched
KVER=$(ls /usr/lib/modules | sort -V | tail -n1)
echo "Kernel: $KVER"

# Signing key for kernel modules, only when the build was given the private key
if [ -s "$KEY" ]; then
    mkdir -p /etc/pki/akmods/certs /etc/pki/akmods/private
    openssl x509 -in "$CERT" -outform DER -out /etc/pki/akmods/certs/public_key.der
    install -m600 "$KEY" /etc/pki/akmods/private/private_key.priv
fi

# NVIDIA open kernel modules (right for RTX 20 series and newer), built for this kernel
# The akmod's own install script won't build as root, so install it with scripts off first,
# then the driver (which pulls it in) finds it already there, and the module gets built as a plain user
dnf -y install --setopt=tsflags=noscripts akmod-nvidia
dnf -y install nvidia-driver nvidia-settings nvidia-modprobe
# Newer drivers build the open modules by default, older ones read this setting
if [ -f /etc/nvidia/kernel.conf ]; then
    sed -i 's/^MODULE_VARIANT=.*/MODULE_VARIANT=kernel-open/' /etc/nvidia/kernel.conf
fi
id kmodbuild >/dev/null 2>&1 || useradd -r -M -s /sbin/nologin kmodbuild
[ -d /etc/pki/akmods/private ] && chown -R kmodbuild /etc/pki/akmods/private
out=$(mktemp -d)
chown kmodbuild "$out"
runuser -u kmodbuild -- env HOME="$out" akmodsbuild --target x86_64 --kernels "$KVER" --outputdir "$out" \
    /usr/src/akmods/nvidia-kmod.latest
dnf -y install "$out"/kmod-nvidia-*.rpm
rm -rf "$out"
ls /usr/lib/modules/"$KVER"/extra/nvidia/nvidia.ko* >/dev/null
modinfo -k "$KVER" nvidia | grep -iE '^(version|signer)' || true
# Secure Boot would refuse the driver if it isn't signed with our key, so stop the build instead
if [ -s "$KEY" ]; then
    want=$(openssl x509 -in "$CERT" -noout -subject -nameopt multiline | sed -n 's/^ *commonName *= *//p')
    for m in nvidia nvidia-drm nvidia-modeset nvidia-uvm; do
        got=$(modinfo -k "$KVER" -F signer "$m")
        [ "$got" = "$want" ] || { echo "$m signed by '$got', want '$want'"; exit 1; }
    done
fi
systemctl enable nvidia-suspend.service nvidia-resume.service nvidia-hibernate.service 2>/dev/null || true
mkdir -p /usr/lib/bootc/kargs.d
printf 'kargs = ["rd.driver.blacklist=nouveau", "modprobe.blacklist=nouveau", "nvidia-drm.modeset=1", "nvidia-drm.fbdev=1"]\n' \
    > "/usr/lib/bootc/kargs.d/20-$SLUG-nvidia.toml"

# Sign the kernel itself so Secure Boot accepts it once our key is enrolled
if [ -s "$KEY" ]; then
    dnf -y install sbsigntools
    sbsign --key "$KEY" --cert "$CERT" --output /tmp/vmlinuz "/usr/lib/modules/$KVER/vmlinuz"
    mv /tmp/vmlinuz "/usr/lib/modules/$KVER/vmlinuz"
    rm -rf /etc/pki/akmods/private
else
    echo "No signing key given, kernel and modules are unsigned (fine with Secure Boot off)" >&2
fi

# Public key ships in the image so the installer can enroll it
install -Dm644 "$CERT" "/usr/share/$SLUG/mok/$SLUG-mok.pem"
openssl x509 -in "$CERT" -outform DER -out "/usr/share/$SLUG/mok/$SLUG-mok.der"

# SELinux has to allow loading the kernel's modules
semanage boolean -m --on domain_kernel_load_modules 2>/dev/null || setsebool -P domain_kernel_load_modules on 2>/dev/null \
    || echo "Could not set domain_kernel_load_modules" >&2

# LAVD scheduler, it favors whatever needs quick answers, like the game, and follows the power profile
dnf -y install scx-scheds
mkdir -p /etc/default
printf 'SCX_SCHEDULER=scx_lavd\nSCX_FLAGS="--autopower"\n' > /etc/default/scx
printf 'default_sched = "scx_lavd"\ndefault_mode = "Auto"\n' > /etc/scx_loader.toml
systemctl enable scx_loader.service 2>/dev/null || systemctl enable scx.service

# Small gaming tweaks
cat > "/usr/lib/sysctl.d/60-$SLUG-gaming.conf" <<'EOF'
# No slowdown for games that trip split lock detection
kernel.split_lock_mitigate = 0
# Room for big games that map lots of memory, same as SteamOS
vm.max_map_count = 2147483642
EOF

# Put the kernel install hooks back
for h in 05-rpmostree.install 50-dracut.install; do
    [ -f "$hooks/$h.off" ] && mv -f "$hooks/$h.off" "$hooks/$h"
done
