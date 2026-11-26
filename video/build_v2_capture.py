#!/usr/bin/env python3
"""Build combined-v2.typescript/.timing: same chunks/delays as v1, but with
all on-screen Indonesian strings translated to natural English.
Only chunks 3 (§2 audit output) and 9 (§4 exhaustive line) change.
"""
import re

HERE = "."
raw = open("combined.typescript", "rb").read()
chunks = []
for line in open("combined.timing"):
    d, n = line.split()
    chunks.append((float(d), int(n)))
assert sum(n for _, n in chunks) == len(raw)

# split into chunk texts (decoded)
texts = []
off = 0
for d, n in chunks:
    texts.append(raw[off:off+n].decode("utf-8"))
    off += n

REPLACEMENTS = [
    ("Ownership sudah renounced", "Ownership already renounced"),
    ("Owner bisa tarik dana dari kontrak", "Owner can withdraw funds from the contract"),
    ("Proxy bisa di-upgrade — logika bisa diganti total",
     "Proxy can be upgraded — logic can be replaced entirely"),
    ("plain language: Skor 65/100 — ada 3 temuan. Masih bisa interaksi, tapi baca dulu temuan di bawah dan jangan approve tanpa batas. Aksi: cek owner & fungsi berbahaya di atas; kalau owner tidak dikenal, jangan lanjut.",
     "plain language: Score 65/100 — 3 findings. You can still interact, but read the findings below first and never approve without limits. Action: check the owner & dangerous functions above; if the owner is unknown, stop here."),
    ("exhaustive: 256 kombinasi, ok=True, gates NAND=46, depth=15",
     "exhaustive: 256 combinations, ok=True, gates NAND=46, depth=15"),
]

new_texts = []
for t in texts:
    for old, new in REPLACEMENTS:
        assert old in t or True  # replacements may span chunks? no — verify below
        t = t.replace(old, new)
    new_texts.append(t)

# verify every old string is gone and every new string present
joined = "".join(new_texts)
for old, new in REPLACEMENTS:
    assert old not in joined, f"OLD STILL PRESENT: {old}"
    assert new in joined, f"NEW MISSING: {new}"

# Indonesian word scan on the whole v2 capture
ID_WORDS = ["sudah", "bisa", "temuan", "jangan", "cek", "berbahaya", "kombinasi",
            "tarik", "dana", "kontrak", "logika", "diganti", "skor", "ada",
            "interaksi", "tapi", "baca", "dulu", "bawah", "tanpa", "batas",
            "aksi", "atas", "kalau", "tidak", "dikenal", "lanjut", "renounced"]
# note: 'renounced' is English; kept out. 'bisa' etc must be gone.
for w in ["sudah", "temuan", "kombinasi", "tarik", "skor", "cek", "bisa"]:
    assert not re.search(rf"\b{w}\b", joined, re.IGNORECASE), f"ID WORD LEFT: {w}"

out = "".join(new_texts).encode("utf-8")
open("combined-v2.typescript", "wb").write(out)
with open("combined-v2.timing", "w") as f:
    for (d, _n), t in zip(chunks, new_texts):
        f.write(f"{d} {len(t.encode('utf-8'))}\n")
print(f"v2 capture: {len(out)} bytes (v1: {len(raw)}), {len(chunks)} chunks")
print(f"total delay: {sum(d for d, _ in chunks):.1f}s (same as v1)")
for i, (t, nt) in enumerate(zip(texts, new_texts)):
    if t != nt:
        print(f"chunk {i} changed: {len(t.encode())} -> {len(nt.encode())} bytes")
