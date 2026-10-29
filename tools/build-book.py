# -*- coding: utf-8 -*-
"""
THE SWITCH — PDF builder.

Reads book-source/the-switch.md (plain, easy to edit) and renders
assets/the-switch.pdf in a 1930s art-deco gold/sepia "silver screen" style:
sepia paper, gold double frame, framed title card, film-card quote,
deco diamond separators, affirmations in gold, minimal footer.

Usage:
    python tools/build-book.py            # build assets/the-switch.pdf
    python tools/build-book.py --check    # only verify the PDF builds
"""
import os
import re
import sys

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_PATH = os.path.join(ROOT, "book-source", "the-switch.md")
OUT_PATH = os.path.join(ROOT, "assets", "the-switch.pdf")

# --- 1930s art-deco palette ---
PAPER = (239, 229, 205)     # sepia cream interior
PAPER_COVER = (233, 221, 193)  # slightly deeper sepia cover
INK = (43, 38, 33)          # body text
GOLD = (176, 141, 46)       # aged gold interior accents
GOLD_BRIGHT = (196, 158, 61)  # cover gold
GOLD_FADED = (171, 140, 80)  # barely-there gold (footers, rules)
OXBLOOD = (94, 45, 24)      # rare accent (scene headings)

CARDS = {
    "TITLE": "THE SWITCH",
    "SUBTITLE": "A Di-Mind Story",
    "TAGLINE": "From Distracted WORLD to Discipline",
    "AUTHOR": "DI-MIND · THE DISTRACTED WORLD",
    "YEAR": "2026",
    "COVER_QUOTE": 'He was distracted. Then he found the switch. That\'s the whole story.',
}

FOOTER_TEXT = "THE SWITCH · 2026"


def spaced(text, every=1):
    """Simulate letterspacing for core fonts (windows-1252 has no char spacing)."""
    return (" ".join(text) if every == 1 else text).replace("   ", "  ·  ")


def deco_diamond(pdf, x, y, r=1.6, fill=True):
    pdf.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], "F" if fill else "D")


def deco_separator(pdf, y, half=18, style=1):
    """Art-deco line: rule — diamond — rule, mirrored."""
    pdf.set_draw_color(*(GOLD if style == 1 else GOLD_FADED))
    pdf.set_fill_color(*GOLD)
    pdf.set_line_width(0.5 if style == 1 else 0.3)
    w = pdf.w
    xl, xr = w / 2 - half, w / 2 + half
    pdf.line(xl, y, w / 2 - 4, y)
    pdf.line(w / 2 + 4, y, xr, y)
    deco_diamond(pdf, w / 2 - 1.6, y)
    deco_diamond(pdf, w / 2 + 1.6, y)


def deco_corner(pdf, x, y, dx, dy, arm=8, gap=2.2):
    """Stepped art-deco corner inside a frame corner at (x, y), arms along dx/dy (±1)."""
    pdf.set_draw_color(*GOLD_BRIGHT)
    for i, lw in enumerate((0.9, 0.5, 0.3)):
        off = gap + i * 2.2
        x0 = x + dx * off
        y0 = y + dy * off
        pdf.set_line_width(lw)
        pdf.line(x0, y0, x0 + dx * arm, y0)
        pdf.line(x0, y0, x0, y0 + dy * arm)


def parse_md(path):
    """Parse the book markdown into (front, blocks). Block kinds:
    h2 (chapter), h3 (scene), p, li, rule (---), scene_close (===),
    quote (>), aside (*...* affirmation line)."""
    with open(path, encoding="utf-8") as fp:
        raw = fp.read()

    front = dict(CARDS)
    m = re.match(r"\s*---\s*\n(.*?)\n---\s*\n?(.*)", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                if k in CARDS and v.strip():
                    front[k] = v.strip().strip('"')
        raw = m.group(2)

    blocks, para = [], []

    def flush():
        if para:
            blocks.append(("p", " ".join(para)))
            para.clear()

    for line in raw.splitlines():
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("## "):
            flush(); blocks.append(("h3", s[3:]))
        elif s.startswith("# "):
            flush(); blocks.append(("h2", s[2:]))
        elif s == "---":
            flush(); blocks.append(("rule", None))
        elif s == "===":
            flush(); blocks.append(("scene_close", None))
        elif s.startswith("> "):
            flush(); blocks.append(("quote", s[2:]))
        elif re.match(r"^\d+\.\s", s):
            flush(); blocks.append(("li", s))
        elif s.startswith("*") and s.endswith("*") and not s.startswith("**"):
            flush(); blocks.append(("aside", s.strip("*")))
        else:
            para.append(s)
    flush()
    return front, blocks


def clean(text):
    return text.replace("**", "")


class DecoPDF(FPDF):
    """FPDF with the minimal clean footer: THE SWITCH · 2026 + page number."""

    def footer(self):
        if self.page_no() <= 1:
            return
        self.set_y(-15)  # 15 mm from bottom
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*GOLD_FADED)
        self.cell(0, 4, spaced(FOOTER_TEXT), align="C")
        self.set_y(-15)
        self.set_x(self.w - 24)
        self.set_font("Helvetica", "I", 7)
        self.cell(8, 4, str(self.page_no()), align="R")


