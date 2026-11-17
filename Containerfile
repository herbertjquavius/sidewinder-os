# System image: Fedora Kinoite base with our branding and settings on top
ARG BASE_IMAGE=ghcr.io/ublue-os/kinoite-main:latest

# Renders all branding from distro.env
FROM registry.fedoraproject.org/fedora:latest AS branding
RUN dnf -y install python3-pillow python3-fonttools grub2-tools-extra && dnf clean all
COPY distro.env /src/distro.env
COPY branding /src/branding
RUN cd /src/branding && python3 make.py

# Files the build script needs, kept out of the final image
FROM scratch AS ctx
COPY distro.env /distro.env
COPY build /build
COPY welcome /welcome
COPY keys /keys
COPY --from=branding /src/branding/out /branding

# The signing key comes in as a build secret and never lands in the image
FROM ${BASE_IMAGE}
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=secret,id=mok_key \
    /ctx/build/build.sh
RUN bootc container lint
