#!/bin/sh
exec "$(dirname "$0")/../production/compositor/src/v4spike/chromium.sh" "$@" --host-resolver-rules='MAP * ~NOTFOUND' --disable-background-networking --disable-component-update --disable-sync
