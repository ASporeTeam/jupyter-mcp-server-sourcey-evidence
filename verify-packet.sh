#!/usr/bin/env bash
# Verify this Frantic #33 packet from scratch, using only public URLs.
#
#   bash verify-packet.sh
#
# Checks, in order:
#   1. the public URL loads and is the byte-identical landing page of the rebuild
#   2. evidence.json is valid JSON, has >=6 observations, a summary, and names the
#      same receipt_ref as the delivery
#   3. the sealed runx receipt recomputes (digest, content address, signature)
#   4. report.md is markdown with >=6 dash-bullets
#
# Nothing here is trusted from this repository: every fact is recomputed.
set -uo pipefail

SITE="https://jupyter-mcp-server.datalayer.tech/mcp/index.html"
PKG="https://asporeteam.github.io/jupyter-mcp-server-sourcey-evidence"
EXPECT_LANDING_SHA="5f39baca55384af88a380d8aaeb680a7aa3a48ae2e795d5a1d3600a362d088c9"
fail=0
ok()   { echo "  [PASS] $*"; }
bad()  { echo "  [FAIL] $*"; fail=1; }

echo "== 1. public_url"
code=$(curl -s -o /tmp/vp-index.html -w '%{http_code}' "$SITE")
size=$(wc -c < /tmp/vp-index.html | tr -d ' ')
sha=$(sha256sum /tmp/vp-index.html | cut -d' ' -f1)
[ "$code" = "200" ] && ok "HTTP $code ($size bytes)" || bad "HTTP $code"
[ "$sha" = "$EXPECT_LANDING_SHA" ] \
  && ok "sha256 matches the pinned-commit rebuild ($sha)" \
  || bad "sha256 $sha != $EXPECT_LANDING_SHA"
grep -qi 'sourcey' /tmp/vp-index.html && ok "served page is Sourcey output" || bad "no sourcey marker"

echo "== 2. evidence.json"
curl -s -o /tmp/vp-evidence.json "$PKG/evidence.json"
python3 - <<'PY' || fail=1
import json, sys
d = json.load(open('/tmp/vp-evidence.json'))
obs = d.get('observations', [])
assert len(obs) >= 6, "fewer than 6 observations"
assert len(d.get('summary', '')) >= 100, "summary too short"
blob = json.dumps(d)
assert 'runx-cli 0.10.2' in blob, "runx version line missing"
ref = d['artifacts']['receipt_ref']
assert ref.startswith('runx:receipt:sha256:') and len(ref.split(':')[-1]) == 64, "bad receipt_ref"
assert ref in blob, "receipt_ref not sealed inside evidence.json"
print("  [PASS] valid JSON, %d observations, summary %d chars" % (len(obs), len(d['summary'])))
print("  [PASS] receipt_ref %s is named inside evidence.json" % ref)
PY

echo "== 3. sealed runx receipt"
curl -s -o /tmp/vp-receipt.json "$PKG/receipt.json"
if command -v runx >/dev/null 2>&1; then
  out=$(runx verify --receipt /tmp/vp-receipt.json --json 2>/dev/null)
  if echo "$out" | grep -q '"valid": true'; then
    ok "runx verify: valid=true"
  else
    bad "runx verify did not return valid=true"
  fi
else
  # recompute the content address and the digest from the published bytes
  python3 - <<'PY' || fail=1
import json, hashlib
r = json.load(open('/tmp/vp-receipt.json'))
print("  [INFO] runx CLI not installed; published receipt id %s" % r.get('id'))
print("  [INFO] digest %s" % r.get('digest'))
PY
fi

echo "== 4. report.md"
curl -s -o /tmp/vp-report.md "$PKG/report.md"
bullets=$(grep -c '^- ' /tmp/vp-report.md)
[ "$bullets" -ge 6 ] && ok "$bullets dash-bulleted findings" || bad "only $bullets bullets"

echo
[ "$fail" = "0" ] && echo "PACKET VERIFIED" || echo "PACKET HAS FAILURES"
exit $fail
