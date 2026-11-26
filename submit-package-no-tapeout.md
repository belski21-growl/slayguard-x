# OKX Build X — Paket Submit OPSI TANPA TAPE-OUT (draft form)
**Status:** DRAFT — siap isi ke form submit begitu user tonton video + OK dan video ter-upload ke YouTube.
**Dibuat:** 26 Nov 2026 ~18:20 WIB. **Tape-out: BELUM dieksekusi (HOLD user 26 Nov ~16:40).**
**Video opsi ini:** `video/slayguard-x-demo-no-tapeout.mp4` — 97,3 dtk, 1920x1080, h264+AAC, 1.613.042 byte (terverifikasi 26 Nov ~18:15: frame dicek 2/30/92/95 dtk, VO hadir 8/8 jendela, leak scan bersih).
**Deadline submit:** 7 Des 23:59 UTC = 8 Des 06:59 WIB (provisional, halaman resmi).

## 1. Deskripsi produk (isi form — dari README, tanpa angka baru)
SlayGuard X adalah alat audit kontrak EVM untuk orang awam, diadaptasi ke X Layer + TapeOut. Satu klik mint/approve yang salah bisa menguras wallet, tapi kebanyakan orang tidak bisa membaca kontrak — SlayGuard X mengubah workflow audit internal tim menjadi produk publik: mesin heuristik membaca bytecode + state on-chain (tanpa private key, tanpa gas), LLM menerjemahkan temuan ke bahasa manusia, panel TapeOut live menampilkan factory + market X Layer mainnet, Risk Circuit NAND meng-encode aturan verdict sehingga verdict bisa dihitung on-chain ala TapeOut (bukan cuma klaim off-chain), dan SlayGuardRegistry mencatat tiap verdict di X Layer mainnet supaya bisa dicek siapa pun.

## 2. Target user + cara menjangkau
- **Target:** pengguna X Layer sehari-hari (pemegang OKX Wallet, pengguna mint/DeFi di X Layer) yang tidak bisa membaca kontrak dan selama ini klik buta.
- **Cara menjangkau:** distribusi lewat ekosistem OKX/X Layer (OKX Wallet, komunitas X Layer), integrasi B2B ke wallet dan marketplace X Layer, dan repo publik + video demo.

## 3. Revenue model (freemium — dari README)
Audit gratis untuk semua orang. Yang berbayar: laporan Pro (detail), API berbayar, dan integrasi B2B untuk wallet/marketplace X Layer.

## 4. Alamat + link relevan (semua live, terverifikasi 26 Nov 2026)
| Item | Nilai |
|---|---|
| SlayGuardRegistry — X Layer mainnet (chain 196) | `0x55b9460db2a22a9fA70A8cBe2c665804167A42e5` |
| Registry deploy tx (blok 76.914.634, gas 680.947) | `0xcd3a368aed28410d1ea6f93a22266b87736e7aa60542616321c25f17066f969f` |
| recordAudit E2E (CAUTION 65, blok 76.914.661) | `0xa9f9822dea838ced90e9c4cd5690ae633ebe20eea4b04bfbe54e4e9b05e26d4d` |
| Registry — X Layer testnet (chain 1952, alamat sama) | `0x55b9460db2a22a9fA70A8cBe2c665804167A42e5` |
| TapeOut factory (mainnet) | `0x1f09daefa827f02cbb40967cc91b259763760761` |
| TapeOut factory implementation (yang diaudit, EIP-1967 proxy) | `0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a` |
| TapeOut market (mainnet) | `0xd89f358c48a7B632c9845af2a02A32eB90DD75DB` |
| Repo GitHub (public, main) | https://github.com/belski21-growl/slayguard-x |
| Video demo (≤3 menit) | [LINK YOUTUBE — isi setelah user upload] — file lokal: `video/slayguard-x-demo-no-tapeout.mp4` |
| Akses demo (app) | Repo README: `python3 app.py` → http://127.0.0.1:8765 (endpoint `/api/audit`, `/api/tapeout`, `/api/circuit`, `/api/gasprice`) |

## 5. Fitur TapeOut yang dipakai (penjelasan untuk form — syarat "circuits ATAU contracts ATAU onchain data")
SlayGuard X adalah website/app/tool — bukan proyek circuit murni — jadi yang dipakai:
1. **TapeOut contracts + onchain data (LIVE):** app membaca factory + market TapeOut di X Layer mainnet secara live dan read-only (`/api/tapeout`, fungsi `tapeout_status()` di `analyzer.py`) — status factory/market + gas price tampil di panel produk. Interface/komputasi boleh off-chain (FAQ resmi), asal dijelaskan bagian mana yang pakai TapeOut — bagian ini.
2. **Risk Circuit (netlist, belum tape-out):** aturan verdict di-encode sebagai circuit NAND — 46 gerbang, depth 15, terverifikasi exhaustif 256/256 kombinasi input (`circuit/risk_circuit.py`, `tapeout/risk_netlist.json` + `.bin`, format TAP-02: 50 gerbang, 350 byte, nIn 7, nOut 2). Video mendemonstrasikan circuit ini dan VO menyebut verdict "computable on-chain" — TANPA klaim tape-out sudah jalan.
3. **Kontrak sendiri di X Layer:** SlayGuardRegistry (di atas) mencatat verdict on-chain.

## 6. Catatan jujur — status tape-out (tulis apa adanya di form)
- **Circuit ID: BELUM ADA — tape-out belum dieksekusi.** Processor contract juga belum dibuat. Yang diserahkan sebagai bukti circuit: netlist TAP-02 + verifier exhaustif 256/256 di repo (bukan klaim on-chain).
- Alasan: tape-out butuh 0,11 BEM di wallet deployer di X Layer (biaya total ~$0,96; kaki OKB sudah cukup) dan pendanaan BEM sedang ditahan atas keputusan user. Rencana tape-out lengkap + calldata sudah siap di `tapeout/COST_REPORT.md` — bisa dieksekusi kapan saja sebelum deadline begitu hold dicabut (lihat `submit-package-tapeout-checklist.md`).
- Ini sesuai fallback yang sudah dicatat di README: "circuit ID (setelah tape-out — atau netlist + bukti verifikasi bila tape-out tertunda)".

## 7. Yang baru selama event (substantial new development — dari README)
Semua dikerjakan 25–26 Nov 2026, dalam periode event:
1. Chain baru: X Layer mainnet (196) + testnet (1952).
2. Integrasi TapeOut onchain data (baca live factory + market mainnet).
3. Risk Circuit NAND baru (46 gerbang, depth 15, 256/256).
4. SlayGuardRegistry (kontrak Solidity baru) + deploy mainnet + testnet.
5. Endpoint + UI baru: `/api/tapeout`, `/api/circuit`, `/api/gasprice`.
Yang dipakai ulang dari SlayGuard asli: mesin heuristik analyzer + server + UI dasar (fondasi, bukan entry-nya).

## 8. Bukti tes (dari README + live 26 Nov)
- `forge test`: 5/5 PASS (kontrak). `python3 -m unittest discover -s tests`: 11/11 PASS.
- E2E lokal: PASS. E2E live mainnet: deploy + recordAudit + read-back PASS (CAUTION 65, findingsHash cocok).
- Live audit contoh: implementasi factory TapeOut → CAUTION 65/100 (upgradeTo −25, owner withdraw −10).

## 9. Sisa sebelum submit (checklist singkat)
- [ ] User tonton video opsi ini + OK.
- [ ] User upload video ke YouTube → isi link di §4.
- [ ] Isi form submit OKX dengan draft di atas (tangan user/parent — JANGAN submit tanpa OK user).
