# OKX Build X — Checklist Finalisasi OPSI DENGAN TAPE-OUT
**Prasyarat mutlak:** user mencabut HOLD tape-out (HOLD 26 Nov ~16:40: jangan beli BEM,
jangan bridge, jangan eksekusi). JANGAN jalankan satu pun langkah di bawah selama hold berdiri.
**Deadline submit:** 7 Des 23:59 UTC = 8 Des 06:59 WIB. Estimasi total pasca-hold: **~45–60 menit**
(diluar waktu pendanaan BEM yang di tangan user).

## 0. Pra-syarat pendanaan — tangan user/koordinator (~waktu user, bukan agen)
- [ ] User setuju dana ~$2,00: beli **0,112 BEM di PancakeSwap BSC** (~$0,86) + **bridge LayerZero ke X Layer** (fee ~0,00203 BNB ≈ $1,13 + 0,5%). Runbook: `tapeout/COST_REPORT.md` § "Siap eksekusi?".
- [ ] Verifikasi (read-only): `balanceOf` BEM di X Layer ≥ 11.000.000 base units (0,11 BEM) di wallet deployer.
- [ ] Verifikasi gas X Layer ≤ 0,1 gwei (aturan tahan — kalau >0,1 gwei, TAHAN + lapor user).

## 1. Eksekusi tape-out — 5 tx, calldata sudah siap (~10–15 menit incl. konfirmasi)
Sumber langkah: `tapeout/COST_REPORT.md` § "Siap eksekusi?" + `tapeout/calldata_*.txt`.
- [ ] `BEM.approve(factory, 10.000.000)` — factory `0x1f09DAeFA827f02CBb40967cc91b259763760761`.
- [ ] `createCPU("SlayGuard Risk Circuit","SLAYRISK","SlayGuard X risk circuit: audit verdict rules as NAND netlist.",50,0)` — calldata `calldata_createCPU.txt` (gas fork 739.652). Lalu baca `cpuAt(cpuCount()-1)` → processor baru; catat **PROCESSOR ADDRESS**.
- [ ] `BEM.approve(transistors, 1.000.000)` lalu `mint(0, 50)` — calldata `calldata_mint.txt` (gas fork 190.313). Cek `balanceOf(deployer, 0) == 50`.
- [ ] `tapeout(netlist, 7, 2)` value 0,0013 OKB — calldata `calldata_tapeout.txt` (netlist 350 byte, 50 gerbang; gas fork 392.515). Catat **CIRCUIT ID** yang dikembalikan.
- [ ] JANGAN eksekusi 2 tx bersamaan dari wallet yang sama (aturan BAW serial — berlaku umum: satu per satu, tunggu receipt).

## 2. Verifikasi pasca-tape-out (~5 menit, read-only)
- [ ] `circuitInfo(id) == (7, 2, 0, 50)`.
- [ ] `netlist(id)` == input netlist (bandingkan dengan `tapeout/risk_netlist.bin`).
- [ ] `ownerOf(id) == deployer` (work wallet 0x8F3E…).
- [ ] Spot-check `eval` (vektor lengkap di `tapeout/risk_netlist.json`).
- [ ] Catat: circuit ID + processor address + semua tx hash di status file + paket submit.

## 3. Re-render video varian tape-out (~5 menit)
- [ ] Isi slot di `video/close-card-tapeout-template.md` (CIRCUIT_ID + processor address untuk paket, bukan kartu).
- [ ] Jalankan perintah render EXACT dari template → `frames_tapeout/` (973 frame, 97,3 dtk).
- [ ] Jalankan perintah mux EXACT dari template → `video/slayguard-x-demo-tapeout.mp4` (file BARU).

## 4. Verifikasi video tape-out (~5 menit — standar yang sama dengan varian tanpa tape-out)
- [ ] ffprobe: durasi 97,3 dtk (≤180), 1920x1080, h264 10fps, AAC mono 24 kHz.
- [ ] Ekstrak + lihat frame: title (~2 dtk), audit (~30 dtk), close card (~92 dtk dan ~95 dtk) — pastikan circuit ID tampil benar, tanpa placeholder.
- [ ] Audio: volumedetect per jendela 8 segmen VO (tidak ada segmen senyap).
- [ ] Leak scan: `strings` mp4 — bersih dari `hsurr:`, alamat deployer lengkap, `CIRCUIT_ID_HERE` (placeholder tidak boleh lolos).

## 5. Update paket submit (~10 menit)
- [ ] Salin `submit-package-no-tapeout.md` → `submit-package-tapeout.md`; ganti:
  - §4: tambah processor address + circuit ID + tx tape-out; video → link YouTube varian tape-out.
  - §5: tambah "Risk Circuit SUDAH tape-out on-chain (circuit ID …, processor …)".
  - §6: hapus catatan "belum dieksekusi"; tulis biaya aktual tape-out (OKB + BEM yang benar-benar terpakai).
- [ ] Update status file `~/workspace/web-gigs/hackathon-okx-status.md` dengan hasil tape-out.

## 6. Serah ke user (tangan user/parent — BUKAN agen)
- [ ] User tonton video varian tape-out + OK.
- [ ] User upload video ke YouTube → isi link di paket submit.
- [ ] Isi form submit OKX dengan paket tape-out → submit sebelum 8 Des 06:59 WIB.
- [ ] Keputusan akhir varian mana yang dikirim (dengan / tanpa tape-out) tetap di tangan user — kalau waktu mepet, varian tanpa tape-out sudah siap kirim kapan saja.
