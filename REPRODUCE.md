# Reproduce this packet from scratch

Target: `https://github.com/datalayer/jupyter-mcp-server` @ `ef47e8b9c9bfce1a23265831a1ad80f94d58bb85`
(BSD-3-Clause). Public reference: <https://jupyter-mcp-server.datalayer.tech/mcp/> — the project's
own registered domain (`datalayer.tech`), served by the project itself.

```bash
# 1. the pinned source
git clone https://github.com/datalayer/jupyter-mcp-server.git
cd jupyter-mcp-server && git checkout ef47e8b9c9bfce1a23265831a1ad80f94d58bb85

# 2. Sourcey at the version the project itself pins (docs/package.json -> devDependencies)
cd docs
npm pack sourcey@3.6.5
npm install ./sourcey-3.6.5.tgz --legacy-peer-deps
npm install @rolldown/binding-linux-x64-gnu@1.2.15 --no-save   # npm optional-dependency bug
npm run mcp-reference        # node sourcey/build_site.mjs
# -> MCP reference: 26 pages -> docs/static/mcp

# 3. prove the published site IS that build
python3 parity.py            # 26 pages fetched over plain HTTPS, sha256 compared
# -> pages compared: 26   byte-identical: 26   different: []   unreachable: []

# 4. the inventory of public APIs, read out of the pinned source
python3 inventory.py         # 23 public MCP tools/prompts with source file:line

# 5. the governed run
runx --version                # runx-cli 0.10.2  (bounty floor: 0.6.13)
runx verify --receipt receipt.json --json
```

Files in this packet: `evidence.json` (the machine-readable evidence, 19 observations),
`report.md` (the maintainer-facing gap analysis), `parity.json` (per-page sha256 of the
published pages and of our rebuild), `inventory.json` (the 23 public tools/prompts with
their source locations), `inventory.py` / `parity.py` / `build-evidence.py` (the scripts
that produced them).
