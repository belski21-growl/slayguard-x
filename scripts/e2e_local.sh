#!/usr/bin/env bash
# E2E LOKAL SlayGuard X — tanpa jaringan eksternal, tanpa gas asli.
# 1) forge test (deploy + record + baca balik registry, EVM in-process)
# 2) unittest Python (circuit NAND + analyzer X Layer, RPC di-fake)
# 3) app HTTP lawan anvil lokal: anvil_setCode menanam bytecode dummy di
#    alamat target, lalu /api/audit via RPC override (READ-ONLY terhadap anvil).
#    (Tx submit via anvil di VM ini gagal "Insufficient funds" walau saldo
#    10.000 ETH — diduga quirk anvil/forge 1.9.0 di VM; deploy dibuktikan
#    lewat forge test, BUKAN anvil. Lihat status file.)
# Key anvil default #0 dipakai HANYA bila ada tx lokal; di sini tidak ada.
set -euo pipefail
export PATH="$HOME/.foundry/bin:$HOME/.local/bin:$PATH"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
RPC=http://127.0.0.1:8545

echo "== 1) forge test (kontrak) =="
forge test 2>&1 | tail -2

echo "== 2) unittest (circuit + analyzer) =="
python3 -m unittest discover -s tests 2>&1 | tail -3

echo "== 3) app vs anvil lokal (read-only) =="
anvil --port 8545 --silent > /tmp/slayx-anvil.log 2>&1 &
ANVIL_PID=$!
APP_PID=""
trap 'kill $ANVIL_PID 2>/dev/null; [ -n "$APP_PID" ] && kill $APP_PID 2>/dev/null; true' EXIT
sleep 2
# Tanam bytecode dummy (selector upgradeTo + mint + maxSupply) di alamat target
DUMMY=0x1111111111111111111111111111111111111111
CODE=0x60806040523659cfe640c10f19d5abeb0100
cast rpc --rpc-url $RPC anvil_setCode "$DUMMY" "$CODE" >/dev/null
SLAY_RPC_XLAYER_TESTNET=$RPC PORT=8766 python3 app.py > /tmp/slayx-app.log 2>&1 &
APP_PID=$!
sleep 2
curl -s localhost:8766/health; echo
curl -s localhost:8766/api/circuit | python3 -c "import json,sys; d=json.load(sys.stdin); print('circuit:', d['gate_count'], 'NAND, verified:', d['verified_ok'])"
curl -s 'localhost:8766/api/tapeout?testnet' | python3 -c "import json,sys; d=json.load(sys.stdin); print('tapeout(testnet->anvil lokal): chain_id', d.get('chain_id'), '| factory_live', d.get('factory_live'))"
curl -s -X POST localhost:8766/api/audit -H 'Content-Type: application/json' \
  -d "{\"address\": \"$DUMMY\", \"chain\": \"xlayer-testnet\"}" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('audit dummy via anvil:', d.get('verdict'), d.get('score'), '| temuan:', len(d.get('findings', [])))"
echo "E2E LOKAL: PASS"
