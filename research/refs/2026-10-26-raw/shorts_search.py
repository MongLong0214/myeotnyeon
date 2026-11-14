#!/usr/bin/env python3
"""Public (logged-out) YouTube Shorts search: query -> shorts ids + accessibility text.
Usage: shorts_search.py <out.jsonl> <max_pages> <query>...
Appends one JSON line per result; prints a log line per query (json) to stdout."""
import json, re, sys, time, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SP_SHORTS = "EgIQCQ%3D%3D"
OWN_CHANNEL = "UCw5vw6Yf-tV9klm05p-0O0A"


def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9",
        **({"Content-Type": "application/json"} if data else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def walk(o, key):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key:
                yield v
            else:
                yield from walk(v, key)
    elif isinstance(o, list):
        for x in o:
            yield from walk(x, key)


def parse(d):
    out = []
    for v in walk(d, "shortsLockupViewModel"):
        ep = (v.get("onTap", {}).get("innertubeCommand", {}).get("reelWatchEndpoint", {}))
        vid = ep.get("videoId")
        if not vid:
            continue
        out.append({"id": vid, "kind": "short", "a11y": v.get("accessibilityText", ""),
                    "own_channel": OWN_CHANNEL in urllib.parse.unquote(ep.get("params", "")) or
                    OWN_CHANNEL in _b64(ep.get("params", ""))})
    for v in walk(d, "videoRenderer"):
        vid = v.get("videoId")
        if not vid:
            continue
        title = "".join(r.get("text", "") for r in v.get("title", {}).get("runs", []))
        out.append({"id": vid, "kind": "video", "a11y": title,
                    "channel": "".join(r.get("text", "") for r in v.get("ownerText", {}).get("runs", [])),
                    "length": v.get("lengthText", {}).get("simpleText"),
                    "views_text": v.get("viewCountText", {}).get("simpleText")})
    conts = [c.get("continuationCommand", {}).get("token") for c in walk(d, "continuationEndpoint")]
    conts = [c for c in conts if c]
    return out, (conts[-1] if conts else None)


def _b64(s):
    import base64
    try:
        s = urllib.parse.unquote(s)
        return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)).decode("latin-1")
    except Exception:
        return ""


def search(query, max_pages):
    url = ("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query) +
           "&sp=" + SP_SHORTS)
    h = get(url)
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", h, re.S)
    key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', h).group(1)
    ver = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', h).group(1)
    items, cont = parse(json.loads(m.group(1)))
    pages = 1
    while cont and pages < max_pages:
        time.sleep(1.5)
        body = json.dumps({"context": {"client": {"clientName": "WEB", "clientVersion": ver,
                                                   "hl": "ko", "gl": "KR"}},
                           "continuation": cont}).encode()
        d = json.loads(get(f"https://www.youtube.com/youtubei/v1/search?key={key}&prettyPrint=false", body))
        more, cont = parse(d)
        if not more:
            break
        items += more
        pages += 1
    return items, pages


if __name__ == "__main__":
    out_path, max_pages, queries = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    with open(out_path, "a", encoding="utf-8") as f:
        for q in queries:
            try:
                items, pages = search(q, max_pages)
                err = None
            except Exception as e:  # noqa: BLE001
                items, pages, err = [], 0, repr(e)
            seen = set()
            for i, it in enumerate(items):
                if it["id"] in seen:
                    continue
                seen.add(it["id"])
                f.write(json.dumps({"query": q, "rank": i + 1, **it}, ensure_ascii=False) + "\n")
            print(json.dumps({"query": q, "method": "youtube.com/results sp=Shorts (logged-out HTML + youtubei continuation)",
                              "results": len(seen), "shorts": sum(1 for x in items if x['kind'] == 'short'),
                              "pages_reached": pages, "error": err,
                              "observed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}, ensure_ascii=False), flush=True)
            time.sleep(2)
