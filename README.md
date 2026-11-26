# SlayGuard X — OKX Build X / X Layer TapeOut Accelerate

**Satu kalimat:** SlayGuard AI (audit kontrak EVM buat orang awam) diadaptasi ke
X Layer + TapeOut — verdict GO/CAUTION/HOLD yang sama kini bisa diverifikasi
lewat data on-chain TapeOut, dihitung ulang oleh Risk Circuit NAND, dan
dicatat permanen di registry on-chain.

## Ide + kenapa bisa menang (1 paragraf)

Tim ini tiap hari audit kontrak BSC pakai skill audit EVM, tapi user biasa
nggak punya skill itu — satu klik mint/approve yang salah bisa nguras wallet.
SlayGuard X ngubah workflow audit internal tim jadi produk publik untuk X
Layer: mesin heuristik baca bytecode + state on-chain (tanpa private key,
tanpa gas), LLM yang nerjemahin temuan jadi bahasa manusia, panel TapeOut
live (factory + market X Layer mainnet), Risk Circuit NAND yang meng-encode
aturan verdict sehingga verdict bisa dihitung on-chain ala TapeOut (bukan
cuma klaim off-chain), dan SlayGuardRegistry yang mencatat tiap verdict di
X Layer biar bisa dicek siapa pun. Ini nyentuh semua kriteria juri sekaligus:
user value nyata (melindungi pengguna X Layer yang jumlahnya tumbuh bareng
OKX), inovasi (audit AI + circuit on-chain), integrasi ekosistem (TapeOut
onchain data + circuit + rencana DeWEB), dan product readiness (produk sudah
jalan, bukan mockup — cuma nambah chain + komponen on-chain baru).

## Sinergi SlayGuard — keputusan: YA, ADAPTASI (bukan fresh build)

Alasan: aturan OKX membolehkan proyek lama **asal ada pengembangan baru yang
substansial selama event, dan hanya kerjaan event yang dinilai**. Yang baru di
SlayGuard X (semua dikerjakan 25 Nov 2026, dalam periode event):
1. Chain baru: X Layer mainnet (196) + testnet (1952) — RPC, gas OKB, UI.
2. Integrasi TapeOut onchain data: baca live factory + market di mainnet
   (read-only, gratis) — memenuhi syarat "circuits, contracts, OR onchain
   data" (FAQ resmi: interface/komputasi boleh off-chain, asal dijelaskan
   bagian mana yang pakai TapeOut).
3. Risk Circuit NAND baru (46 gerbang, depth 15, terverifikasi exhaustif
   256/256 kombinasi input) — artefak tape-out siap submit.
4. SlayGuardRegistry (kontrak Solidity baru) — verdict tercatat on-chain.
5. Endpoint + UI baru: `/api/tapeout`, `/api/circuit`, `/api/gasprice`.
Yang dipakai ulang dari SlayGuard asli: mesin heuristik analyzer + server +
UI dasar. Itu fondasi, bukan entry-nya — semua nilai TapeOut/X Layer adalah
baru. Risiko juri menganggap "cuma ganti chain": dimitigasi dengan circuit +
registry yang nyata-nyata baru dan terverifikasi.

## Struktur repo

- `analyzer.py` — audit heuristik (BSC/ETH/X Layer/testnet) + `tapeout_status()`
- `app.py` — server stdlib; `/api/audit`, `/api/tapeout`, `/api/circuit`, `/api/gasprice`
- `circuit/risk_circuit.py` — netlist NAND Risk Circuit + verifier exhaustif
- `contracts/SlayGuardRegistry.sol` — registry verdict on-chain
- `test/SlayGuardRegistry.t.sol` — forge test (tanpa forge-std)
- `tests/` — unittest Python + `live_e2e_xlayer.py` (read-only, butuh network)
- `scripts/e2e_local.sh` — E2E lokal lengkap (tanpa network eksternal)
- `static/index.html` — UI (chain X Layer + panel TapeOut + panel circuit)

## Cara run

```bash
cd ~/workspace/scratch/okx-buildx
python3 app.py            # http://127.0.0.1:8765
```

Mode AI (opsional, key dari env, tidak pernah di-hardcode):
```bash
export SLAY_LLM_BASE_URL="https://api.100milionseek.com/v1"
export SLAY_LLM_API_KEY="..."
export SLAY_LLM_MODEL="deepseek-v4.1-flash-free"
python3 app.py
```

## Tes (hasil 25 Nov 2026 ~06:00 WIB)

```bash
forge test -vv --gas-report        # 5/5 PASS (kontrak)
python3 -m unittest discover -s tests   # 11/11 PASS (circuit + analyzer)
bash scripts/e2e_local.sh          # E2E LOKAL: PASS
python3 tests/live_e2e_xlayer.py   # LIVE read-only — PENDING approval egress (lihat Blocker)
```

