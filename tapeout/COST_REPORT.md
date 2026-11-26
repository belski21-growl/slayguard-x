# Biaya Tape-Out Risk Circuit — LAPORAN FINAL (26 Nov 2026, read-only)

## Jawaban singkat

| Item | Angka |
|---|---|
| Fee tape-out (`TAPEOUT_FEE`, per circuit) | **0,0013 OKB** (~$0,107) |
| Gas 3 tx (fork sim, @0,02 gwei live) | **1.322.480 gas = 0,0000264 OKB** (~$0,0022) |
| **Total OKB** (fee + gas) | **~0,001326 OKB (~$0,109)** |
| BEM (deploy fee 0,10 + mint protocol fee 0,01) | **0,11 BEM (~$0,85 @ $7,71)** |
| **GRAND TOTAL** (OKB + BEM, harga live 26 Nov) | **~$0,96** |
| Dana baru yang harus disiapkan user | **~$2,00** (0,112 BEM di BSC ~$0,86 + bridge LayerZero ~0,00203 BNB ~$1,13); OKB sudah ada di wallet |
| Saldo deployer 0,001789 OKB | **CUKUP untuk kaki OKB** (surplus ~0,00046 OKB) — **TAPI BEM 0**, jadi **BELUM BISA eksekusi** sampai 0,11 BEM masuk ke wallet di X Layer |

## Rincian biaya (semua live + terbukti fork sim)

### 1. Kaki OKB — dibayar di X Layer, dari saldo deployer
- `TAPEOUT_FEE()` = 0,0013 OKB — dibaca live dari 3 processor (cpu 0, cpu 424 ViperX,
  cpu 454): nilainya KONSTAN di semua processor, bukan per-processor.
- Gas (diukur di fork sim, bukan taksiran):
  - `createCPU` 739.652 gas
  - `mint(NAND, 50)` 190.313 gas
  - `tapeout(netlist, 7, 2)` 392.515 gas
  - Total 1.322.480 gas × 0,02 gwei = 0,0000264496 OKB
  - (+ 2× `approve` BEM, tidak dimeter terpisah di sim — taksiran <0,00001 OKB)
- Total OKB ≈ 0,001326 OKB ≈ $0,109 (@ OKB $82,10, ticker OKX live).
- Sensitivitas gas: impas di ~0,37 gwei (saldo 0,001789 − fee 0,0013, dibagi gas).
  Aturan tahan->0,1 gwei tetap berlaku; di 0,1 gwei total jadi 0,001432 OKB — masih cukup.

### 2. Kaki BEM — dibayar dalam token BEM (ERC-20, 8 desimal), BUKAN OKB
- `deployFee()` factory = 10.000.000 base units = **0,10 BEM** (ditarik dari caller saat `createCPU`; butuh `approve` dulu).
- Mint 50 NAND: `mintPrice()` processor baru = 0 (kita set saat createCPU) × 50
  + `protocolFee()` transistors = 1.000.000 = **0,01 BEM**.
- **Total BEM = 0,11 BEM.** Sama persis dengan yang diukur ViperX 16 Nov (0,10 + 0,01).
- BEM X Layer: `0x60e62Efa9405d6873C5deaBD4E6CC91c25363952`, desimal 8, totalSupply 15.824,75 BEM.
- Harga BEM live: **$7,71** (PancakeSwap BSC, pool BEM/USDT liq ~$117k; token BSC
  `0x5ce033B2bFCa3Af30b3e8C8457DeaF776A8b695a`). Turun dari ~$10,2 (16 Nov).
  → 0,11 BEM ≈ **$0,85**.
- **Tidak ada pool BEM di X Layer** (DexScreener 0 pair) — satu-satunya jalan:
  beli di BSC → bridge LayerZero ke X Layer (cara ViperX, `bridge-bem.sh`).
  Bridge: fee ~0,00203 BNB (~$1,13 @ BNB $554,30) + 0,5% dari jumlah (~0,00056 BEM).
  Runbook ViperX: siapkan **0,112 BEM + 0,0025 BNB di BSC**.

