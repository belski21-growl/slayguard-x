# Tape-out sim log (read-only, 26 Nov 2026)

## Live eth_call sims (X Layer mainnet, from deployer 0x8F3E... — no signing)
- `createCPU(...)` -> REVERT `ERC20InsufficientAllowance(factory, 0, 10000000)`:
  factory pulls 0.10 BEM deployFee; deployer holds 0 BEM + 0 allowance.
  BUKAN rute mati — ini bukti jalurnya benar + fee-nya 10.000.000 base units.
- `tapeout(netlist,7,2)` (on ViperX cpu, value 0.0013 OKB) -> REVERT
  `ERC1155InsufficientBalance(deployer, 0, 50, 0)`: tape-out burns 50 NAND,
  deployer holds 0. BUKAN rute mati — bukti jumlah NAND yang dibakar = 50.
- `eval` sanity on ViperX circuit 1: input 500 (LE bytes 0xF401) -> 0x01 PASS;
  input 2500 (0xC409) -> 0x00 FAIL. Read path + LE packing terverifikasi.

## Fork sim (forge test, fork X Layer mainnet, in-process, no real tx/key)
- File: fork-sim/test/TapeOutSim.t.sol — PASS 1/1 (19.42s)
- Result: fork_sim_result.json
- Processor (FORK-ONLY address, will differ on real run): 0xDFd3A2BB3a0B8bCDEBCD2230671c0af335b6A322
- Circuit id: 1; gas createCPU 739652, mint 190313, tapeout 392515 (total 1322480)
- TAPEOUT_FEE 0.0013 OKB; BEM spent 11000000 base = 0.11 BEM; eval 256/256 PASS
- Note: forge on the fork does not deduct gas from the pranked sender's
  balance (okb_spent_wei == tapeout fee exactly), so gas cost is computed
  separately: 1,322,480 gas x 0.02 gwei = 0.0000264496 OKB.

## Live reads used (all in live_*.log)
- factory cpuCount 455; deployFee 10,000,000 (0.10 BEM); protocolFee 1,000,000 (0.01 BEM)
- TAPEOUT_FEE 0.0013 OKB on cpu 0, 424 (ViperX), 454 — constant across processors
- ViperX transistors: mintPrice 0, protocolFee 0.01 BEM, supplyCap 158, minted 158 (FULL)
- BEM X Layer 0x60e62Efa9405d6873C5deaBD4E6CC91c25363952, decimals 8, totalSupply 15,824.75 BEM
- BEM balances mapping slot 5 (verified vs protocolWallet 416.445 BEM)
- OKB $82.10 (OKX ticker), BEM $7.71 (PancakeSwap BSC, liq $117k), BNB $554.30
- No BEM pool on X Layer (DexScreener 0 pairs) — BSC buy + LayerZero bridge only.
