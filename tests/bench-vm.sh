#!/usr/bin/env bash
# Boots a disk once with the benchmark injected as systemd credentials, saves the serial log
# Usage: bench-vm.sh DISK OUT.log [no-scx]
set -euo pipefail
DISK=$1
LOG=$2
HERE=$(dirname "$0")

b64() { printf '%s' "$1" | base64 -w0; }
skip='[Unit]
ConditionPathExists=/skip-for-benchmark
'
unit='[Unit]
Description=Benchmark
After=multi-user.target
[Service]
Type=oneshot
ImportCredential=sw.bench
ExecStart=/bin/sh %d/sw.bench
'
creds=(
    "io.systemd.credential.binary:sw.bench=$(base64 -w0 "$HERE/bench.sh")"
    "io.systemd.credential.binary:systemd.extra-unit.sw-bench.service=$(b64 "$unit")"
    "io.systemd.credential.binary:systemd.unit-dropin.multi-user.target=$(b64 $'[Unit]\nWants=sw-bench.service\n')"
)
# Keep the desktop, first-boot wizard and app downloads out of the numbers
for u in plasma-setup.service sddm.service sidewinder-flatpaks.service; do
    creds+=("io.systemd.credential.binary:systemd.unit-dropin.$u=$(b64 "$skip")")
done
if [ "${3:-}" = "no-scx" ]; then
    for u in scx_loader.service scx.service; do
        creds+=("io.systemd.credential.binary:systemd.unit-dropin.$u=$(b64 "$skip")")
    done
fi
smbios=()
for c in "${creds[@]}"; do
    smbios+=(-smbios "type=11,value=$c")
done

VARS=$(mktemp)
cp /usr/share/OVMF/OVMF_VARS_4M.fd "$VARS"
timeout 1200 qemu-system-x86_64 -enable-kvm -cpu host -smp 2 -m 4096 \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
    -drive if=pflash,format=raw,file="$VARS" \
    -drive file="$DISK",if=virtio,format=qcow2,snapshot=on \
    -display none -serial file:"$LOG" "${smbios[@]}" || true
chmod a+r "$LOG"
grep -a BENCH "$LOG" || echo "No benchmark output in $LOG"