### 3. Yang TIDAK ada biayanya
- Tidak ada fee per-gerbang (mintPrice 0 — kita yang set saat createCPU).
- Tidak ada fee tetap factory selain deployFee BEM di atas.
- `factory.protocolFee()` = 1.000.000 (0,01 BEM) — itu yang dipakai transistors
  `protocolFee()`; bukan biaya tambahan di luar 0,11 BEM.
- Tidak ada langkah mint Circuit NFT terpisah — `tapeout()` langsung mint NFT
  circuit (id 1 di sim) ke caller + burn 50 NAND. Tidak ada registrasi lain.
- DeWEB container (0,08 OKB) TIDAK termasuk — itu opsional, bukan bagian tape-out.

## Verdict saldo
- OKB: BUTUH ~0,001326 → PUNYA 0,001789 → **CUKUP, surplus ~0,000463 OKB (~$0,038)**.
- BEM: BUTUH 0,11 → PUNYA 0 → **KURANG 0,11 BEM**. Ini satu-satunya blocker dana.
- Total dana baru: ~$2,00 (beli + bridge BEM). Setelah BEM masuk, eksekusi bisa
  jalan tanpa tambahan dana lain.

## Siap eksekusi? TIDAK — tinggal 1 langkah pendanaan
Alur + calldata + sim SUDAH siap 100%. Yang kurang hanya **0,11 BEM di wallet
deployer di X Layer**. Setelah itu, eksekusi = 5 tx (2 approve + 3 utama):

1. **Pendanaan (tangan user / koordinator):** beli 0,112 BEM di PancakeSwap BSC,
   bridge ke X Layer (LayerZero, EID 30274; adapter BSC
   `0xa84b8d3893de6e9922f2b29be1e1b115845f5e72`). Verifikasi:
   `cast call <BEM_XLAYER> "balanceOf(address)(uint256)" <deployer>` ≥ 11.000.000.
2. `BEM.approve(factory, 10.000.000)` — factory
   `0x1f09DAeFA827f02CBb40967cc91b259763760761`.
3. `createCPU("SlayGuard Risk Circuit","SLAYRISK","SlayGuard X risk circuit: audit verdict rules as NAND netlist.",50,0)`
   — calldata: `calldata_createCPU.txt` (388 byte). Gas fork 739.652.
   Lalu baca `cpuAt(cpuCount()-1)` → processor baru; cek `transistorsContract()`.
4. `BEM.approve(transistors, 1.000.000)` lalu `mint(0, 50)` — calldata:
   `calldata_mint.txt`. Gas fork 190.313. Cek `balanceOf(deployer, 0) == 50`.
5. `tapeout(netlist, 7, 2)` value 0,0013 OKB — calldata: `calldata_tapeout.txt`
   (netlist 350 byte, 50 gerbang NAND). Gas fork 392.515. Circuit id ekspektasi 1.
6. Verifikasi: `circuitInfo(id) == (7,2,0,50)`, `netlist(id)` == input,
   `ownerOf(id) == deployer`, spot-check `eval` (vektor lengkap di `risk_netlist.json`).

**TIDAK ADA eksekusi yang dilakukan dalam investigasi ini** (0 tx, 0 signing).
Semua angka gas/fee di atas dari fork sim + live eth_call; bukan dari tx nyata.

## Jalur UI (alternatif, tidak diperlukan)
Tape-out BISA lewat UI canvas (tapeout.net: gambar circuit → klik "Tape Out"),
tapi TIDAK WAJIB — contract call langsung terbukti jalan (dipakai ViperX di
mainnet 16 Nov + fork sim ini). Jalur kontrak lebih murah/presisi untuk kita
karena netlist sudah jadi + calldata sudah siap. Kalau user lebih pilih UI:
langkahnya = buka tapeout.net → connect wallet (X Layer) → pilih/buat processor
→ gambar/import 50 NAND → klik Tape Out → sign (fee yang sama: 0,0013 OKB +
gas + BEM sudah harus ada). UI TIDAK menghilangkan kebutuhan BEM.

