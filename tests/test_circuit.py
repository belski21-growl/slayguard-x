"""Unit test Risk Circuit — offline, stdlib unittest (tanpa pytest)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "circuit"))
from risk_circuit import (  # noqa: E402
    build_netlist, netlist_json, reference, verify_exhaustive)


class TestRiskCircuit(unittest.TestCase):
    def test_exhaustive_256(self):
        ok, checked, n_gates, depth, failures = verify_exhaustive()
        self.assertTrue(ok, f"failures: {failures[:2]}")
        self.assertEqual(checked, 256)
        self.assertGreater(n_gates, 0)
        self.assertLess(depth, 64)

    def test_reference_spot(self):
        z = {k: 0 for k in "abcdefg"}
        self.assertEqual(reference(z), {"hold": 0, "caution": 0})  # GO
        self.assertEqual(reference({**z, "a": 1}), {"hold": 1, "caution": 0})
        self.assertEqual(reference({**z, "b": 1}), {"hold": 1, "caution": 0})
        self.assertEqual(reference({**z, "d": 1}), {"hold": 0, "caution": 1})
        self.assertEqual(reference({**z, "d": 1, "e": 1, "f": 1}),
                           {"hold": 1, "caution": 0})  # med>=3 -> HOLD
        self.assertEqual(reference({**z, "d": 1, "e": 1}),
                           {"hold": 0, "caution": 1})  # 2 med -> CAUTION

    def test_netlist_gates_are_nand_only(self):
        data = netlist_json()
        self.assertTrue(data["verified_ok"])
        self.assertEqual(data["verified_exhaustive_inputs"], 256)
        for g in data["gates_nand"]:
            self.assertIn("out", g)
            self.assertIn("a", g)
            self.assertIn("b", g)
        self.assertEqual(len(data["gates_nand"]), data["gate_count"])

    def test_netlist_matches_reference_on_samples(self):
        nl, outs = build_netlist()
        for combo in (0, 1, 0b0001000, 0b1111000, 0xFF, 0b0101010):
            inputs = {n: (combo >> i) & 1 for i, n in enumerate("abcdefg")}
            vals = nl.evaluate(inputs)
            got = {k: vals[w] for k, w in outs.items()}
            self.assertEqual(got, reference(inputs), f"combo {combo:08b}")


if __name__ == "__main__":
    unittest.main()
