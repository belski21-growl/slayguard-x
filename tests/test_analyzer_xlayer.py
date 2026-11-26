"""Unit test analyzer X Layer + TapeOut — offline (RPC di-fake).

Jalan: python3 -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyzer  # noqa: E402

# Bytecode fixture: mengandung selector owner(), upgradeTo, mint, maxSupply.
FAKE_CODE = ("0x6080604052" + "8da5cb5b" + "3659cfe6" + "40c10f19"
             + "d5abeb01" + "00" * 100)
EOA_CODE = "0x"


def fake_rpc(chain, method, params, timeout=15):
    if method == "eth_chainId":
        return "0xc4" if chain == "xlayer" else "0x7a0"  # 196 / 1952
    if method == "eth_blockNumber":
        return "0x123456"
    if method == "eth_getCode":
        addr = params[0].lower()
        if addr in (analyzer.TAPEOUT_FACTORY.lower(),
                    analyzer.TAPEOUT_MARKET.lower()):
            return "0x" + "60" * 5000  # factory/market hidup
        if addr == "0x" + "11" * 20:
            return FAKE_CODE
        return EOA_CODE
    if method == "eth_getStorageAt":
        return "0x" + "00" * 12 + "22" * 20  # impl dummy
    if method == "eth_call":
        data = params[0]["data"]
        if data.endswith("8da5cb5b"):  # owner()
            return "0x" + "00" * 12 + "33" * 20
        if data.endswith("18160ddd"):  # totalSupply()
            return "0x" + "00" * 31 + "64"  # 100
        if data.endswith("d5abeb01"):  # maxSupply()
            return "0x" + "00" * 31 + "64"  # 100 -> 100% minted
        return "0x" + "00" * 32
    if method == "eth_gasPrice":
        return "0x3b9aca00"  # 1 gwei
    raise AssertionError(f"method tak terduga: {method}")


class TestXLayer(unittest.TestCase):
    def test_chains_registered(self):
        self.assertIn("xlayer", analyzer.RPCS)
        self.assertIn("xlayer-testnet", analyzer.RPCS)
        self.assertEqual(analyzer.RPCS["xlayer"],
                         ["https://rpc.xlayer.tech"])
        self.assertEqual(analyzer.RPCS["xlayer-testnet"],
                         ["https://testrpc.xlayer.tech/terigon"])

    @patch.object(analyzer, "rpc_call", side_effect=fake_rpc)
    def test_tapeout_status_live(self, _):
        st = analyzer.tapeout_status("xlayer")
        self.assertEqual(st["chain_id"], 196)
        self.assertTrue(st["factory_live"])
        self.assertTrue(st["market_live"])
        self.assertEqual(st["factory_code_bytes"], 5000)
        self.assertIn("factory_implementation", st)

    @patch.object(analyzer, "rpc_call", side_effect=fake_rpc)
    def test_tapeout_status_testnet_chainid(self, _):
        st = analyzer.tapeout_status("xlayer-testnet")
        self.assertEqual(st["chain_id"], 1952)

    @patch.object(analyzer, "rpc_call", side_effect=fake_rpc)
    def test_gas_price(self, _):
        self.assertAlmostEqual(analyzer.gas_price_gwei("xlayer"), 1.0)

    @patch.object(analyzer, "rpc_call", side_effect=fake_rpc)
    def test_analyze_xlayer_risky_contract(self, _):
        # upgradeTo + 100% minted -> HOLD
        res = analyzer.analyze("0x" + "11" * 20, "xlayer")
        self.assertEqual(res["verdict"], "HOLD")
        self.assertEqual(res["chain"], "xlayer")

    @patch.object(analyzer, "rpc_call", side_effect=fake_rpc)
    def test_analyze_xlayer_eoa(self, _):
        res = analyzer.analyze("0x" + "22" * 20, "xlayer")
        self.assertEqual(res["verdict"], "HOLD")
        self.assertEqual(res["score"], 0)

    def test_analyze_bad_chain(self):
        with self.assertRaises(ValueError):
            analyzer.analyze("0x" + "11" * 20, "solana")


if __name__ == "__main__":
    unittest.main()
