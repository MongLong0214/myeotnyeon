#!/bin/zsh
# usage: vz_get.sh <vecteezy vector-art slug> <outdir>  -- anonymous free-licence download (site's normal free flow)
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
P="https://www.vecteezy.com/vector-art/$1"; mkdir -p "$2"; J=$(mktemp); H=$(mktemp)
curl -sL -A "$UA" -c $J -b $J -o $H "$P"
grep -q 'Free License' $H || { echo "NOT FREE $1"; exit 1; }
dp=$(grep -oE 'data-download-download-path-value="[^"]+"' $H | head -1 | sed -E 's/.*="//;s/"$//;s/&amp;/\&/g')
tok=$(grep -oE 'name="csrf-token" content="[^"]+"' $H | sed -E 's/.*content="//;s/"//')
u=$(curl -s -A "$UA" -b $J -H "Accept: application/json" -H "X-CSRF-Token: $tok" -H "X-Requested-With: XMLHttpRequest" -H "Referer: $P" "https://www.vecteezy.com$dp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('url') or '')")
[ -n "$u" ] || { echo "NO URL $1"; exit 1; }
curl -sL -A "$UA" -o "$2/$1.zip" "$u"; ls -la "$2/$1.zip" | awk '{print $5, $9}'; rm -f $J $H
