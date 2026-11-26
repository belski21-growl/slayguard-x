#!/bin/bash
# record-demo.sh — drives the SlayGuard X demo-video terminal session.
# Run under `script` for timing capture. READ-ONLY: local API (127.0.0.1:8765)
# + public X Layer RPC (eth_call). No key, no signing, no tx anywhere.
# The app must already be running: cd ~/workspace/scratch/okx-buildx && python3 app.py
set -o pipefail
FACTORY=0x1f09daefa827f02cbb40967cc91b259763760761
IMPL=0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a
cd "$HOME/workspace/scratch/okx-buildx" || exit 1

say() { printf '\n### %s ###\n\n' "$1"; sleep 2; }

say "1 - PROBLEM: one wrong mint or approve can drain a wallet. Most people cannot read a contract."
sleep 8

say "2 - LIVE AUDIT: the TapeOut factory on X Layer mainnet is a proxy - the real logic lives in its implementation. Audit the logic."
curl -s -X POST http://127.0.0.1:8765/api/audit -H 'Content-Type: application/json' -d "{\"address\":\"$IMPL\",\"chain\":\"xlayer\"}" | jq -r '"verdict: \(.verdict)  score: \(.score)/100", (.findings[] | "  - [\(.severity) -\(.points)] \(.title)"), ("plain language: " + .explanation)'
sleep 8

say "3 - TAPEOUT LIVE: factory + market on X Layer mainnet, plus live gas."
curl -s http://127.0.0.1:8765/api/tapeout | jq -r '"chain: \(.chain) (id \(.chain_id))  block: \(.block_number)", "factory: live (\(.factory_code_bytes) bytes of code)", "market:  live (\(.market_code_bytes) bytes of code)"'
curl -s http://127.0.0.1:8765/api/gasprice | jq -r '"gas price: \(.gas_price_gwei) gwei"'
sleep 6

say "4 - RISK CIRCUIT: the verdict rules as pure NAND logic - verified against every input before any tape-out."
python3 circuit/risk_circuit.py | head -1
curl -s http://127.0.0.1:8765/api/circuit | jq -r '"gates: \(.gate_count) NAND  depth: \(.depth)", "exhaustive check: \(.verified_exhaustive_inputs)/\(.verified_exhaustive_inputs) inputs pass"'
sleep 6

say "5 - REGISTRY ON-CHAIN: the verdict is recorded on X Layer mainnet - anyone can read it back."
python3 video/show_registry.py
sleep 8

say "6 - WHO PAYS: free audits for everyone; Pro reports, API and B2B pay for it."
printf '  Free : audits for everyone - no wallet, no gas\n  Pro  : full reports + history + alerts\n  API  : paid API for wallets and marketplaces\n  B2B  : X Layer wallets and marketplaces embed SlayGuard\n'
sleep 8

say "7 - CLOSE: SlayGuard X - audit before you click. OKX Build X, X Layer TapeOut Accelerate."
sleep 2
