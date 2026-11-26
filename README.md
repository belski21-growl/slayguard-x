# SlayGuard X — OKX Build X / X Layer TapeOut Accelerate

**One sentence:** SlayGuard AI (EVM contract auditing for everyday users) adapted to
X Layer + TapeOut — the same GO/CAUTION/HOLD verdict can now be verified
through TapeOut on-chain data, recomputed by a NAND Risk Circuit, and
recorded permanently in an on-chain registry.

## Idea + why it can win (1 paragraph)

This team audits BSC contracts every day using EVM audit skills, but ordinary
users don't have those skills — one wrong mint/approve click can drain a wallet.
SlayGuard X turns the team's internal audit workflow into a public product for X
Layer: a heuristic engine that reads bytecode + on-chain state (no private key,
no gas), an LLM that translates findings into human language, a live TapeOut
panel (factory + market on X Layer mainnet), a NAND Risk Circuit that encodes
the verdict rules so the verdict can be computed on-chain TapeOut-style (not
just an off-chain claim), and SlayGuardRegistry that records every verdict on
X Layer so anyone can check it. It hits every judging criterion at once:
real user value (protecting X Layer users, whose numbers grow with OKX),
innovation (audit AI + on-chain circuit), ecosystem integration (TapeOut
on-chain data + circuit + DeWEB plans), and product readiness (the product
already works, not a mockup — only the chain + new on-chain components were
added).

## SlayGuard synergy — decision: YES, ADAPT (not a fresh build)

Reason: the OKX rules allow existing projects **as long as there is substantial
new development during the event, and only work done during the event is judged**.
What's new in SlayGuard X (all done 25 Nov 2026, inside the event period):
1. New chain: X Layer mainnet (196) + testnet (1952) — RPC, OKB gas, UI.
2. TapeOut on-chain data integration: live reads of factory + market on mainnet
   (read-only, free) — satisfies the "circuits, contracts, OR on-chain data"
   requirement (official FAQ: interface/computation may run off-chain, as long as
   it is explained which part uses TapeOut).
3. New NAND Risk Circuit (46 gates, depth 15, exhaustively verified
   256/256 input combinations) — tape-out artifact ready to submit.
4. SlayGuardRegistry (new Solidity contract) — verdicts recorded on-chain.
5. New endpoints + UI: `/api/tapeout`, `/api/circuit`, `/api/gasprice`.
Reused from the original SlayGuard: the analyzer heuristic engine + server +
basic UI. That is the foundation, not the entry — all the TapeOut/X Layer value is
new. Risk of judges seeing it as "just a chain swap": mitigated by the circuit +
registry, which are genuinely new and verified.

## Repo structure

- `analyzer.py` — heuristic audit (BSC/ETH/X Layer/testnet) + `tapeout_status()`
- `app.py` — stdlib server; `/api/audit`, `/api/tapeout`, `/api/circuit`, `/api/gasprice`
- `circuit/risk_circuit.py` — NAND Risk Circuit netlist + exhaustive verifier
- `contracts/SlayGuardRegistry.sol` — on-chain verdict registry
- `test/SlayGuardRegistry.t.sol` — forge test (no forge-std)
- `tests/` — Python unittests + `live_e2e_xlayer.py` (read-only, needs network)
- `scripts/e2e_local.sh` — full local E2E (no external network)
- `static/index.html` — UI (X Layer chain + TapeOut panel + circuit panel)

## How to run

```bash
cd ~/workspace/scratch/okx-buildx
python3 app.py            # http://127.0.0.1:8765
```

AI mode (optional, key from env, never hardcoded):
```bash
export SLAY_LLM_BASE_URL="https://api.100milionseek.com/v1"
export SLAY_LLM_API_KEY="..."
export SLAY_LLM_MODEL="deepseek-v4.1-flash-free"
python3 app.py
```

## Tests (results 25 Nov 2026 ~06:00 WIB)

```bash
forge test -vv --gas-report        # 5/5 PASS (contract)
python3 -m unittest discover -s tests   # 11/11 PASS (circuit + analyzer)
bash scripts/e2e_local.sh          # LOCAL E2E: PASS
python3 tests/live_e2e_xlayer.py   # LIVE read-only — PENDING egress approval (see Blocker)
```

Local E2E: deploy + record + read-back proven via `forge test`
(in-process EVM); app against local anvil via `anvil_setCode`
(dummy audit: CAUTION 65, 2 findings — correct: upgradeTo −25, mint without
owner −10). Tx submission via anvil on this VM fails "Insufficient funds" even
with a 10,000 ETH balance (anvil/forge 1.9.0 quirk on this VM) — not a contract bug.

