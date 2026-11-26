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
What's new in SlayGuard X (all done 25–26 Nov 2026, inside the event period):
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
- `video/` — demo video (final: `slayguard-x-demo-no-tapeout-v2.mp4`, 97.3 s) + render scripts
- `tapeout/` — Risk Circuit netlist, cost report, fork sim, tape-out calldata

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

## Tests (re-run 26 Nov 2026 ~20:50 WIB — all PASS)

```bash
forge test -vv --gas-report        # 5/5 PASS (contract)
python3 -m unittest discover -s tests   # 11/11 PASS (circuit + analyzer)
bash scripts/e2e_local.sh          # LOCAL E2E: PASS
python3 tests/live_e2e_xlayer.py   # LIVE read-only — PASS 26 Nov 2026 ~15:12 WIB
                                   # (mainnet block 76,911,718; factory + market LIVE;
                                   # gas 0.02 gwei on mainnet + testnet)
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

Both figures were confirmed live on testnet and mainnet on 26 Nov 2026
(deploy 680,947 gas; first recordAudit 116,149 gas — exact match).

## Mainnet X Layer cost — estimate vs actual (OKB ≈ $81.92, 26 Nov 2026, CoinGecko)

| Action | @1 gwei | @10 gwei | @100 gwei |
|---|---|---|---|
| Deploy registry | 0.000681 OKB ≈ **$0.06** | ≈ $0.56 | ≈ $5.59 |
| First recordAudit | ≈ $0.01 | ≈ $0.10 | ≈ $0.95 |

Live X Layer gas price was read on 26 Nov 2026 ~15:12 WIB: **0.02 gwei**
on mainnet and testnet — far below the table above. Actual mainnet costs
(26 Nov ~16:00): deploy 680,947 gas ≈ 0.0000136 OKB; first recordAudit
116,149 gas; total deploy + record ≈ **0.0000159 OKB (~$0.0013)**.
**NO mainnet deploy without user approval.** Tape-out of the Risk Circuit
to the mainnet factory: cost **KNOWN — ~$0.96 total** (TAPEOUT_FEE 0.0013 OKB
~$0.107 + gas for 3 tx, 1,322,480 @ 0.02 gwei ≈ 0.0000264 OKB + 0.11 BEM
~$0.85; full breakdown in `tapeout/COST_REPORT.md`). The deployer holds
~0.001789 OKB — enough for the OKB leg — but **BEM balance is 0**, so
tape-out cannot execute until ~0.11 BEM is funded (~$2.00 new funding:
buy ~0.112 BEM on BSC + LayerZero bridge; no BEM pool exists on X Layer).
**Tape-out is ON HOLD by user decision (26 Nov) — do not execute, do not
buy BEM, do not bridge, until the user says otherwise.**

## Mainnet — DEPLOYED LIVE 26 Nov 2026 ~16:00 WIB

- Funding: user bridged 0.0001 ETH (Base) via Relay → **0.001805028261152912 OKB**
  arrived in the deployer wallet.
- **Registry: `0x55b9460db2a22a9fA70A8cBe2c665804167A42e5`** (X Layer mainnet,
  chain 196) — tx `0xcd3a368aed28410d1ea6f93a22266b87736e7aa60542616321c25f17066f969f`,
  block 76,914,634, gas 680,947, status success. **Same address as testnet**
  (same deployer + nonce 0 + same bytecode).
- **recordAudit E2E: SUCCESS** — tx `0xa9f9822dea838ced90e9c4cd5690ae633ebe20eea4b04bfbe54e4e9b05e26d4d`,
  block 76,914,661, gas 116,149; getAudit read-back matched (CAUTION, 65,
  findings hash, auditor).
- Total mainnet cost ≈ 0.0000159 OKB (~$0.0013); deployer balance after
  ≈ 0.001789 OKB.

## Testnet — DEPLOYED LIVE 26 Nov 2026 ~15:20 WIB

- X Layer testnet: chain 1952, RPC `https://testrpc.xlayer.tech/terigon`,
  official faucet `web3.okx.com/xlayer/faucet` (0.2 OKB/day, claim via browser).
- Faucet claimed 26 Nov 15:17–15:20 ("Successfully queued 0.2 OKB");
  on-chain balance verified: 0.2 OKB, nonce 0.
