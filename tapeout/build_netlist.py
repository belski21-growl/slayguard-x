"""Build the TAP-02 netlist bytes for the SlayGuard Risk Circuit.

Reads circuit/risk_circuit.py (the verified 46-gate NAND netlist), maps its
wires onto TAP-02 signal numbering (0=CONST0, 1=CONST1, inputs 2..8, gate i
output 2+7+i), and appends double-inversion gates so the two outputs
(hold, caution) are the LAST two signals, as TAP-02 requires (outputs =
last nOut signals; cf. ViperX gen_comparator.py: "Output must be an
element-produced signal and the last one").

Encoder written from the TAP-02 spec as vendored in ViperX's
tap02_reference.py (read in full, MIT): one element = opcode 0x00 (NAND)
+ input A as u24 big-endian + input B as u24 big-endian = 7 bytes/gate.
No external code is imported; the evaluator below is implemented here too
and cross-checked exhaustively (256/256) against risk_circuit.reference().

Outputs (all files under tapeout/):
  risk_netlist.json  - netlist bytes (hex), nIn=7, nOut=2, gates, expected eval bytes
  risk_netlist.bin   - raw netlist bytes
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "circuit"))

from risk_circuit import build_netlist, reference, INPUTS  # noqa: E402

N_IN = 7
N_OUT = 2


def tap02_signal(name, gate_index):
    """Map a risk_circuit wire name to a TAP-02 signal index."""
    if name in INPUTS:
        return 2 + INPUTS.index(name)
    if name.startswith("n"):
        k = int(name[1:])
        return 2 + N_IN + (k - 1)
    raise ValueError(f"unknown wire {name}")


def build_tap02_elements():
    nl, outs = build_netlist()
    # gates: list of (out_wire, in1, in2) in emission order
    elements = []  # (a_sig, b_sig) per gate, in order
    wire_to_gate = {}
    for i, (o, i1, i2) in enumerate(nl.gates):
        wire_to_gate[o] = i
        elements.append((tap02_signal(i1, i), tap02_signal(i2, i)))
    # Append double-inversion so hold & caution are the last two signals.
    # hold2 = NOT(NOT(hold)); caution2 = NOT(NOT(caution)).
    hold_sig = tap02_signal(outs["hold"], None)
    caution_sig = tap02_signal(outs["caution"], None)
    n_base = 2 + N_IN + len(elements)  # first new gate's output signal
    # Both single inversions first, then both double-inversions, so the
    # LAST two gate outputs are hold2 (n_base+2) and caution2 (n_base+3).
    elements.append((hold_sig, hold_sig))        # NOT(hold) -> n_base
    elements.append((caution_sig, caution_sig))  # NOT(caution) -> n_base+1
    elements.append((n_base, n_base))            # hold2 -> n_base+2
    elements.append((n_base + 1, n_base + 1))    # caution2 -> n_base+3
    return elements, {"hold": n_base + 2, "caution": n_base + 3}


def encode(elements):
    out = bytearray()
    for a, b in elements:
        out.append(0x00)
        out += a.to_bytes(3, "big")
        out += b.to_bytes(3, "big")
    return bytes(out)


def evaluate(elements, inputs):
    """TAP-02 one-beat evaluation (combinational). inputs: 7 bits LSB-first."""
    a = [0, 1] + list(inputs)
    for x, y in elements:
        a.append(1 - (a[x] & a[y]))
    return a[len(a) - N_OUT:]


def main():
    elements, out_sigs = build_tap02_elements()
    netlist = encode(elements)
    n_gates = len(elements)
    print(f"TAP-02 netlist: {n_gates} NAND gates, {len(netlist)} bytes")
    print(f"output signals: hold={out_sigs['hold']}, caution={out_sigs['caution']}")
    assert out_sigs["hold"] == 2 + N_IN + n_gates - 2
    assert out_sigs["caution"] == 2 + N_IN + n_gates - 1
    # Exhaustive cross-check vs the reference logic.
    expected = []
    for combo in range(256):
        inputs = {name: (combo >> i) & 1 for i, name in enumerate(INPUTS)}
        bits = [inputs[n] for n in INPUTS]
        got = evaluate(elements, bits)
        want = reference(inputs)
        assert got == [want["hold"], want["caution"]], (combo, got, want)
        expected.append(got[0] | (got[1] << 1))
    print("exhaustive: 256/256 match risk_circuit.reference()")
    # Packed eval-input / expected-output vectors (LSB-first bit packing, TAP-02 pack()).
    vectors = []
    for combo in range(256):
        vectors.append({"input": combo, "input_byte": combo & 0xFF,
                        "expected_output_byte": expected[combo]})
    data = {
        "name": "SlayGuard Risk Circuit v1",
        "nIn": N_IN,
        "nOut": N_OUT,
        "gates": n_gates,
        "netlist": "0x" + netlist.hex(),
        "netlist_bytes": len(netlist),
        "output_wires_tap02": out_sigs,
        "note": "46 gates from risk_circuit.py + 4 double-inversion gates so "
                "(hold, caution) are the last two TAP-02 signals.",
        "verified_exhaustive_inputs": 256,
        "expected_output_bytes": expected,
        "vectors": vectors,
    }
    (HERE / "risk_netlist.json").write_text(json.dumps(data, indent=2) + "\n")
    (HERE / "risk_netlist.bin").write_bytes(netlist)
    print("wrote risk_netlist.json + risk_netlist.bin")
    print("netlist head:", netlist[:21].hex(), "...")
    print("expected output bytes (256):", bytes(expected).hex())


if __name__ == "__main__":
    main()