## Netlist (untuk eksekusi)
- Sumber: `circuit/risk_circuit.py` (46 gerbang NAND, depth 15, 256/256).
- Format TAP-02: 7 byte/gerbang (opcode 0x00 + 2× u24 BE). **50 gerbang, 350 byte**
  — +4 gerbang double-inversi agar output (hold, caution) jadi 2 sinyal TERAKHIR,
  syarat TAP-02 (output = sinyal terakhir). Verifikasi exhaustif 256/256 vs
  `risk_circuit.reference()` — file `risk_netlist.json` / `risk_netlist.bin`.
- nIn=7 (a..g), nOut=2 (hold, caution), nState=0 (kombinasional, tanpa LATCH).

## Sumber yang dipakai
- Skill: **hackathon-triage** (custom skill, tidak ada nomor versi di file).
- On-chain live (X Layer mainnet, blok ~76.916.000): factory/market/BEM/transistors
  reads — log `live_*.log`, `processors.json` (455 processor).
- ViperX (preseden mainnet 16 Nov, repo publik MIT ritesh59697/ViperX):
  `ITapeOut.sol`, `TapeOutSpike.fork.t.sol`, `TapeOutRiskCircuits.s.sol`,
  `TAPEOUT_MAINNET_RUNBOOK.md`, `gen_comparator.py`, `tap02_reference.py`,
  `TAPEOUT_HACKATHON.md` — file di `viperx/`.
- TapeKit repo (TapeOutProtocol/TapeKit): SPEC.md App. B + `kernel/src/config.js`
  — hanya berisi interface read-only factory + DeWEB; fungsi tape-out TIDAK ada
  di sana (tape-out hidup di processor contract, bukan factory).
- OKLink API `verify-contract-info`: factory proxy terverifikasi (OZ Proxy.sol);
  implementation `0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a` TIDAK terverifikasi
  (juga di BSC/Base) — ABI direkonstruksi dari bytecode (dispatcher, 31 selector)
  + disilangkan dengan interface ViperX (selector cocok: createCPU 0x47f9b5fd,
  bem 0x8765cf7b, deployFee 0xeb2a5d2c, cpuCount 0xa94da8a7, cpuAt 0x4bc7cbbd).
- Harga live 26 Nov: OKB $82,10 + BNB $554,30 (OKX ticker); BEM $7,71 (DexScreener).
- Dokumen panduan: tapeout beginner's guide (PANews/HTX) — alur mint NAND →
  canvas → burn → Circuit NFT; konsisten dengan temuan on-chain.

## Yang sempat buntu / catatan
- OKX explorer 403 di `browser.open` (diketahui); diatasi via OKLink API + RPC.
- RPC X Layer sempat timeout total ~10 menit (semua endpoint, termasuk drpc/thirdweb),
  lalu pulih sendiri — live reads diulang setelah pulih; angka di atas dari blok
  76.916.084+.
- GitHub API rate-limit (IP egress bersama) saat ambil 2 file kecil ViperX —
  diatasi via raw.githubusercontent.com.
- `forge` 1.9.0 di VM ini TIDAK mengenal cheatcode `deal` ERC20 (selector
  0x6bce989b/0x97754ae9 "unknown cheatcode") — sim didanai via `vm.store`
  ke slot balances BEM (slot 5, diverifikasi live dari protocolWallet).
- 4byte.directory hanya mengenali sebagian selector factory (seal, isSealed,
  protocolWallet, upgradeTo, dsb.); sisanya diidentifikasi via interface ViperX
  + pembuktian live (eth_call sukses + nilai konsisten dengan dossier ViperX).
- Processor ViperX (cpu 424) supplyCap 158/158 MINTED PENUH — tidak bisa dipakai
  untuk circuit kita; kita buat processor sendiri (itulah yang disimulasikan).
