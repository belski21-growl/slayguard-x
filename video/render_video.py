#!/usr/bin/env python3
"""Render the SlayGuard X demo video from combined.typescript/combined.timing.

Adapted from the Telegraph Listings Desk renderer (proven pattern):
- Replays the `script` typescript+timing capture as a terminal at 10 fps.
- Injects the canonical `$ <command>` line after each `### N -` section header
  (the driver does not echo commands, so the video shows them this way).
- Title card up front, close card at the end.
- EDITING NOTE (honest, disclosed in build.log): long stalls while a live
  RPC call is in flight are capped at 8s per stall — the command OUTPUT is
  never edited, only the waiting time is compressed. A 6s hold is added
  after the registry section so its 11 lines stay readable.
- Frames -> video/frames/*.png; assemble with ffmpeg separately.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FPS = 10
COLS = 108
ROWS = 30
FONT_SIZE = 24
LINE_H = 31
MARGIN_X, MARGIN_Y = 64, 56
BG = (11, 15, 20)
FG = (201, 209, 217)
GREEN = (126, 231, 135)
BLUE = (88, 166, 255)
MUTED = (139, 148, 158)
STALL_CAP = 8.0      # max seconds shown for one idle gap (live RPC wait)
REGISTRY_HOLD = 6.0  # extra hold after the registry section (readability)
TITLE_S = 8
CLOSE_S = 10

from PIL import Image, ImageDraw, ImageFont

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Commands shown after each section header (canonical reviewer commands).
SECTION_CMDS = {
    "2": ["$ curl -s -X POST localhost:8765/api/audit "
          "-d '{\"address\":\"0x336e…ae2a\",\"chain\":\"xlayer\"}' | jq"],
    "3": ["$ curl -s localhost:8765/api/tapeout | jq",
          "$ curl -s localhost:8765/api/gasprice | jq"],
    "4": ["$ python3 circuit/risk_circuit.py",
          "$ curl -s localhost:8765/api/circuit | jq"],
    "5": ["$ python3 video/show_registry.py"],
}

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b[()][0-9A-B]|\x00")
HEADER_RE = re.compile(r"^### (\d+[a-z]?) - ")


def load_events(ts_path, timing_path):
    with open(ts_path, "rb") as f:
        raw = f.read()
    chunks = []
    total = 0.0
    with open(timing_path) as f:
        for line in f:
            parts = line.split()
            if len(parts) != 2:
                continue
            try:
                delay, nbytes = float(parts[0]), int(parts[1])
            except ValueError:
                continue
            delay = min(delay, STALL_CAP)  # compress live-RPC waiting stalls
            total += delay
            chunks.append((total, raw[:nbytes]))
            raw = raw[nbytes:]
    if raw:
        chunks.append((total + 0.1, raw))
    return chunks


def replay(chunks):
    """Return list of (time, [visible lines as (text, kind)]) snapshots at FPS."""
    lines = []  # list of (text, kind); kind: plain|cmd|header
    cur = ""
    cur_kind = "plain"
    events = []  # (time, lines-copy)
    injected = set()
    section_times = {}  # section number -> first-seen time
    pending_header = [None]  # section number of a header still wrapping

    def inject_cmds(n):
        if n in SECTION_CMDS and n not in injected:
            injected.add(n)
            for c in SECTION_CMDS[n]:
                lines.append((c, "cmd"))

    def flush_line():
        nonlocal cur, cur_kind
        if cur or cur_kind != "plain":
            lines.append((cur, cur_kind))
            # Inject the section's canonical commands right after its header.
            # Headers longer than COLS wrap across flushed lines: a header is
            # complete only when a flushed line ends with "###".
            m = HEADER_RE.match(lines[-1][0])
            if m and lines[-1][0].rstrip().endswith("###"):
                inject_cmds(m.group(1))
                pending_header[0] = None
            elif m:
                pending_header[0] = m.group(1)  # header started, still wrapping
            elif pending_header[0] is not None and lines[-1][0].rstrip().endswith("###"):
                inject_cmds(pending_header[0])
                pending_header[0] = None
            elif pending_header[0] is not None:
                pending_header[0] = None  # not a header after all; drop it
        cur = ""
        cur_kind = "plain"

    def push_text(text):
        nonlocal cur, cur_kind
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == "\r":
                if i + 1 < len(text) and text[i + 1] == "\n":
                    flush_line()
                    i += 2
                    continue
                cur = ""
                i += 1
                continue
            elif ch == "\n":
                flush_line()
                i += 1
            elif ch == "\b":
                cur = cur[:-1]
                i += 1
            else:
                cur += ch
                if len(cur) >= COLS:
                    flush_line()
                i += 1

    carry = ""
    for t, chunk in chunks:
        text = ANSI_RE.sub("", chunk.decode("utf-8", errors="replace"))
        text = carry + text
        carry = ""
        if text.endswith("\r"):
            carry = "\r"
            text = text[:-1]
        push_text(text)
        if cur:
            snap = lines + [(cur, cur_kind)]
        else:
            snap = list(lines)
        events.append((t, snap))
        for line, _ in snap:
            m = HEADER_RE.match(line)
            if m and m.group(1) not in section_times:
                section_times[m.group(1)] = t
    if cur:
        flush_line()
    total = chunks[-1][0] if chunks else 0.0
    return events, total, section_times


def draw_terminal(draw, snap_lines):
    font = ImageFont.truetype(MONO, FONT_SIZE)
    font_b = ImageFont.truetype(MONO_BOLD, FONT_SIZE)
    visible = snap_lines[-ROWS:]
    y = MARGIN_Y
    for text, kind in visible:
        f = font_b if kind in ("cmd", "header") else font
        color = GREEN if kind == "cmd" else (BLUE if kind == "header" else FG)
        while len(text) > COLS:
            draw.text((MARGIN_X, y), text[:COLS], font=f, fill=color)
            text = text[COLS:]
            y += LINE_H
        draw.text((MARGIN_X, y), text, font=f, fill=color)
        y += LINE_H


def draw_card(title_lines, sub_lines, accent, footer=None):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = ImageFont.truetype(SANS_BOLD, 92)
    f_sub = ImageFont.truetype(SANS, 44)
    f_small = ImageFont.truetype(SANS, 32)
    y = 300
    for line in title_lines:
        bb = d.textbbox((0, 0), line, font=f_title)
        d.text(((W - (bb[2] - bb[0])) // 2, y), line, font=f_title, fill=FG)
        y += 130
    y += 30
    for line in sub_lines:
        bb = d.textbbox((0, 0), line, font=f_sub)
        d.text(((W - (bb[2] - bb[0])) // 2, y), line, font=f_sub, fill=accent)
        y += 70
    d.text((MARGIN_X, H - 90),
           footer or "OKX Build X  ·  X Layer TapeOut Accelerate",
           font=f_small, fill=MUTED)
    return img


def main():
    ts_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "combined.typescript")
    timing_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "combined.timing")
    frames_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    chunks = load_events(ts_path, timing_path)
    events, total, section_times = replay(chunks)
    print(f"session: {len(chunks)} chunks, {total:.1f}s (stalls capped at {STALL_CAP}s)")

    # Hold after the registry section (§5): insert extra time at the end of
    # the terminal replay by shifting the close card later — implemented as
    # extra still frames of the final terminal state before the close card.
    frames = 0

    def save(img):
        nonlocal frames
        img.save(os.path.join(frames_dir, f"frame_{frames:06d}.png"))
        frames += 1

    # title card
    title = draw_card(["SlayGuard X"],
                      ["One wrong click can drain a wallet.",
                       "Audit any X Layer contract first — free."], BLUE)
    for _ in range(TITLE_S * FPS):
        save(title)
    # terminal replay, with a readability hold frozen on the registry (§5)
    # frame: for 6s after §6's header time, keep showing the snapshot from
    # the event just BEFORE §6 appeared (registry output, no §6 yet), then
    # resume (everything after shifts +6s). Index-based, because the
    # registry output and the §6 header share one event timestamp.
    t6 = section_times.get("6", total)
    idx6 = None
    for i, (_et, snap) in enumerate(events):
        if any(HEADER_RE.match(line) and line.startswith("### 6 - ")
               for line, _ in snap):
            idx6 = i
            break
    hold_snap = events[idx6 - 1][1] if idx6 else (events[-1][1] if events else None)
    hold_end = t6 + REGISTRY_HOLD
    total_warped = total + REGISTRY_HOLD

    def snap_at(t):
        snap = None
        for et, el in events:
            if et <= t:
                snap = el
            else:
                break
        return snap

    n_term = int(total_warped * FPS) + 1
    for i in range(n_term):
        t = i / FPS
        if t6 <= t < hold_end:
            snap = hold_snap
        elif t >= hold_end:
            snap = snap_at(t - REGISTRY_HOLD)
        else:
            snap = snap_at(t)
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        if snap:
            draw_terminal(d, snap)
        save(img)
    # close card — sub-lines overridable via env SLAY_CLOSE_SUBS (JSON list),
    # e.g. for the no-tapeout variant (repo pushed, no circuit ID claim).
    # Default = original card ("GitHub repo — not yet pushed").
    import json as _json
    _close_subs = _json.loads(os.environ["SLAY_CLOSE_SUBS"]) \
        if os.environ.get("SLAY_CLOSE_SUBS") else \
        ["SlayGuard X  ·  OKX Build X",
         "Registry 0x55b9…42e5 — X Layer mainnet",
         "GitHub repo — not yet pushed"]
    close = draw_card(["Audit before you click."], _close_subs, GREEN)
    for _ in range(CLOSE_S * FPS):
        save(close)

    dur = frames / FPS
    print(f"frames: {frames}, duration: {dur:.1f}s ({dur/60:.2f} min)")
    print("section starts (terminal time, add title card):")
    for n in sorted(section_times):
        shift = REGISTRY_HOLD if n in ("6", "7") else 0.0
        print(f"  §{n}: {section_times[n]:.1f}s terminal = {section_times[n] + TITLE_S + shift:.1f}s video")
    print(f"  terminal ends: {total:.1f}s terminal = {total + TITLE_S + REGISTRY_HOLD:.1f}s video")
    print(f"  close card: {total + TITLE_S + REGISTRY_HOLD:.1f}s video")
    if not (60 <= dur <= 180):
        print("WARNING: duration outside 1-3 min target!")


if __name__ == "__main__":
    main()
