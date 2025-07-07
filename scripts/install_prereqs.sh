#!/bin/sh
set -e

# Determine package manager
if command -v apt-get >/dev/null 2>&1; then
    PKG_MGR=apt
elif command -v brew >/dev/null 2>&1; then
    PKG_MGR=brew
else
    echo "Unsupported system. Please install JACK and jacktrip manually." >&2
    exit 1
fi

# Helper to run commands with sudo if not root
if [ "$(id -u)" -ne 0 ]; then
    SUDO=sudo
else
    SUDO=
fi

apt_install() {
    packages="jackd2 jacktrip libjack-jackd2-dev"
    missing=""
    for pkg in $packages; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            missing="$missing $pkg"
        fi
    done
    if [ -z "$missing" ]; then
        echo "Prerequisites already installed"
        return
    fi
    echo "Installing:$missing"
    $SUDO apt-get update
    $SUDO apt-get install -y --no-install-recommends $missing
}

brew_install() {
    packages="jack jacktrip"
    missing=""
    for pkg in $packages; do
        if ! brew ls --versions "$pkg" >/dev/null 2>&1; then
            missing="$missing $pkg"
        fi
    done
    if [ -z "$missing" ]; then
        echo "Prerequisites already installed"
        return
    fi
    echo "Installing:$missing"
    brew install $missing
}

case "$PKG_MGR" in
    apt)
        apt_install
        ;;
    brew)
        brew_install
        ;;
esac