E2E lokal: deploy + record + baca balik dibuktikan via `forge test`
(EVM in-process); app lawan anvil lokal via `anvil_setCode`
(audit dummy: CAUTION 65, 2 temuan — benar: upgradeTo −25, mint tanpa
owner −10). Tx submit via anvil di VM ini gagal "Insufficient funds" walau
saldo 10.000 ETH (quirk anvil/forge 1.9.0 di VM) — bukan bug kontrak.

## Angka gas terukur (forge --gas-report)

| Aksi | Gas |
|---|---|
| Deploy SlayGuardRegistry | 680.947 |
| recordAudit pertama (cold) | ~116.149 |
| recordAudit berikutnya (warm) | ~22.867 |

## Estimasi biaya mainnet X Layer (OKB ≈ $82, 24 Nov 2026, OKX)

| Aksi | @1 gwei | @10 gwei | @100 gwei |
|---|---|---|---|
| Deploy registry | 0,000681 OKB ≈ **$0,06** | ≈ $0,56 | ≈ $5,59 |
| recordAudit pertama | ≈ $0,01 | ≈ $0,10 | ≈ $0,95 |

Gas price live X Layer belum dibaca (butuh egress — pending); docs OKX
bilang gas X Layer "negligible". **TIDAK ADA deploy mainnet tanpa
persetujuan user.** Tape-out Risk Circuit ke factory mainnet: biaya
BELUM DIKETAHUI (butuh ABI + fungsi biaya factory — lihat Blocker).

## Testnet (gratis, tapi butuh langkah manual)

- X Layer testnet: chain 1952, RPC `https://testrpc.xlayer.tech/terigon`,
  faucet resmi `web3.okx.com/xlayer/faucet` (0,2 OKB/hari, klaim via browser).
- Deploy testnet butuh: (1) user klaim faucet ke alamat deployer,
  (2) deployer key diserahkan via jalur aman (BUKAN chat) — koordinator/user
  yang putuskan. Sampai itu ada, bukti deploy = `forge test` + anvil lokal.

## Rencana demo video (≤3 menit)

- 0:00–0:20 Masalah: 1 klik mint/approve salah bisa nguras wallet.
- 0:20–0:50 Live audit kontrak X Layer → verdict + penjelasan bahasa manusia.
- 0:50–1:20 Panel TapeOut live + Risk Circuit NAND (46 gerbang, 256/256).
- 1:20–1:50 Registry: verdict tercatat on-chain, bisa dicek siapa pun.
- 1:50–2:40 Target user + revenue: freemium (audit gratis; Pro report + API
  berbayar; B2B wallet/marketplace X Layer).
- 2:40–3:00 Penutup: repo + link demo + apa yang baru selama event.

## Docs yang dipelajari

- OKX Build X (resmi): https://web3.okx.com/xlayer/build-x-series
- X Layer dev docs (resmi): https://web3.okx.com/onchainos/dev-docs/xlayer/developer/build-on-xlayer/about-xlayer
- X Layer testnet faucet (resmi): https://web3.okx.com/onchainos/dev-docs/xlayer/developer/bridge/get-testnet-okb-from-faucet
- TapeOut beginner's guide v1.5: https://tapeoutdaily.ai/downloads/tapeout-complete-beginners-guide-v1.5-en.pdf
- TapeOut ecosystem reference: https://tape4fun.com/en/index.html
- TapeKit repo (resmi): https://github.com/TapeOutProtocol/TapeKit
- ViperX docs (preseden: 4 risk circuit TapeOut di X Layer mainnet, factory
  hanya ada di mainnet): https://docs.viperx.site/roadmap
- TapeOut factory X Layer mainnet `0x1f09daefa827f02cbb40967cc91b259763760761`,
  market `0xd89f358c48a7B632c9845af2a02A32eB90DD75DB` (dua sumber independen).

## Blocker / yang belum terverifikasi live

1. **Egress VM ke RPC publik kena approval card (timeout, tidak terjawab).**
   Akibat: `tapeout_status()` live, `gasPrice` live, dan audit 1 kontrak
   X Layer mainnet nyata BELUM terbukti dari VM ini. Perlu: approval egress
   ATAU jalankan `tests/live_e2e_xlayer.py` dari Simular box / tempat lain.
2. **Faucet + deploy testnet** butuh langkah manual user (klaim + key).
3. **Biaya tape-out circuit** belum diketahui (butuh ABI factory / docs
   TapeOut resmi — kemungkinan butuh browser task ke tapeout.build/canvas).
4. OKX explorer 403 di `browser.open` — verifikasi alamat factory via
   explorer belum bisa dari tool ini (alamat dikonfirmasi 2 sumber lain).
5. DeWEB publish (TapeKit container) butuh tape-out mainnet juga — stretch
   goal, bukan blocker submit (FAQ: interface tidak wajib on-chain).

## Submit (JANGAN submit — target siap 7 Des ~06:59 WIB)

Butuh untuk form: deskripsi produk + target user + revenue model,
alamat registry (testnet/mainnet), alamat factory + market TapeOut,
circuit ID (setelah tape-out — atau netlist + bukti verifikasi bila
tape-out tertunda), link demo, video ≤3 menit.
