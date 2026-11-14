#!/bin/bash
# Re-authorize the read-only YouTube Analytics OAuth token (Testing-mode apps expire every 7 days).
# Starts oauth_setup.py and prints AUTH_URL; open it in the logged-in Aside browser, pick the channel's Google account,
# Brand channels: reauth.sh <registry key> (guessthesentence | nannenderu | beastclash) and pick THAT brand channel
# at consent; the token is stored per channel and only if the channel id matches the registry.
# accept the unverified-app warning (our own app), tick both read-only scopes, continue. Verify CHANNELS shows 몇년나옴.
cd "$(dirname "$0")/../.." && exec .venv/bin/python -u channel/analytics/oauth_setup.py "$@"
