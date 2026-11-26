#!/bin/bash
# record-retry.sh — TAKE 2: re-records ONLY the network sections (2, 3, 5)
# that failed in take 1 when the X Layer RPC egress flapped.
# Same "### N - ..." headers as take 1 so the splice aligns.
# Each live call retries up to 3x and only prints on success (clean frames).
set -o pipefail
IMPL=0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a
cd "$HOME/workspace/scratch/okx-buildx" || exit 1

say() { printf '\n### %s ###\n\n' "$1"; sleep 2; }

# Run a command string up to 3x; print its output only when $marker appears.
net() {
  local marker="$1"; shift
  local tmp i
  tmp=$(mktemp)
  for i in 1 2 3; do
    if eval "$1" > "$tmp" 2>&1 && grep -q "$marker" "$tmp"; then
      cat "$tmp"; rm -f "$tmp"; return 0
    fi
    echo "(retry $i: live endpoint not answering, waiting…)"
    sleep 8
  done
  echo "LIVE CHECK FAILED after 3 tries: $marker"
  cat "$tmp"; rm -f "$tmp"; return 1
}

# Pre-check: wait for the public RPC to answer before burning a take.
for i in 1 2 3 4 5 6; do
  if curl -s --max-time 15 -X POST https://rpc.xlayer.tech \
      -H 'Content-Type: application/json' \
      -d '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' \
      | grep -q result; then
    echo "rpc.xlayer.tech live."
    break
  fi
  echo "(waiting for rpc.xlayer.tech… try $i)"
  sleep 10
done

say "2 - LIVE AUDIT: the TapeOut factory on X Layer mainnet is a proxy - the real logic lives in its implementation. Audit the logic."
net "CAUTION" "curl -s --max-time 60 -X POST http://127.0.0.1:8765/api/audit -H 'Content-Type: application/json' -d '{\"address\":\"$IMPL\",\"chain\":\"xlayer\"}' | jq -r '\"verdict: \(.verdict)  score: \(.score)/100\", (.findings[] | \"  - [\(.severity) -\(.points)] \(.title)\"), (\"plain language: \" + .explanation)'"
sleep 8

say "3 - TAPEOUT LIVE: factory + market on X Layer mainnet, plus live gas."
net "factory: live" "curl -s --max-time 60 http://127.0.0.1:8765/api/tapeout | jq -r '\"chain: \(.chain) (id \(.chain_id))  block: \(.block_number)\", \"factory: live (\(.factory_code_bytes) bytes of code)\", \"market:  live (\(.market_code_bytes) bytes of code)\"'"
net "gas price" "curl -s --max-time 60 http://127.0.0.1:8765/api/gasprice | jq -r '\"gas price: \(.gas_price_gwei) gwei\"'"
sleep 6

say "5 - REGISTRY ON-CHAIN: the verdict is recorded on X Layer mainnet - anyone can read it back."
net "CAUTION" "python3 video/show_registry.py"
sleep 8
