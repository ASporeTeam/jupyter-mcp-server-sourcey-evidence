#!/usr/bin/env python3
"""
agent-2 2026-10-22T14:4xZ — Frantic #33 PARITY PROOF (public_url == our pinned-commit build).

Proves, page by page, that the Sourcey reference served at the PROJECT'S OWN
domain is exactly what Sourcey produces from the pinned commit of the target
repo, with the project's own config and the project's own pinned Sourcey
version.  This is the artifact the reviewer can re-run.

    python3 agent2-33-parity.py            # check and print
    python3 agent2-33-parity.py --json out.json

REBUILD (done by agent-2, a2 lane, see notes/agent2-33-rebuild/):
    npm pack sourcey@3.6.5 && npm install ./sourcey-3.6.5.tgz --legacy-peer-deps
    npm install @rolldown/binding-linux-x64-gnu@1.2.15   # npm optional-dep bug
    cp -r <repo>/docs/sourcey ./sourcey && cd sourcey && node build_site.mjs
    -> "MCP reference: 26 pages -> docs/static/mcp"
"""
import hashlib
import json
import pathlib
import subprocess
import sys
import urllib.request

LOCAL = pathlib.Path("/srv/shared/gc/notes/agent2-33-rebuild/static/mcp")
LIVE = "https://jupyter-mcp-server.datalayer.tech/mcp/"
UA = {"User-Agent": "spore-crew/1.0 (parity proof)"}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def pages():
    out = []
    for p in sorted(LOCAL.rglob("*.html")):
        rel = p.relative_to(LOCAL).as_posix()
        if rel.endswith("index.html"):
            rel = rel[: -len("index.html")]
        out.append(rel)
    return out


def main():
    res = {"live": LIVE, "checked_at": "", "pages": [], "identical": 0,
           "different": [], "missing_live": []}
    res["checked_at"] = subprocess.run(
        ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip()
    for rel in pages():
        url = LIVE + rel
        lp = LOCAL / (rel + "index.html" if not rel.endswith(".html") else rel)
        if not lp.exists():
            lp = LOCAL / rel
        if not lp.exists():
            continue
        lb = lp.read_bytes()
        try:
            rb = fetch(url)
        except Exception as e:
            res["missing_live"].append({"page": rel, "error": repr(e)[:90]})
            continue
        same = sha(lb) == sha(rb)
        res["pages"].append({"page": rel or "/", "local_sha256": sha(lb),
                             "live_sha256": sha(rb), "local_bytes": len(lb),
                             "live_bytes": len(rb), "identical": same})
        if same:
            res["identical"] += 1
        else:
            res["different"].append(rel or "/")
    print("live   : %s" % LIVE)
    print("pages compared: %d   byte-identical: %d   different: %s   unreachable: %s" % (
        len(res["pages"]), res["identical"], res["different"], res["missing_live"]))
    for p in res["pages"][:6]:
        print("  %-28s %s %s" % (p["page"], p["local_sha256"][:16], p["live_sha256"][:16]))
    if "--json" in sys.argv:
        out = pathlib.Path(sys.argv[sys.argv.index("--json") + 1])
        out.write_text(json.dumps(res, indent=1))
        print("wrote", out)
    return 0 if not res["different"] else 1


if __name__ == "__main__":
    sys.exit(main())
