#!/usr/bin/env python3
"""render_video.py -> render_video_v2.py: eye-catching pass + all-English.
Changes: terminal 24->25pt, header band + real blue headers, amber key-number
tokens (digits / CAUTION / NAND) in terminal + cards, card title 92->112pt,
card subs 44->48pt bold, amber rule under card titles. No timing/structure
changes: TITLE_S/CLOSE_S/STALL_CAP/REGISTRY_HOLD unchanged."""
import re

src = open("render_video.py").read()

src = src.replace("FONT_SIZE = 24\nLINE_H = 31",
                  "FONT_SIZE = 25\nLINE_H = 32")
src = src.replace('MUTED = (139, 148, 158)',
                  'MUTED = (139, 148, 158)\nAMBER = (255, 193, 7)\nBAND = (16, 34, 56)\nKEY_RE = re.compile(r"\\d|CAUTION|NAND")')

old_terminal = src[src.index("def draw_terminal"):src.index("def draw_card")]
new_terminal = '''def draw_rich_terminal(d, x, y, seg, font, font_b):
    """Draw one terminal line word by word: tokens with digits (or
    CAUTION/NAND) in bold amber, the rest in the regular foreground."""
    parts = re.split(r"(\\s+)", seg)
    cx = x
    for part in parts:
        if not part:
            continue
        if part.isspace():
            cx += font.getlength(part)
            continue
        if KEY_RE.search(part):
            d.text((cx, y), part, font=font_b, fill=AMBER)
            cx += font_b.getlength(part)
        else:
            d.text((cx, y), part, font=font, fill=FG)
            cx += font.getlength(part)


def draw_terminal(draw, snap_lines):
    font = ImageFont.truetype(MONO, FONT_SIZE)
    font_b = ImageFont.truetype(MONO_BOLD, FONT_SIZE)
    visible = snap_lines[-ROWS:]
    y = MARGIN_Y
    for text, kind in visible:
        is_header = text.startswith("###")
        is_cmd = kind == "cmd"
        segs = []
        t = text
        while len(t) > COLS:
            segs.append(t[:COLS])
            t = t[COLS:]
        segs.append(t)
        for seg in segs:
            if is_header:
                draw.rectangle([MARGIN_X - 16, y - 4,
                                W - MARGIN_X + 16, y + LINE_H - 6], fill=BAND)
            if is_cmd:
                draw.text((MARGIN_X, y), seg, font=font_b, fill=GREEN)
            elif is_header:
                draw.text((MARGIN_X, y), seg, font=font_b, fill=BLUE)
            else:
                draw_rich_terminal(draw, MARGIN_X, y, seg, font, font_b)
            y += LINE_H


'''
src = src.replace(old_terminal, new_terminal)

old_card = src[src.index("def draw_card"):src.index("def main():")]
new_card = '''def draw_centered_rich(d, y, line, font, base):
    """Center one card sub-line; tokens with digits (or CAUTION/NAND)
    in amber, the rest in the base accent color."""
    parts = re.split(r"(\\s+)", line)
    total = sum(font.getlength(p) for p in parts if p)
    cx = (W - total) // 2
    for part in parts:
        if not part:
            continue
        if part.isspace():
            cx += font.getlength(part)
            continue
        color = AMBER if KEY_RE.search(part) else base
        d.text((cx, y), part, font=font, fill=color)
        cx += font.getlength(part)


def draw_card(title_lines, sub_lines, accent, footer=None):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = ImageFont.truetype(SANS_BOLD, 112)
    f_sub = ImageFont.truetype(SANS_BOLD, 48)
    f_small = ImageFont.truetype(SANS, 34)
    y = 290
    for line in title_lines:
        bb = d.textbbox((0, 0), line, font=f_title)
        d.text(((W - (bb[2] - bb[0])) // 2, y), line, font=f_title, fill=FG)
        y += 150
    # amber accent rule under the title
    rule_w = 420
    d.rectangle([(W - rule_w) // 2, y - 8, (W + rule_w) // 2, y - 2], fill=AMBER)
    y += 30
    for line in sub_lines:
        draw_centered_rich(d, y, line, f_sub, accent)
        y += 72
    d.text((MARGIN_X, H - 90),
           footer or "OKX Build X  ·  X Layer TapeOut Accelerate",
           font=f_small, fill=MUTED)
    return img


'''
src = src.replace(old_card, new_card)
open("render_video_v2.py", "w").write(src)
print("render_video_v2.py written")
import py_compile
py_compile.compile("render_video_v2.py", doraise=True)
print("compiles OK")
