# OKX Build X — Submit Package, NO-TAPEOUT option (form text, English)
**Status:** READY — fill into the submit form. User order 26 Nov 2026 ~20:50 WIB: "Gas lanjut aja sampe selesai tanpa tapeout" (finish it without tape-out).
**Tape-out: NOT executed (user HOLD 26 Nov ~16:40).**
**Video:** `video/slayguard-x-demo-no-tapeout-v2.mp4` — 97.3 s, 1920x1080, h264+AAC, 1,935,152 bytes, fully English, user-approved 26 Nov ~20:36. YouTube: https://youtu.be/k-E5g13plAM (Public, @belskiraizo, no copyright issue).
**Deadline:** 7 Dec 23:59 UTC = 8 Dec 06:59 WIB (provisional, official page).
**Project name:** SlayGuard X. **Submitter:** Belski Raizo (solo). **Contact:** belskiraizo@gmail.com.

## 1. Product description
SlayGuard X is an EVM contract audit tool for everyday users, adapted to X Layer + TapeOut. One wrong mint/approve click can drain a wallet, but most people cannot read contracts — SlayGuard X turns our team's internal audit workflow into a public product: a heuristic engine reads bytecode + on-chain state (no private key, no gas), an LLM translates findings into plain language, a live TapeOut panel shows the X Layer mainnet factory + market, a Risk Circuit of NAND gates encodes the verdict rules so verdicts are computable on-chain in the TapeOut style (not just an off-chain claim), and the SlayGuardRegistry records every verdict on X Layer mainnet so anyone can verify it.

## 2. Target users + how to reach them
- **Target:** everyday X Layer users (OKX Wallet holders, mint/DeFi users on X Layer) who cannot read contracts and have been clicking blind.
- **Reach:** distribution through the OKX/X Layer ecosystem (OKX Wallet, X Layer community), B2B integrations with X Layer wallets and marketplaces, plus the public repo + demo video.

## 3. Revenue model (freemium — from README)
Audits are free for everyone. Paid: Pro reports (detail), paid API, and B2B integrations for X Layer wallets/marketplaces.

## 4. Addresses + links (all live, verified 26 Nov 2026)
| Item | Value |
|---|---|
| SlayGuardRegistry — X Layer mainnet (chain 196) | `0x55b9460db2a22a9fA70A8cBe2c665804167A42e5` |
| Registry deploy tx (block 76,914,634, gas 680,947) | `0xcd3a368aed28410d1ea6f93a22266b87736e7aa60542616321c25f17066f969f` |
| recordAudit E2E (CAUTION 65, block 76,914,661) | `0xa9f9822dea838ced90e9c4cd5690ae633ebe20eea4b04bfbe54e4e9b05e26d4d` |
| Registry — X Layer testnet (chain 1952, same address) | `0x55b9460db2a22a9fA70A8cBe2c665804167A42e5` |
| TapeOut factory (mainnet) | `0x1f09daefa827f02cbb40967cc91b259763760761` |
| TapeOut factory implementation (the audited one, EIP-1967 proxy) | `0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a` |
| TapeOut market (mainnet) | `0xd89f358c48a7B632c9845af2a02A32eB90DD75DB` |
| GitHub repo (public, main) | https://github.com/belski21-growl/slayguard-x |
| Demo video (≤3 minutes) | https://youtu.be/k-E5g13plAM |
| Demo access (app) | Repo README: `python3 app.py` → http://127.0.0.1:8765 (endpoints `/api/audit`, `/api/tapeout`, `/api/circuit`, `/api/gasprice`) |

## 5. TapeOut features used (for the form — requirement is "circuits OR contracts OR onchain data")
SlayGuard X is a website/app/tool — not a pure circuit project — so what it uses:
1. **TapeOut contracts + onchain data (LIVE):** the app reads the TapeOut factory + market on X Layer mainnet live and read-only (`/api/tapeout`, `tapeout_status()` in `analyzer.py`) — factory/market status + gas price appear in the product panel. Interfaces/computation may run off-chain (official FAQ), as long as the TapeOut part is explained — this is it.
2. **Risk Circuit (netlist, not yet taped out):** the verdict rules are encoded as a NAND circuit — 46 gates, depth 15, exhaustively verified 256/256 input combinations (`circuit/risk_circuit.py`, `tapeout/risk_netlist.json` + `.bin`, TAP-02 format: 50 gates, 350 bytes, nIn 7, nOut 2). The video demonstrates this circuit and the voiceover calls the verdict "computable on-chain" — WITHOUT claiming tape-out is live.
3. **Own contract on X Layer:** SlayGuardRegistry (above) records verdicts on-chain.

## 6. Honest note — tape-out status (write as-is in the form)
- **Circuit ID: DOES NOT EXIST YET — tape-out has not been executed.** The processor contract has not been created either. Submitted as circuit evidence: the TAP-02 netlist + exhaustive 256/256 verifier in the repo (not an on-chain claim).
- Reason: tape-out needs 0.11 BEM in the deployer wallet on X Layer (total cost ~$0.96; the OKB leg is already covered) and BEM funding is on hold by user decision. The full tape-out plan + calldata is ready in `tapeout/COST_REPORT.md` — it can be executed any time before the deadline once the hold is lifted (see `submit-package-tapeout-checklist.md`).
- This matches the fallback recorded in the README: "circuit ID (after tape-out — or netlist + verification proof if tape-out is delayed)".

## 7. What is new during the event (substantial new development — from README)
All built 25–26 Nov 2026, inside the event period:
1. New chain: X Layer mainnet (196) + testnet (1952).
2. TapeOut onchain data integration (live reads of mainnet factory + market).
3. New Risk Circuit NAND (46 gates, depth 15, 256/256).
4. SlayGuardRegistry (new Solidity contract) + mainnet + testnet deploys.
5. New endpoints + UI: `/api/tapeout`, `/api/circuit`, `/api/gasprice`.
Reused from the original SlayGuard: the heuristic analyzer engine + server + base UI (foundation, not the entry itself).

## 8. Test evidence (from README + live 26 Nov)
- `forge test`: 5/5 PASS (contract). `python3 -m unittest discover -s tests`: 11/11 PASS.
- Local E2E: PASS. Live mainnet E2E: deploy + recordAudit + read-back PASS (CAUTION 65, findingsHash matched).
- Live audit example: TapeOut factory implementation → CAUTION 65/100 (upgradeTo −25, owner withdraw −10).

## 9. Pre-submit checklist
- [x] User watched the video + OK'd it. DONE 26 Nov ~20:36 (v2).
- [x] Video uploaded to YouTube. DONE 26 Nov ~20:48: https://youtu.be/k-E5g13plAM.
- [ ] Fill the OKX submit form with the draft above — IN PROGRESS 26 Nov ~20:50 (user order: finish without tape-out).
