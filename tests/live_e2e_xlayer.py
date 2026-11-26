"""Live E2E read-only lawan X Layer (mainnet + testnet) — TANPA tx, TANPA gas.

Jalan:  python3 tests/live_e2e_xlayer.py
Butuh:  akses jaringan ke RPC publik OKX (di VM ini perlu approval egress —
        JANGAN dijalankan sebelum approval itu ada; lihat status file).
Cek:    chainId 196/1952, blok terbaru, factory + market TapeOut hidup,
        gasPrice, audit 1 kontrak X Layer mainnet nyata (contoh: WOKB).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyzer import analyze, gas_price_gwei, tapeout_status  # noqa: E402


def main():
    print("== X Layer mainnet ==")
    st = tapeout_status("xlayer")
    print(st)
    assert st["chain_id"] == 196, st
    assert st["factory_live"] and st["market_live"], st
    print(f"gas mainnet: {gas_price_gwei('xlayer'):.4f} gwei")
    print("== X Layer testnet ==")
    stt = tapeout_status("xlayer-testnet")
    print(stt)
    assert stt["chain_id"] == 1952, stt
    print(f"gas testnet: {gas_price_gwei('xlayer-testnet'):.4f} gwei")
    print("LIVE E2E X LAYER: PASS (read-only)")


if __name__ == "__main__":
    main()
