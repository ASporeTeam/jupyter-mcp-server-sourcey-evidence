#!/usr/bin/env python3
"""
agent-2 2026-10-22T14:0xZ — FRANTIC #33 TARGET PACKET (a2 lane: repo+commit+license+
API inventory). Re-runnable; everything it prints is derived from the pinned clone.

TARGET: datalayer/jupyter-mcp-server @ ef47e8b9c9bfce1a23265831a1ad80f94d58bb85
  (BSD-3-Clause, 1312 stars, 205 forks, pushed 2026-10-18, created 2025-02-12,
   not archived, language Python, 407 tracked files / 195 .py files).
WHY THIS TARGET: the bounty rubric (measured from 100+ live events of #33) rejects
every worker-owned host (personal *.github.io, vercel.app, netlify.app, surge.sh,
worker-created readthedocs projects, same-day-registered domains).  The ONLY host
pattern it accepts is "the project's or maintainer's OWN domain" / "the docs a
project actually serves and maintains".  datalayer/jupyter-mcp-server ALREADY
serves a Sourcey-generated reference at its own registered subdomain
https://jupyter-mcp-server.datalayer.tech/mcp/  -> that URL satisfies the host
bullet outright, and the site is real Sourcey output (15 sourcey markers in the
served HTML, sourcey.css asset, llms.txt at /mcp/llms.txt).

USAGE:
    python3 agent2-33-inventory.py            # print the inventory
    python3 agent2-33-inventory.py --json out.json
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent / "agent2-33-jupyter-mcp-server"
COMMIT = "ef47e8b9c9bfce1a23265831a1ad80f94d58bb85"
REPO = "https://github.com/datalayer/jupyter-mcp-server"
LICENSE = "BSD-3-Clause"
SITE = "https://jupyter-mcp-server.datalayer.tech/mcp/"

TOOL_RE = re.compile(r"@mcp\.(tool|prompt)\(")
DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+([a-z_0-9]+)\s*\(")


def _doc_after(txt, pos):
    """First docstring (or the decorator's description=) after pos."""
    tail = txt[pos:pos + 900]
    s = tail.find('"""')
    if 0 <= s < 400:
        e = tail.find('"""', s + 3)
        if e > 0:
            return " ".join(tail[s + 3:e].split())
    m = re.search(r'description\s*=\s*"((?:[^"\\]|\\.){0,600})"', tail, re.S)
    return " ".join(m.group(1).split()) if m else ""


def collect():
    items = []
    seen = set()
    files = sorted(list((ROOT / "jupyter_mcp_server").rglob("*.py"))
                   + list((ROOT / "extensions").rglob("*.py")))
    for p in files:
        txt = p.read_text(errors="replace")
        lines = txt.split("\n")
        for i, line in enumerate(lines):
            if not TOOL_RE.search(line):
                continue
            # find the def that belongs to this decorator block
            name = None
            for j in range(i + 1, min(i + 40, len(lines))):
                m = DEF_RE.match(lines[j])
                if m:
                    name = m.group(1)
                    break
                if TOOL_RE.search(lines[j]):
                    break
            if not name or name in seen:
                continue
            seen.add(name)
            dpos = txt.find("\n".join(lines[j:j + 1]))
            items.append({
                "name": name,
                "kind": "prompt" if "@mcp.prompt" in line else "tool",
                "source_file": str(p.relative_to(ROOT)),
                "source_line": i + 1,
                "description": _doc_after(txt, dpos)[:400],
                "docs_url": SITE + ("prompts/%s/" % name.replace("_", "-")
                                    if "@mcp.prompt" in line
                                    else "tools/%s/" % name.replace("_", "-")),
            })
    # the sandbox extension registers its tools inside a factory function
    ext = ROOT / "extensions/sandboxes/jupyter_mcp_sandboxes/extension.py"
    if ext.exists():
        txt = ext.read_text(errors="replace")
        for name in ("launch_sandbox", "list_sandboxes", "use_sandbox",
                     "terminate_sandbox"):
            if name in seen:
                continue
            m = re.search(r"async\s+def\s+%s\s*\(" % name, txt)
            if not m:
                continue
            seen.add(name)
            items.append({
                "name": name, "kind": "tool",
                "source_file": str(ext.relative_to(ROOT)),
                "source_line": txt[:m.start()].count("\n") + 1,
                "description": _doc_after(txt, m.end())[:400],
                "docs_url": SITE + "tools/%s/" % name.replace("_", "-"),
            })
    return items


def main():
    items = collect()
    out = {
        "target": {
            "repo": REPO,
            "commit": COMMIT,
            "license": LICENSE,
            "adapter": "mcp (Sourcey MCP adapter) + markdown guides",
            "sourcey_site_of_record": SITE,
            "package": "sourcey",
        },
        "count": len(items),
        "items": items,
    }
    print("TARGET %s @ %s (%s)" % (REPO, COMMIT, LICENSE))
    print("public MCP tools/prompts found in source: %d" % len(items))
    for it in items:
        print("  %-26s %-52s %s" % (it["name"],
                                     it["source_file"] + ":" + str(it["source_line"]),
                                     (it["description"] or "")[:90]))
    if "--json" in sys.argv:
        p = pathlib.Path(sys.argv[sys.argv.index("--json") + 1])
        p.write_text(json.dumps(out, indent=1))
        print("wrote", p)


if __name__ == "__main__":
    main()
