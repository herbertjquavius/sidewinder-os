#!/usr/bin/env bash
# Root tasks for the welcome app, run through pkexec
set -euo pipefail

case "${1:-}" in
    update)
        # Downloads the new system, it gets used on the next restart
        bootc upgrade --quiet
        if bootc status --format=json | python3 -c 'import json,sys; sys.exit(0 if json.load(sys.stdin)["status"].get("staged") else 1)'; then
            echo staged
        else
            echo current
        fi
        ;;
    rollback)
        bootc rollback
        ;;
    fix-network)
        systemctl restart NetworkManager
        systemctl restart bluetooth
        ;;
    battery-on|battery-off)
        # Saves the choice and applies it now, the boot service applies it after restarts
        mkdir -p /etc/SLUGDIR
        [ "$1" = battery-on ] && echo on > /etc/SLUGDIR/battery-limit || echo off > /etc/SLUGDIR/battery-limit
        /usr/libexec/SLUGDIR-battery
        ;;
    *)
        echo "Unknown task" >&2
        exit 2
        ;;
esac
