#!/usr/bin/env python3
"""Splice take 1 (demo.*) and take 2 (retry.*) into combined.*.

Take 1: sections 1-7, but 2/3/5 failed (X Layer RPC egress flapped:
audit + tapeout returned error JSON, registry read timed out).
Take 2: sections 2, 3, 5 re-recorded clean (CAUTION 65 live).
Combined: 1 (take 1) + 2-3 (take 2) + 4 (take 1) + 5 (take 2) + 6-7 (take 1).
Timing files are (delay, bytes) per chunk; cuts are byte-exact.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def read_capture(ts_path, timing_path):
    with open(ts_path, "rb") as f:
        raw = f.read()
    chunks = []  # (delay, bytes)
    with open(timing_path) as f:
        for line in f:
            p = line.split()
            if len(p) == 2:
                chunks.append((float(p[0]), int(p[1])))
    # `script` writes a header ("Script started on ...") and a footer
    # ("Script done on ...") that the timing log does not cover; strip both.
    if raw.startswith(b"Script started on"):
        nl = raw.find(b"\n")
        raw = raw[nl + 1:]
    footer = raw.find(b"\nScript done on")
    if footer >= 0:
        raw = raw[:footer]
    assert sum(n for _, n in chunks) == len(raw), (
        f"timing bytes {sum(n for _, n in chunks)} != typescript {len(raw)}")
    return raw, chunks


def split_at(raw, chunks, marker):
    """Split (raw, chunks) at the first byte offset of marker."""
    idx = raw.find(marker.encode())
    assert idx >= 0, f"marker not found: {marker}"
    a_chunks, b_chunks = [], []
    pos = 0
    for delay, n in chunks:
        end = pos + n
        if end <= idx:
            a_chunks.append((delay, n))
        elif pos >= idx:
            b_chunks.append((delay, n))
        else:  # straddles the cut
            a_chunks.append((delay, idx - pos))
            b_chunks.append((0.0, end - idx))
        pos = end
    return (raw[:idx], a_chunks), (raw[idx:], b_chunks)


def write_capture(ts_path, timing_path, raw, chunks):
    with open(ts_path, "wb") as f:
        f.write(raw)
    with open(timing_path, "w") as f:
        for delay, n in chunks:
            f.write(f"{delay} {n}\n")


def main():
    raw1, ch1 = read_capture(os.path.join(HERE, "demo.typescript"),
                             os.path.join(HERE, "demo.timing"))
    raw2, ch2 = read_capture(os.path.join(HERE, "retry.typescript"),
                             os.path.join(HERE, "retry.timing"))
    # A = take1 §1 | B = take2 §2-3 | C = take1 §4 | D = take2 §5 | E = take1 §6-7
    (a_raw, a_ch), (rest1_raw, rest1_ch) = split_at(raw1, ch1, "### 2 - LIVE AUDIT")
    (b_raw, b_ch), (_, _) = split_at(raw2, ch2, "### 5 - REGISTRY")
    (c_raw, c_ch), (e_raw, e_ch) = split_at(rest1_raw, rest1_ch, "### 5 - REGISTRY")
    # c currently starts at §2 of take1; cut it down to start at §4
    (_, _), (c_raw, c_ch) = split_at(c_raw, c_ch, "### 4 - RISK CIRCUIT")
    # e currently starts at §5 of take1; cut it down to start at §6
    (_, _), (e_raw, e_ch) = split_at(e_raw, e_ch, "### 6 - WHO PAYS")
    # d = take2 §5 to end
    (_, _), (d_raw, d_ch) = split_at(raw2, ch2, "### 5 - REGISTRY")
    combined_raw = a_raw + b_raw + c_raw + d_raw + e_raw
    combined_ch = a_ch + b_ch + c_ch + d_ch + e_ch
    assert sum(n for _, n in combined_ch) == len(combined_raw)
    assert b"hsurr:" not in combined_raw, "credential leak in combined capture!"
    assert b"0x8F3E972f8006aE76D55385cF9Df8bF86160983AA" not in combined_raw
    assert b"Traceback" not in combined_raw, "traceback leaked into combined capture!"
    assert b"verdict: null" not in combined_raw, "failed audit leaked into combined!"
    write_capture(os.path.join(HERE, "combined.typescript"),
                  os.path.join(HERE, "combined.timing"),
                  combined_raw, combined_ch)
    total = sum(d for d, _ in combined_ch)
    print(f"combined: {len(combined_raw)} bytes, {len(combined_ch)} chunks, {total:.1f}s raw timing")
    for name, ch in [("A §1", a_ch), ("B §2-3", b_ch), ("C §4", c_ch),
                     ("D §5", d_ch), ("E §6-7", e_ch)]:
        print(f"  {name}: {sum(d for d, _ in ch):.1f}s")


if __name__ == "__main__":
    main()
