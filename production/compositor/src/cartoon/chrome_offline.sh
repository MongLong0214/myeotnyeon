#!/bin/sh
# Loopback is required by Remotion. All DNS names other than localhost are disabled.
exec /Users/isaac/projects/verdict-kr/work/production/compositor/node_modules/.remotion/chrome-headless-shell/mac-arm64/chrome-headless-shell-mac-arm64/chrome-headless-shell --host-resolver-rules='MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1' --disable-background-networking --disable-component-update --disable-sync --disable-domain-reliability --no-pings "$@"
