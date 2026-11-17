# One-command builds, run `just` to see them all
image := env("IMAGE", "localhost/os:latest")
bib := "quay.io/centos-bootc/bootc-image-builder:latest"

default:
    @just --list

# Render branding into branding/out
branding:
    cd branding && python3 make.py

# Build the system image
build:
    sudo podman build --pull=newer -t {{image}} .

# Make a test disk image in output/qcow2
disk:
    mkdir -p output
    sudo podman run --rm --privileged --pull=newer \
        --security-opt label=type:unconfined_t \
        -v ./output:/output \
        -v ./tests/vm-config.toml:/config.toml:ro \
        -v /var/lib/containers/storage:/var/lib/containers/storage \
        {{bib}} --type qcow2 --rootfs btrfs {{image}}

# Make the install ISO in output/bootiso
iso:
    mkdir -p output
    sudo podman run --rm --privileged --pull=newer \
        --security-opt label=type:unconfined_t \
        -v ./output:/output \
        -v /var/lib/containers/storage:/var/lib/containers/storage \
        {{bib}} --type anaconda-iso --rootfs btrfs {{image}}

# Boot the test disk headless and check it reaches our login screen
test:
    sudo tests/vm-boot.sh output/qcow2/disk.qcow2 output/screens
    python3 tests/shots.py output/screens
