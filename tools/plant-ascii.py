"""Plant ASCII-art "images" into the blog.

Replaces every https://placehold.co image (blog card thumbnails and in-post
banners) with a themed ASCII plate, centered programmatically so the art
cannot misalign. Plates use plain ASCII characters only (safe in any font).
Run after any post list edit:  python tools/plant-ascii.py

Idempotent: repairs previous runs' output too (broken \1/\2 tokens and the
older unicode plate design) by re-planting.
"""
import io
import re

POSTS = {
    1:  ("*", "SWITCH"),
    2:  ("~", "DRIP"),
    3:  ("#", "NOISE"),
    4:  ("%", "INTUIT"),
    5:  ("+", "BUILD"),
    6:  ("o", "SIGNAL"),
    7:  ("@", "FOCUS"),
    8:  ("x", "REST"),
    9:  ("|", "ZONE"),
    10: ("8", "NO"),
    11: ("$", "WINS"),
    12: ("*", "MIRROR"),
    13: ("=", "PLAN"),
    14: ("(", "LO-KI"),
    15: ("'", "SILENCE"),
    16: ("O", "NOW"),
    17: ("\\", "SHADOW"),
    18: ("*", "IT WORKS"),
    19: ("^", "NPC-PC"),
}

# Matches the legacy broken tokens  \1 ... \2  OR a leftover placehold.co img.
TOKEN_RE = re.compile(
    "\\\\1(.*?)\\\\2|<img src=\"https://placehold\\.co[^>]*>", re.DOTALL)
BANNER_RE = re.compile(
    "<pre class=\"ascii-art ascii-banner\">.*?</pre>|"
    "<img src=\"https://placehold\\.co/600x300[^>]*>", re.DOTALL)


def _center(text, width):
    """ASCII centering with trailing spaces trimmed."""
    return text.center(width).rstrip()


def card_art(glyph, keyword):
    """Small plate for the blog grid thumbnail."""
    kw = (".  " + keyword + "  .")
    return ("<pre class=\"ascii-art ascii-card\">"
            + glyph + "\n" + _center(kw, 14)
            + "</pre>")


def banner_art(glyph, keyword, n):
    """Wider plate for the in-post banner."""
    w = 30
    top = "+" + ("-" * (w - 2)) + "+"
    no = "POST N\xba " + str(n).zfill(2)
    kw = (".  " + keyword + "  .")
    motif = "--   " + glyph + "   --"
    return ("<pre class=\"ascii-art ascii-banner\">"
            + top + "\n"
            + _center(no, w) + "\n"
            + _center(kw, w) + "\n"
            + _center(motif, w) + "\n"
            + top + "</pre>")


def main():
    src = io.open('index.html', encoding='utf-8').read()

    # 1. Card thumbnails: identified by data-post-id="post-N" in the anchor.
    n_cards = 0
    for m in list(re.finditer(r'data-post-id="post-(\d+)"', src)):
        n = int(m.group(1))
        scope_end = src.find('</article>', m.end())
        if scope_end == -1:
            continue
        segment = src[m.start():scope_end]
        glyph, kw = POSTS[n]
        segment2, cnt = TOKEN_RE.subn(lambda _: card_art(glyph, kw), segment)
        if cnt:
            src = src[:m.start()] + segment2 + src[scope_end:]
            n_cards += cnt

    # 2. In-post banners: region from id="post-N-content" to the next post.
    n_banners = 0
    parts = re.split('(id="post-\\d+-content")', src)
    cur_post = None
    for i, part in enumerate(parts):
        m = re.match('id="post-(\\d+)-content"', part)
        if m:
            cur_post = int(m.group(1))
            continue
        if cur_post is None:
            continue
        glyph, kw = POSTS.get(cur_post, ("*", "POST"))
        new_part, cnt = BANNER_RE.subn(
            lambda _: banner_art(glyph, kw, cur_post), part)
        if cnt:
            n_banners += cnt
            parts[i] = new_part
    src = ''.join(parts)

    io.open('index.html', 'w', encoding='utf-8', newline='\n').write(src)
    print("cards planted: %d, banners planted: %d" % (n_cards, n_banners))
    print("remaining placehold refs: %d" % len(re.findall("placehold\\.co", src)))
    print("broken tokens: %d" % len(TOKEN_RE.findall(src)))


if __name__ == '__main__':
    main()
