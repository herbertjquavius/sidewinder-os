#!/usr/bin/env bash
# Boots a disk image headless in QEMU and takes a screenshot every 10 seconds
set -euo pipefail
DISK=$1
OUT=$2
SHOTS=${SHOTS:-18}
mkdir -p "$OUT"
VARS=$(mktemp)
cp /usr/share/OVMF/OVMF_VARS_4M.fd "$VARS"
MON=$(mktemp -u)

qemu-system-x86_64 -enable-kvm -cpu host -smp 2 -m 4096 \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
    -drive if=pflash,format=raw,file="$VARS" \
    -drive file="$DISK",if=virtio,format=qcow2,snapshot=on \
    -device virtio-vga -display none \
    -serial file:"$OUT/serial.log" \
    -monitor unix:"$MON",server,nowait ${QEMU_EXTRA:-} &
QEMU=$!
trap 'kill $QEMU 2>/dev/null || true' EXIT

for i in $(seq -w 1 "$SHOTS"); do
    sleep 10
    echo "screendump $OUT/shot-$i.ppm" | socat - UNIX-CONNECT:"$MON" >/dev/null
    # Optionally type a password and press Enter at one point, to log in like a person
    if [ -n "${TYPE_AT:-}" ] && [ "$((10#$i))" -eq "$TYPE_AT" ]; then
        for c in $(echo "$TYPE_TEXT" | grep -o .); do
            echo "sendkey $c" | socat - UNIX-CONNECT:"$MON" >/dev/null
            sleep 0.2
        done
        echo "sendkey ret" | socat - UNIX-CONNECT:"$MON" >/dev/null
    fi
done
chmod -R a+rwX "$OUT"
