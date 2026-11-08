#!/bin/sh
exec production/compositor/node_modules/.remotion/chrome-headless-shell/mac-arm64/chrome-headless-shell-mac-arm64/chrome-headless-shell --host-resolver-rules='MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1' --disable-background-networking --disable-component-update --disable-sync --disable-domain-reliability --no-pings "$@"
