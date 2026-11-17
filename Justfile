# One-command builds, run `just` to see them all
image := env("IMAGE", "localhost/os:latest")
kernel_image := env("KERNEL_IMAGE", "localhost/os-kernel:latest")
bib := "quay.io/centos-bootc/bootc-image-builder:latest"
# Secure Boot signing key, empty means an unsigned build
mok_key := env("MOK_KEY_FILE", "/dev/null")
# Drop-in that skips the first-boot wizard, passed to the test VM as a systemd credential
skip_setup := "W1VuaXRdCkNvbmRpdGlvblBhdGhFeGlzdHM9L3NraXAtcGxhc21hLXNldHVwCg=="

default:
    @just --list

# Render branding into branding/out
branding:
    cd branding && python3 make.py

# Build the kernel layer: CachyOS kernel, signed NVIDIA driver, scheduler (slow, run when they change)
kernel:
    sudo podman build --pull=newer --secret id=mok_key,src={{mok_key}} -f Containerfile.kernel -t {{kernel_image}} .

# Build the system image on top of the kernel layer
build:
    sudo podman build --pull=newer --build-arg BASE_IMAGE={{kernel_image}} -t {{image}} .

# Make a test disk image in output/qcow2
disk:
    mkdir -p output
    sudo podman run --rm --privileged --pull=newer \
        --security-opt label=type:unconfined_t \
        -v ./output:/output \
        -v ./tests/vm-config.toml:/config.toml:ro \
        -v /var/lib/containers/storage:/var/lib/containers/storage \
        {{bib}} --type qcow2 --rootfs btrfs {{image}}

# Make the install ISO in output/bootiso, with our kickstart and installer look
iso:
    sudo installer/make-iso.sh {{image}} {{bib}}

# Make the ISO plus a self-installing test copy, then install it in a Secure Boot VM
iso-test:
    sudo TEST=1 installer/make-iso.sh {{image}} {{bib}}
    sudo python3 tests/iso-test.py output/bootiso/$(ls output/bootiso | grep -v test | grep '\.iso$') output/iso-screens look
    sudo python3 tests/iso-test.py output/bootiso/test.iso output/iso-screens install $(. ./distro.env && echo "$NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')

# Boot the test disk headless and check it reaches our login screen
test:
    sudo SHOTS=12 tests/vm-boot.sh output/qcow2/disk.qcow2 output/screens/setup
    sudo SHOTS=30 TYPE_AT=12 TYPE_TEXT=test QEMU_EXTRA="-smbios type=11,value=io.systemd.credential.binary:systemd.unit-dropin.plasma-setup.service={{skip_setup}}" \
        tests/vm-boot.sh output/qcow2/disk.qcow2 output/screens/login
    python3 tests/shots.py output/screens/setup --no-check
    python3 tests/shots.py output/screens/login