def build(check=False):
    if FPDF is None:
        print("fpdf2 is missing. Install with: pip install fpdf2")
        sys.exit(1)

    front, blocks = parse_md(MD_PATH)

    pdf = DecoPDF(format="A5")
    pdf.core_fonts_encoding = "windows-1252"
    pdf.set_margins(20, 22, 20)
    pdf.set_auto_page_break(auto=True, margin=24)
    W, H = pdf.w, pdf.h

    # ============================ COVER ============================
    pdf.add_page()
    pdf.set_fill_color(*PAPER_COVER)
    pdf.rect(0, 0, W, H, "F")

    # Art-deco double frame with stepped corners.
    pdf.set_draw_color(*GOLD_BRIGHT)
    pdf.set_line_width(0.4)
    pdf.rect(9, 9, W - 18, H - 18)
    pdf.set_line_width(1.1)
    pdf.rect(13, 13, W - 26, H - 26)
    for x, y, dx, dy in ((15, 15, 1, 1), (W - 15, 15, -1, 1),
                         (15, H - 15, 1, -1), (W - 15, H - 15, -1, -1)):
        deco_corner(pdf, x, y, dx, dy)

    # Title card: small framed panel with stepped deco rules above/below.
    card_w, card_x = W - 76, 38
    top = 44
    # stepped lines above card
    pdf.set_draw_color(*GOLD_BRIGHT)
    for i, inset in enumerate((0, 6, 12)):
        y = top - 4 + i * 2.2
        pdf.set_line_width(0.9 - i * 0.25)
        pdf.line(card_x + 6 + inset, y, W - 38 - 6 - inset, y)
    pdf.set_fill_color(*PAPER_COVER)
    pdf.rect(card_x, top, card_w, 52, style="DF")
    pdf.set_line_width(0.4)
    pdf.rect(card_x + 2.5, top + 2.5, card_w - 5, 52 - 5)

    pdf.set_text_color(*OXBLOOD)
    pdf.set_y(top + 9)
    try:
        pdf.set_char_spacing(1.2)
    except AttributeError:
        pass
    pdf.set_font("Times", "B", 34)
    pdf.cell(0, 16, front["TITLE"], align="C")
    try:
        pdf.set_char_spacing(0)
    except AttributeError:
        pass
    pdf.set_y(top + 27)
    pdf.set_text_color(*INK)
    pdf.set_font("Times", "I", 15)
    pdf.cell(0, 8, front["SUBTITLE"], align="C")
    # stepped lines below card
    for i, inset in enumerate((12, 6, 0)):
        y = top + 56 + i * 2.2
        pdf.set_line_width(0.3 + (2 - i) * 0.3)
        pdf.set_draw_color(*GOLD_BRIGHT)
        pdf.line(card_x + 6 + inset, y, W - 38 - 6 - inset, y)

    # Tagline (small caps feel via caps text)
    pdf.set_y(top + 68)
    pdf.set_text_color(*GOLD)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(0, 6, spaced(front["TAGLINE"].upper()) if len(front["TAGLINE"]) < 60 else front["TAGLINE"].upper(), align="C")

    # Film-card quote: double-bordered panel like a 1930s cinema title card.
    qy = top + 86
    qw, qx = W - 90, 45
    pdf.set_draw_color(*GOLD_BRIGHT)
    pdf.set_line_width(0.7)
    pdf.rect(qx, qy, qw, 30, "D")
    pdf.set_line_width(0.3)
    pdf.rect(qx + 2, qy + 2, qw - 4, 30 - 4)
    pdf.set_y(qy + 5)
    pdf.set_x(qx + 5)
    pdf.set_text_color(*INK)
    pdf.set_font("Times", "I", 11.5)
    pdf.multi_cell(qw - 10, 5.4, '"' + front["COVER_QUOTE"] + '"', align="C")

    # Footer crest: small diamond + author + year.
    pdf.set_y(H - 46)
    pdf.set_text_color(*GOLD_BRIGHT)
    pdf.set_font("Helvetica", "", 8)
    deco_separator(pdf, H - 46, half=30, style=1)
    pdf.set_y(H - 42)
    pdf.cell(0, 6, spaced(front["AUTHOR"]), align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, front["YEAR"], align="C")

    # ============================ INTERIOR ============================
    body_started = [False]

    def interior_page(first=False):
        pdf.add_page()
        pdf.set_fill_color(*PAPER)
        pdf.rect(0, 0, W, H, "F")
        # faint deco frame on every interior page
        pdf.set_draw_color(*GOLD_FADED)
        pdf.set_line_width(0.25)
        pdf.rect(8, 8, W - 16, H - 16)
        pdf.set_text_color(*INK)
        if not first:
            body_started[0] = True

    def h(txt, h=6, align="J", style="", size=11, color=INK):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Times", style, size)
        if color != INK:
            pdf.set_text_color(*color)
        pdf.multi_cell(0, h, txt, align=align)
        if color != INK:
            pdf.set_text_color(*INK)

    interior_page()

    for kind, text in blocks:
        try:
            if pdf.get_y() > pdf.page_break_trigger - 22 and kind in ("h2", "h3"):
                interior_page()
            if kind == "h2":
                pdf.ln(6)
                # deco ornament above chapter title
                y = pdf.get_y()
                deco_separator(pdf, y, half=14, style=1)
                pdf.set_y(y + 5)
                try:
                    pdf.set_char_spacing(0.8)
                except AttributeError:
                    pass
                h(text.upper(), h=7.5, align="C", style="B", size=14, color=OXBLOOD)
                try:
                    pdf.set_char_spacing(0)
                except AttributeError:
                    pass
                y = pdf.get_y()
                pdf.set_draw_color(*GOLD)
                pdf.set_line_width(0.5)
                pdf.line(W / 2 - 16, y + 2.5, W / 2 + 16, y + 2.5)
                deco_diamond(pdf, W / 2, y + 2.5, r=1.4)
                pdf.set_y(y + 9)
            elif kind == "h3":
                pdf.ln(3)
                h(clean(text).replace("/", "·"), h=6, align="L", style="B", size=11.5, color=OXBLOOD)
            elif kind == "quote":
                h(text, align="L", style="I")
            elif kind == "li":
                h(text)
            elif kind == "aside":
                # affirmation-style line, centered, gold
                pdf.ln(2)
                y = pdf.get_y()
                pdf.set_draw_color(*GOLD_FADED)
                pdf.set_line_width(0.3)
                pdf.set_x(24)
                pdf.line(24, y + 2.5, W - 24, y + 2.5)
                pdf.set_y(y + 6)
                h(text, h=5.6, align="C", style="I", size=10.5, color=GOLD)
                pdf.ln(2)
            elif kind == "rule":
                y = pdf.get_y() + 3
                deco_separator(pdf, y, half=12, style=2)
                pdf.set_y(y + 6)
            elif kind == "scene_close":
                y = pdf.get_y() + 4
                deco_separator(pdf, y, half=22, style=1)
                pdf.set_y(y + 8)
            else:
                h(clean(text))
        except Exception:
            print("FAILED at block: kind=%r text=%r y=%r" % (kind, (text[:80] if isinstance(text, str) else text), pdf.get_y()), file=sys.stderr)
            raise

    if not check:
        pdf.output(OUT_PATH)
        size = os.path.getsize(OUT_PATH)
        total = pdf.pages_count if hasattr(pdf, "pages_count") else pdf.no_pages
        print("OK: wrote %s (%d KB, %d pages)" % (OUT_PATH, size // 1024, total))
    else:
        pdf_bytes = pdf.output()
        total = pdf.pages_count if hasattr(pdf, "pages_count") else pdf.no_pages
        print("OK: PDF builds (%d KB, %d pages)" % (len(pdf_bytes) // 1024, total))


if __name__ == "__main__":
    try:
        from fpdf import FPDF  # noqa: F401
    except ImportError:
        print("fpdf2 is missing. Install with: pip install fpdf2")
        sys.exit(1)
    build(check="--check" in sys.argv)