- **Registry: `0x55b9460db2a22a9fA70A8cBe2c665804167A42e5`** (X Layer testnet,
  chain 1952) — tx `0x4136a0a26efc4e05e65b79c561f0372766a0446a0db3788afc121d49d0bbd455`,
  block 47,222,412, gas 680,947, status success. **Same address as mainnet**
  (same deployer + nonce 0 + same bytecode).
- **recordAudit E2E: SUCCESS** — tx `0xd09752e180a1d2ebc61315178a6399e7b07e048ddc0cdfdfed52141057118709`,
  block 47,222,449, gas 116,149; getAudit read-back matched (CAUTION, 65).
- Total testnet cost ≈ 0.000016 OKB (~$0.0013); deployer balance after
  ≈ 0.199984 OKB.

## Demo video — DONE (v2, user-approved 26 Nov 2026 ~20:36 WIB)

File: `video/slayguard-x-demo-no-tapeout-v2.mp4` — 97.3 s (≤3 min ✓),
1920x1080, h264+AAC, ~1.9 MB; English voiceover (TTS), 8 segments, all
on-screen text in English. Segments:

- 0:00–0:20 Problem: 1 wrong mint/approve click can drain a wallet.
- 0:20–0:50 Live audit of an X Layer contract → verdict + human-language explanation.
- 0:50–1:20 Live TapeOut panel + NAND Risk Circuit (46 gates, 256/256).
- 1:20–1:50 Registry: verdict recorded on-chain, checkable by anyone.
- 1:50–2:40 Target users + revenue: freemium (free audits; paid Pro reports + API;
  B2B for X Layer wallets/marketplaces).
- 2:40–3:00 Close: repo + demo link + what is new during the event.

**Not yet uploaded to YouTube** — upload is the user's hands, then the
YouTube link goes into the submission form. The video makes no tape-out
claim (tape-out is on HOLD); the circuit is shown as a verified netlist
(46 NAND gates, exhaustive 256/256).

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

## Blockers / status (updated 26 Nov 2026)

Resolved (were blockers, now done — kept here so the history is honest):
1. ~~VM egress to public RPCs hits an approval card.~~ **RESOLVED 26 Nov
   ~15:11** — user approved egress; `tests/live_e2e_xlayer.py` PASSED
   ~15:12 (mainnet block 76,911,718; factory + market LIVE; gas 0.02 gwei).
2. ~~Faucet + testnet deploy need manual user steps.~~ **DONE 26 Nov
   ~15:20** — faucet claimed (0.2 OKB), registry deployed + recordAudit
   E2E on testnet (see "Testnet" above). Mainnet deploy + recordAudit
   also DONE 26 Nov ~16:00 (see "Mainnet" above).
3. ~~Tape-out circuit cost not yet known.~~ **KNOWN 26 Nov ~16:36**
   (~$0.96 total; fork sim PASS 1/1; see `tapeout/COST_REPORT.md`).
   Remaining blocker is funding only: BEM balance is 0, ~$2.00 new
   funding needed — and **tape-out is ON HOLD by user decision**, so no
   execution until the user says otherwise.

Still open:
4. OKX explorer 403s in `browser.open` — factory address verification via
   explorer not possible from this tool (address confirmed via 2 other sources).
5. DeWEB publish (TapeKit container) needs a mainnet tape-out — stretch
   goal, not a submit blocker (FAQ: the interface does not have to be on-chain).
   Blocked by the same tape-out HOLD as item 3.

## Submit (DO NOT submit — only after user approval)

Needed for the form: product description + target users + revenue model,
registry address (testnet/mainnet), TapeOut factory + market addresses,
circuit ID (after tape-out — or netlist + verification proof if
tape-out is delayed), demo link, video ≤3 minutes.

Status 26 Nov ~20:50 WIB: registry is LIVE on testnet + mainnet (same
address `0x55b9460db2a22a9fA70A8cBe2c665804167A42e5`); demo video v2 is DONE
and user-approved; repo is public at
https://github.com/belski21-growl/slayguard-x. Still missing: the YouTube
link (video not yet uploaded — user's hands) and the circuit ID (tape-out
is ON HOLD — submit with netlist + 256/256 verification proof instead).
Two submit options are prepared in `submit-package-no-tapeout.md`
(without tape-out, ready now) and `submit-package-tapeout-checklist.md`
(finalize once the HOLD is lifted). Submit only after the user has seen
the finished entry and approved it. Deadline: 7 Dec 23:59 UTC
(= 8 Dec 06:59 WIB).