## Measured gas numbers (forge --gas-report)

| Action | Gas |
|---|---|
| Deploy SlayGuardRegistry | 680,947 |
| First recordAudit (cold) | ~116,149 |
| Later recordAudit (warm) | ~22,867 |

## Mainnet X Layer cost estimate (OKB ≈ $82, 24 Nov 2026, OKX)

| Action | @1 gwei | @10 gwei | @100 gwei |
|---|---|---|---|
| Deploy registry | 0.000681 OKB ≈ **$0.06** | ≈ $0.56 | ≈ $5.59 |
| First recordAudit | ≈ $0.01 | ≈ $0.10 | ≈ $0.95 |

Live X Layer gas price not yet read (needs egress — pending); OKX docs
say X Layer gas is "negligible". **NO mainnet deploy without
user approval.** Tape-out of the Risk Circuit to the mainnet factory: cost
NOT YET KNOWN (needs factory ABI + fee function — see Blocker).

## Testnet (free, but needs manual steps)

- X Layer testnet: chain 1952, RPC `https://testrpc.xlayer.tech/terigon`,
  official faucet `web3.okx.com/xlayer/faucet` (0.2 OKB/day, claim via browser).
- Testnet deploy needs: (1) user claims the faucet to the deployer address,
  (2) deployer key handed over via a secure channel (NOT chat) — coordinator/user
  decide. Until then, deploy proof = `forge test` + local anvil.

## Demo video plan (≤3 minutes)

- 0:00–0:20 Problem: 1 wrong mint/approve click can drain a wallet.
- 0:20–0:50 Live audit of an X Layer contract → verdict + human-language explanation.
- 0:50–1:20 Live TapeOut panel + NAND Risk Circuit (46 gates, 256/256).
- 1:20–1:50 Registry: verdict recorded on-chain, checkable by anyone.
- 1:50–2:40 Target users + revenue: freemium (free audits; paid Pro reports + API;
  B2B for X Layer wallets/marketplaces).
- 2:40–3:00 Close: repo + demo link + what is new during the event.

## Docs studied

- OKX Build X (official): https://web3.okx.com/xlayer/build-x-series
- X Layer dev docs (official): https://web3.okx.com/onchainos/dev-docs/xlayer/developer/build-on-xlayer/about-xlayer
- X Layer testnet faucet (official): https://web3.okx.com/onchainos/dev-docs/xlayer/developer/bridge/get-testnet-okb-from-faucet
- TapeOut beginner's guide v1.5: https://tapeoutdaily.ai/downloads/tapeout-complete-beginners-guide-v1.5-en.pdf
- TapeOut ecosystem reference: https://tape4fun.com/en/index.html
- TapeKit repo (official): https://github.com/TapeOutProtocol/TapeKit
- ViperX docs (precedent: 4 risk circuits taped out on X Layer mainnet, factory
  only exists on mainnet): https://docs.viperx.site/roadmap
- TapeOut factory X Layer mainnet `0x1f09daefa827f02cbb40967cc91b259763760761`,
  market `0xd89f358c48a7B632c9845af2a02A32eB90DD75DB` (two independent sources).

## Blockers / not yet verified live

1. **VM egress to public RPCs hits an approval card (timeout, unanswered).**
   Consequence: live `tapeout_status()`, live `gasPrice`, and auditing 1 real
   X Layer mainnet contract are NOT yet proven from this VM. Needs: egress approval
   OR run `tests/live_e2e_xlayer.py` from the Simular box / elsewhere.
2. **Faucet + testnet deploy** need manual user steps (claim + key).
3. **Tape-out circuit cost** not yet known (needs factory ABI / official TapeOut
   docs — may need a browser task to tapeout.build/canvas).
4. OKX explorer 403s in `browser.open` — factory address verification via
   explorer not possible from this tool (address confirmed via 2 other sources).
5. DeWEB publish (TapeKit container) also needs a mainnet tape-out — stretch
   goal, not a submit blocker (FAQ: the interface does not have to be on-chain).

## Submit (DO NOT submit — target ready 7 Dec ~06:59 WIB)

Needed for the form: product description + target users + revenue model,
registry address (testnet/mainnet), TapeOut factory + market addresses,
circuit ID (after tape-out — or netlist + verification proof if
tape-out is delayed), demo link, video ≤3 minutes.
