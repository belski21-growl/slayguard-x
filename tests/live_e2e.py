"""Live E2E — lawan RPC publik (BSC + ETH). Butuh internet, tanpa key.
Jalankan: python3 tests/live_e2e.py
Ekspektasi: WBNB (BSC) = kontrak beneran, skor tinggi; EOA = HOLD skor 0;
alamat sampah = error validasi; USDC (ETH) = kontrak beneran.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer import analyze  # noqa: E402

CASES = [
    ("WBNB di BSC (kontrak dikenal)", "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c", "bsc", "GO"),
    ("EOA di BSC (burn address, bukan kontrak)", "0x000000000000000000000000000000000000dEaD", "bsc", "HOLD"),
    ("USDC di ETH (kontrak dikenal)", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "eth", None),
]

fails = 0
for label, addr, chain, expect in CASES:
    try:
        r = analyze(addr, chain)
        ok = (expect is None) or (r["verdict"] == expect)
        print(f"[{'PASS' if ok else 'FAIL'}] {label}: verdict={r['verdict']} "
              f"skor={r['score']} meta={r['meta']} temuan={len(r['findings'])}")
        if not ok:
            fails += 1
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] {label}: {type(e).__name__}: {e}")
        fails += 1

try:
    analyze("0x123", "bsc")
    print("[FAIL] alamat invalid tidak ditolak")
    fails += 1
except ValueError as e:
    print(f"[PASS] alamat invalid ditolak: {e}")

print("E2E:", "SEMUA PASS" if fails == 0 else f"{fails} GAGAL")
sys.exit(1 if fails else 0)
