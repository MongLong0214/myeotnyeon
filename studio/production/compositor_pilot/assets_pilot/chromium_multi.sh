#!/bin/sh
exec "$(dirname "$0")/../node_modules/.remotion/chrome-headless-shell/mac-arm64/chrome-headless-shell-mac-arm64/chrome-headless-shell" "$@" --use-angle=swiftshader --enable-unsafe-swiftshader --disable-gpu-compositing --disable-gpu-rasterization --disable-features=SkiaGraphite
