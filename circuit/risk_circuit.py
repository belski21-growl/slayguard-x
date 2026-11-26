"""SlayGuard X — Risk Circuit: aturan verdict audit sebagai netlist NAND-only.

Gaya TapeOut: komputasi apa pun bisa dibangun dari gerbang NAND. Circuit ini
meng-encode aturan inti SlayGuard (dari analyzer.py) sebagai logika Boolean
murni, sehingga verdict GO/CAUTION/HOLD bisa diverifikasi on-chain lewat
sebuah TapeOut circuit — bukan cuma dihitung off-chain.

Input (8 flag Boolean dari hasil audit off-chain):
  a = is_eoa        (alamat tanpa bytecode — bukan kontrak)
  b = proxy_upgrade (selector upgradeTo ada di bytecode — logika bisa diganti)
  c = supply_ge_99  (totalSupply >= 99% maxSupply)
  d = owner_withdraw, e = owner_pause, f = owner_set_uri, g = open_mint
      (4 flag "owner-power / mint terbuka" level medium)

Logika referensi:
  med_ge1 = d | e | f | g
  med_ge3 = mayoritas >=3 dari {d,e,f,g}
  HOLD    = a | b | c | med_ge3
  CAUTION = (bukan HOLD) & med_ge1
  GO      = (bukan HOLD) & (bukan med_ge1)
Output: 2 bit (hold, caution); GO = (0, 0).

Implementasi: SEMUA gerbang adalah NAND 2-input. NOT/AND/OR dibangun dari
NAND. Netlist dievaluasi secara simulasi, dan verify_exhaustive() membuktikan
netlist == logika referensi untuk SEMUA 256 kombinasi input (pola yang sama
dengan yang dipakai ViperX: risk circuit diverifikasi terhadap semua input
sebelum tape-out).

Tape-out ke factory TapeOut di X Layer mainnet (factory hanya ada di mainnet)
adalah langkah terpisah yang butuh biaya mainnet + ABI factory — BELUM
dilakukan; netlist + bukti verifikasi ini adalah artefak yang disubmit.
"""
import json

INPUTS = ["a", "b", "c", "d", "e", "f", "g"]
OUTPUTS = ["hold", "caution"]


def reference(inputs):
    """Logika referensi (Python polos). inputs: dict nama -> 0/1."""
    a, b, c = inputs["a"], inputs["b"], inputs["c"]
    d, e, f, g = inputs["d"], inputs["e"], inputs["f"], inputs["g"]
    med = [d, e, f, g]
    med_ge1 = 1 if any(med) else 0
    med_ge3 = 1 if sum(med) >= 3 else 0
    hold = 1 if (a or b or c or med_ge3) else 0
    caution = 1 if (not hold and med_ge1) else 0
    return {"hold": hold, "caution": caution}


class Netlist:
    """Netlist NAND-only. gates: list (out, in1, in2); semua gerbang NAND."""

    def __init__(self):
        self.gates = []          # (out, in1, in2)
        self.n = 0

    def _wire(self, prefix):
        self.n += 1
        return f"{prefix}{self.n}"

    def nand(self, x, y):
        w = self._wire("n")
        self.gates.append((w, x, y))
        return w

    def not_(self, x):
        return self.nand(x, x)

    def and_(self, x, y):
        return self.not_(self.nand(x, y))

    def or_(self, x, y):
        return self.nand(self.not_(x), self.not_(y))

    def or4(self, w, x, y, z):
        return self.or_(self.or_(w, x), self.or_(y, z))

    def and3(self, x, y, z):
        return self.and_(self.and_(x, y), z)

    def evaluate(self, inputs):
        vals = dict(inputs)
        for out, i1, i2 in self.gates:
            vals[out] = 0 if (vals[i1] and vals[i2]) else 1  # NAND
        return vals

    def depth(self):
        """Kedalaman gerbang terpanjang (level logika)."""
        lvl = {name: 0 for name in INPUTS}
        for out, i1, i2 in self.gates:
            lvl[out] = max(lvl[i1], lvl[i2]) + 1
        return max(lvl.values())


def build_netlist():
    """Bangun netlist NAND-only untuk logika referensi. Return (netlist, out_wires)."""
    nl = Netlist()
    a, b, c, d, e, f, g = INPUTS
    med_ge1 = nl.or4(d, e, f, g)
    # med_ge3 = (d&e&f)|(d&e&g)|(d&f&g)|(e&f&g)
    m1 = nl.and3(d, e, f)
    m2 = nl.and3(d, e, g)
    m3 = nl.and3(d, f, g)
    m4 = nl.and3(e, f, g)
    med_ge3 = nl.or4(m1, m2, m3, m4)
    hold = nl.or4(a, b, c, med_ge3)
    not_hold = nl.not_(hold)
    caution = nl.and_(not_hold, med_ge1)
    return nl, {"hold": hold, "caution": caution}


def verify_exhaustive():
    """Cek netlist vs referensi untuk semua 256 kombinasi input.

    Return (ok, checked, gate_count, depth, failures).
    """
    nl, outs = build_netlist()
    failures = []
    for combo in range(256):
        inputs = {name: (combo >> i) & 1 for i, name in enumerate(INPUTS)}
        vals = nl.evaluate(inputs)
        got = {k: vals[w] for k, w in outs.items()}
        want = reference(inputs)
        if got != want:
            failures.append((inputs, got, want))
    return (not failures, 256, len(nl.gates), nl.depth(), failures)


def netlist_json():
    """Serialisasi netlist + metadata (artefak submit)."""
    nl, outs = build_netlist()
    ok, checked, n_gates, depth, _ = verify_exhaustive()
    return {
        "name": "SlayGuard Risk Circuit v1",
        "inputs": INPUTS,
        "outputs": OUTPUTS,
        "gates_nand": [{"out": o, "a": i1, "b": i2} for o, i1, i2 in nl.gates],
        "gate_count": n_gates,
        "depth": depth,
        "output_wires": outs,
        "verified_exhaustive_inputs": checked,
        "verified_ok": ok,
        "note": "Semua gerbang NAND 2-input. Tape-out ke TapeOut factory "
                "X Layer mainnet masih menunggu biaya + ABI factory.",
    }


if __name__ == "__main__":
    ok, checked, n_gates, depth, failures = verify_exhaustive()
    print(f"exhaustive: {checked} kombinasi, ok={ok}, "
          f"gates NAND={n_gates}, depth={depth}")
    if failures:
        print(f"FAILURES: {failures[:3]}")
        raise SystemExit(1)
    data = netlist_json()
    print(json.dumps({k: v for k, v in data.items() if k != "gates_nand"},
                     indent=2))
