"""Unit tests — offline, pakai fixture (tanpa RPC)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import analyzer


def test_invalid_address():
    for bad in ["", "0x123", "not-an-address", "0x" + "zz" * 20]:
        try:
            analyzer.analyze(bad, "bsc")
        except ValueError:
            continue
        raise AssertionError(f"{bad} harus ditolak")


def test_bad_chain():
    try:
        analyzer.analyze("0x" + "ab" * 20, "solana")
    except ValueError:
        return
    raise AssertionError("chain solana harus ditolak")


def test_eoa_returns_hold(monkeypatch):
    monkeypatch.setattr(analyzer, "rpc_call", lambda c, m, p, timeout=15: "0x")
    r = analyzer.analyze("0x" + "11" * 20, "bsc")
    assert r["verdict"] == "HOLD" and r["score"] == 0


def test_clean_contract_scores_high(monkeypatch):
    # bytecode tanpa selector berisiko + owner() + name/symbol/totalSupply kosong
    def fake_rpc(chain, method, params, timeout=15):
        if method == "eth_getCode":
            return "0x608060405234801561001057600080fd5b50" + "00" * 100
        if method == "eth_getStorageAt":
            return "0x" + "00" * 32
        return "0x" + "00" * 32
    monkeypatch.setattr(analyzer, "rpc_call", fake_rpc)
    r = analyzer.analyze("0x" + "22" * 20, "bsc")
    assert r["score"] >= 80 and r["verdict"] == "GO", r


def test_proxy_and_pause_flagged(monkeypatch):
    # bytecode mengandung selector owner(), pause(), upgradeTo()
    body = ("6080604052" + analyzer.SELECTORS["owner()"]
            + analyzer.SELECTORS["pause()"] + analyzer.SELECTORS["upgradeTo(address)"]
            + "00" * 200)

    def fake_rpc(chain, method, params, timeout=15):
        if method == "eth_getCode":
            return "0x" + body
        if method == "eth_getStorageAt":
            return "0x" + "00" * 31 + "01"  # slot nonzero -> proxy
        if method == "eth_call":
            data = params[0]["data"]
            if data.endswith(analyzer.SELECTORS["owner()"]):
                return "0x" + "00" * 12 + "ab" * 20
            return "0x" + "00" * 32
        return "0x"
    monkeypatch.setattr(analyzer, "rpc_call", fake_rpc)
    r = analyzer.analyze("0x" + "33" * 20, "bsc")
    titles = [f["title"] for f in r["findings"]]
    assert any("proxy" in t.lower() for t in titles), titles
    assert any("pause" in t.lower() for t in titles), titles
    assert any("upgrade" in t.lower() for t in titles), titles
    assert r["verdict"] in ("CAUTION", "HOLD"), r
