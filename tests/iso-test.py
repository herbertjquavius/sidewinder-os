#!/usr/bin/env python3
# Boots an install ISO in a VM with Secure Boot on and takes screenshots
# look: just shows the installer; install: lets the test copy install, enrolls our key on the blue screen, checks it boots to our login
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

from PIL import Image

ISO, OUT, MODE = sys.argv[1], sys.argv[2], sys.argv[3]
PASSWORD = sys.argv[4] if len(sys.argv) > 4 else ""
os.makedirs(OUT, exist_ok=True)
tmp = tempfile.mkdtemp()
disk = os.path.join(tmp, "disk.qcow2")
subprocess.run(["qemu-img", "create", "-q", "-f", "qcow2", disk, "60G"], check=True)
vars_fd = os.path.join(tmp, "vars.fd")
shutil.copy("/usr/share/OVMF/OVMF_VARS_4M.ms.fd", vars_fd)
sock = os.path.join(tmp, "mon.sock")

qemu = subprocess.Popen([
    "qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-smp", "4", "-m", "8192",
    "-machine", "q35,smm=on", "-global", "driver=cfi.pflash01,property=secure,value=on",
    "-drive", "if=pflash,format=raw,unit=0,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.secboot.fd",
    "-drive", f"if=pflash,format=raw,unit=1,file={vars_fd}",
    # Disk first, so after the install it boots the disk instead of installing again
    "-drive", f"file={disk},if=none,id=d0,format=qcow2", "-device", "virtio-blk-pci,drive=d0,bootindex=1",
    "-drive", f"file={ISO},if=none,id=cd,media=cdrom,readonly=on", "-device", "ide-cd,drive=cd,bootindex=2",
    "-device", "virtio-vga", "-display", "none",
    "-serial", f"file:{OUT}/serial-{MODE}.log",
    "-monitor", f"unix:{sock},server,nowait",
])


def mon(cmd):
    # One command to the QEMU monitor
    for _ in range(50):
        try:
            s = socket.socket(socket.AF_UNIX)
            s.connect(sock)
            break
        except OSError:
            time.sleep(0.2)
    s.settimeout(2)
    try:
        s.recv(4096)
        s.sendall((cmd + "\n").encode())
        time.sleep(0.3)
        s.recv(65536)
    except OSError:
        pass
    s.close()


def shot(name=None):
    # Screenshot as a PIL image, saved as PNG when named
    ppm = os.path.join(tmp, "s.ppm")
    if os.path.exists(ppm):
        os.remove(ppm)
    mon(f"screendump {ppm}")
    for _ in range(20):
        if os.path.exists(ppm) and os.path.getsize(ppm) > 100:
            break
        time.sleep(0.2)
    try:
        img = Image.open(ppm).convert("RGB")
        img.load()
    except Exception:
        return None
    if name:
        img.save(os.path.join(OUT, name + ".png"))
    return img


def share(img, test):
    # Fraction of pixels that pass a color test, on a small copy
    small = img.resize((160, 100))
    px = list(small.getdata())
    return sum(1 for p in px if test(*p)) / len(px)


def is_blue(img):
    # Shim's key manager draws white text on a solid blue screen
    return share(img, lambda r, g, b: b > 140 and r < 60 and g < 60) > 0.2


def shim_started():
    # Serial log shows shim starting from the disk after the install
    try:
        log = open(os.path.join(OUT, f"serial-{MODE}.log"), errors="ignore").read()
    except OSError:
        return False
    i = log.find("Install finished")
    return i >= 0 and "shimx64.efi" in log[i:]


def is_ours(img):
    # Our login and setup screens use the HUD green
    return share(img, lambda r, g, b: g > 200 and r < 140 and b < 170 and g - r > 90) > 0.004


def key(k, wait=2.0):
    mon(f"sendkey {k}")
    time.sleep(wait)


def done(ok, msg):
    print(("PASS: " if ok else "FAIL: ") + msg)
    qemu.kill()
    subprocess.run(["chmod", "-R", "a+rwX", OUT])
    sys.exit(0 if ok else 1)


start = time.time()
if MODE == "look":
    # Pictures of the installer for 5 minutes
    for i in range(30):
        time.sleep(10)
        shot(f"installer-{i:02d}")
    done(True, "installer pictures taken")

# Install, then wait for the blue key screen after the restart
n = 0
while True:
    time.sleep(2)
    img = shot()
    if img is None:
        continue
    n += 1
    if n % 15 == 0:
        img.save(os.path.join(OUT, f"install-{n // 15:03d}.png"))
    if is_blue(img):
        break
    if shim_started():
        # Key screen only stays up 10 seconds, so watch closely
        t1 = time.time()
        while time.time() - t1 < 8 and not is_blue(img):
            time.sleep(0.5)
            img = shot() or img
        break
    if qemu.poll() is not None:
        done(False, "VM stopped during install")
    if time.time() - start > 75 * 60:
        done(False, "no Secure Boot key screen after 75 minutes")
print(f"Key screen after {int(time.time() - start)}s")

# Enroll: menu opens directly (timeout -1), so Enroll MOK, Continue, Yes, password, Reboot
time.sleep(2)
shot("mok-1-menu")
key("down"); key("ret")
shot("mok-3-enroll")
key("down"); key("ret")
shot("mok-4-confirm")
key("down"); key("ret")
shot("mok-5-password")
for c in PASSWORD:
    key(c, 0.2)
key("ret")
shot("mok-6-done")
key("ret", 1)

# Boot menu and first boot with Secure Boot on
t0 = time.time()
i = 0
while time.time() - t0 < 15 * 60:
    time.sleep(2 if time.time() - t0 < 90 else 10)
    img = shot()
    if img is None:
        continue
    i += 1
    if time.time() - t0 < 90 or i % 3 == 0:
        img.save(os.path.join(OUT, f"boot-{i:03d}.png"))
    if time.time() - t0 > 60 and is_ours(img):
        time.sleep(20)
        shot("first-boot")
        done(True, f"booted to our screen {int(time.time() - t0)}s after enrolling the key")
shot("first-boot")
done(False, "did not reach our screen after enrolling the key")
