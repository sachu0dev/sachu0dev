#!/usr/bin/env python3
"""Builds assets/hero.svg and assets/namestead.svg for the profile README.

    pip install fonttools
    python scripts/build-svgs.py path/to/Oswald[wght].ttf

Oswald comes from github.com/google/fonts (ofl/oswald). The big display words are drawn as
paths so they look the same on every machine; everything else is monospace text pinned to a
9px grid with textLength, so fallback fonts keep the layout. Edit the copy below and rebuild.
"""
import pathlib
import sys
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = pathlib.Path(__file__).resolve().parent.parent
W = 880
FS, CW = 15, 9  # monospace grid: 15px text, 9px per character
PAD = 32

# sushilk.tech palette
INK, INK2, CHAR, LINE = '#14160d', '#1d1f16', '#23231f', '#2c2c26'
CREAM, DIM, FAINT = '#fffaf5', '#b4b6a3', '#74766a'
LIME, MINT, RED = '#d1e030', '#9eef80', '#c4321f'
# namestead palette
CYAN, NS_INK = '#43c5e9', '#111212'

NBSP = '\u00a0'  # plain spaces collapse in SVG text, even with xml:space
MONO = "'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

font = instancer.instantiateVariableFont(TTFont(sys.argv[1]), {'wght': 700})
glyphs, cmap, upm = font.getGlyphSet(), font.getBestCmap(), font['head'].unitsPerEm
CAP = font['OS/2'].sCapHeight / upm


def num(v):
    s = f'{v:.1f}'
    return s[:-2] if s.endswith('.0') else s


def oswald(text, x, y, size, track=0.0):
    """Path data for text set in Oswald Bold with its baseline at y, and its width."""
    s, out, cx = size / upm, [], x
    for ch in text:
        g = glyphs[cmap[ord(ch)]]
        pen = SVGPathPen(glyphs, ntos=num)
        g.draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
        out.append(pen.getCommands())
        cx += g.width * s + track * size
    return ''.join(out), cx - x - track * size


def mono(segs, x, y, size=FS, cw=None, anchor=None):
    """One line of monospace text. segs is a string or [(text, fill[, inner svg])]."""
    if isinstance(segs, str):
        segs = [(segs, CREAM)]
    cw = cw or size * 0.6
    n = sum(len(s[0]) for s in segs)
    spans = ''.join(
        f'<tspan fill="{s[1]}">{escape(s[0].replace(" ", NBSP))}{s[2] if len(s) > 2 else ""}</tspan>' for s in segs
    )
    a = f' text-anchor="{anchor}"' if anchor else ''
    return (
        f'<text x="{num(x)}" y="{num(y)}" font-size="{size}" textLength="{num(n * cw)}" '
        f'lengthAdjust="spacing"{a}>{spans}</text>'
    ), n


def appear(content, begin):
    return f'<g opacity="0">{content}<set attributeName="opacity" to="1" begin="{begin:.2f}s" fill="freeze"/></g>'


def typed(cid, segs, x, y, begin, speed=0.045):
    """A line typed out one character at a time behind a moving block cursor; returns (svg, end)."""
    text, n = mono(segs, x, y)
    dur = max(n * speed, 0.05)
    widths = ';'.join(num(i * CW) for i in range(n + 1))
    xs = ';'.join(num(x + i * CW) for i in range(n + 1))
    svg = (
        f'<clipPath id="{cid}"><rect x="{num(x - 1)}" y="{num(y - FS)}" height="{FS + 6}" width="0">'
        f'<animate attributeName="width" values="{widths}" calcMode="discrete" begin="{begin:.2f}s" '
        f'dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>'
        f'<g clip-path="url(#{cid})">{text}</g>'
        f'<rect x="{num(x)}" y="{num(y - FS + 2)}" width="{CW}" height="{FS + 2}" fill="{LIME}" opacity="0">'
        f'<animate attributeName="x" values="{xs}" calcMode="discrete" begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{begin + dur + 0.12:.2f}s" fill="freeze"/></rect>'
    )
    return svg, begin + dur


def window(h, title):
    t, n = mono([(title, FAINT)], W / 2, 25, size=12, anchor='middle')
    return (
        f'<rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="14" fill="{INK}" stroke="{LINE}" stroke-width="2"/>'
        f'<path d="M2,15 a13,13 0 0 1 13,-13 h{W - 30} a13,13 0 0 1 13,13 v24 h-{W - 4} z" fill="{INK2}"/>'
        f'<line x1="2" y1="39" x2="{W - 2}" y2="39" stroke="{LINE}" stroke-width="1.5"/>'
        f'<circle cx="24" cy="20" r="6" fill="{RED}"/><circle cx="44" cy="20" r="6" fill="{LIME}"/>'
        f'<circle cx="64" cy="20" r="6" fill="{MINT}"/>{t}'
    )


def svg_doc(h, label, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" '
        f'role="img" aria-label="{escape(label)}" xml:space="preserve" font-family="{MONO}" '
        f'style="white-space:pre">'
        f'<title>{escape(label)}</title>{body}</svg>\n'
    )


def pulse(dur=1.6):
    return f'<animate attributeName="fill-opacity" values="1;.2;1" dur="{dur}s" repeatCount="indefinite"/>'


def hero():
    body, t = [], 0.5
    # the ruler from sushilk.tech, with a marker that tracks the intro
    ruler = [f'<rect x="2" y="40" width="{W - 4}" height="22" fill="{LIME}"/>']
    for x in range(10, W - 2, 10):
        h = 10 if x % 100 == 0 else 6 if x % 50 == 0 else 3
        ruler.append(f'<line x1="{x}" y1="40" x2="{x}" y2="{40 + h}" stroke="{INK}" stroke-width="1"/>')
        if x % 100 == 0:
            ruler.append(mono([(str(x), INK)], x + 3, 58, size=8)[0])
    body.append(''.join(ruler))

    y = 98
    s, t = typed('c0', [('$ ', LIME), ('figlet -f oswald "sushil kumar"', CREAM)], PAD, y, t)
    body.append(s)

    # the name, sized to leave room for the badge
    size, track = 100, 0.07
    _, w1 = oswald('SUSHIL', 0, 0, size, track)
    _, w2 = oswald('KUMAR', 0, 0, size, track)
    gap = 0.28 * size
    size *= 640 / (w1 + gap + w2)
    gap = 0.28 * size
    nb = y + 22 + CAP * size
    d1, w1 = oswald('SUSHIL', PAD, nb, size, track)
    d2, _ = oswald('KUMAR', PAD + w1 + gap, nb, size, track)
    t += 0.25
    body.append(
        f'<clipPath id="wipe"><rect x="{PAD - 4}" y="{y + 10}" height="{num(CAP * size + 24)}" width="0">'
        f'<animate attributeName="width" values="0;{W}" keyTimes="0;1" calcMode="spline" keySplines=".2 .8 .2 1" '
        f'begin="{t:.2f}s" dur=".8s" fill="freeze"/></rect></clipPath>'
        f'<g clip-path="url(#wipe)"><path d="{d1}" fill="{CREAM}"/>'
        f'<path d="{d2}" fill="none" stroke="{CREAM}" stroke-width="2"/></g>'
    )

    # the "dev" badge, with a slow ring of the tagline around it
    cx, cy = W - PAD - 72, nb - CAP * size / 2
    dd, dw = oswald('dev', 0, 0, 38)
    ring = ' BUILDS IT · SHIPS IT · KEEPS IT RUNNING ·'
    body.append(
        f'<g transform="translate({num(cx)},{num(cy)})"><g transform="scale(0)">'
        f'<animateTransform attributeName="transform" type="scale" values="0;1.08;1" keyTimes="0;.7;1" '
        f'begin="{t + 0.35:.2f}s" dur=".5s" fill="freeze"/>'
        f'<path id="ring" d="M-64,0 a64,64 0 1,1 128,0 a64,64 0 1,1 -128,0" fill="none"/>'
        f'<g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="28s" repeatCount="indefinite"/>'
        f'<text font-size="10.5" fill="{DIM}" letter-spacing="1"><textPath href="#ring" textLength="398" '
        f'lengthAdjust="spacing">{escape(ring)}</textPath></text></g>'
        f'<circle r="48" fill="{CHAR}" stroke="{LIME}" stroke-width="5"/>'
        f'<path d="{dd}" fill="{LIME}" transform="translate({num(-dw / 2)},{num(CAP * 38 / 2)})"/></g></g>'
    )
    t += 1.1

    lead = 24
    y = nb + 54

    def say(segs, gap=0.12):
        nonlocal y, t
        body.append(appear(mono(segs, PAD, y)[0], t))
        y += lead
        t += gap

    def run(cid, cmd):
        nonlocal y, t
        s, t = typed(cid, [('$ ', LIME), (cmd, CREAM)], PAD, y, t + 0.35)
        body.append(s)
        y += lead
        t += 0.25

    run('c1', 'whoami')
    say([('sushil kumar', CREAM), (' · ', FAINT), ('fullstack developer', CREAM), (' · ', FAINT),
         ('associate @ mind roots', DIM)])
    say([('// builds it, ships it, keeps it running.', LIME), ('  remote · india', FAINT)])
    y += 10

    run('c2', 'cat now.txt')
    say([('● ', MINT, pulse()), ('namestead.dev', CYAN), (' is live', CREAM),
         (': free subdomains for developers', DIM)])
    say([('  yourname.portfilio.live', CREAM), ('  https on · no card · no pull request', FAINT)])
    say([('  built ', DIM), ('✓', MINT), ('   live ', DIM), ('✓', MINT), ('   now ', DIM), ('→ ', LIME),
         ('getting it in front of developers', CREAM)])
    y += 10

    run('c3', 'uptime')
    say([('grovyo', CREAM), (' 2024 ', FAINT), ('→ ', LIME), ('script space', CREAM), (' 2025 ', FAINT),
         ('→ ', LIME), ('mind roots', CREAM), (' now', FAINT)])
    y += 4

    prompt, _ = mono([('$ ', LIME)], PAD, y)
    body.append(appear(
        prompt + f'<rect x="{PAD + 2 * CW}" y="{num(y - FS + 2)}" width="{CW}" height="{FS + 2}" fill="{LIME}">'
        f'<animate attributeName="opacity" values="1;0" dur="1.1s" calcMode="discrete" repeatCount="indefinite"/></rect>',
        t + 0.2,
    ))

    # the ruler marker follows the intro, then rests at the end
    body.insert(1, (
        f'<path d="M-5,62 L5,62 L0,55 Z" fill="{INK}"><animateTransform attributeName="transform" type="translate" '
        f'values="{PAD},0;{W - PAD},0" keyTimes="0;1" calcMode="spline" keySplines=".4 0 .2 1" '
        f'begin="0.3s" dur="{t:.2f}s" fill="freeze"/></path>'
    ))

    h = int(y + 32)
    return svg_doc(h, "Sushil Kumar: fullstack developer. Builds it, ships it, keeps it running. Now: Namestead.",
                   window(h, 'sushil@prod: ~ · zsh') + ''.join(body))


def namestead():
    body = []
    # the Namestead mark (34-unit artboard) beside the wordmark
    size = 44
    base = 66 + CAP * size
    m = (CAP * size + 8) / 34
    body.append(
        f'<g transform="translate({PAD},{num(base - CAP * size - 4)}) scale({m:.3f})">'
        f'<path d="M1,17 A16,16 0 0 1 17,1 A16,16 0 0 1 33,17 A16,16 0 0 1 17,33 L1,33 Z" fill="{CYAN}" '
        f'stroke="{NS_INK}" stroke-width="2" stroke-linejoin="round"/>'
        f'<polygon points="12.3,24.6 14.9,24.6 21.7,9.4 19.1,9.4" fill="{NS_INK}"/></g>'
    )
    wx = PAD + 34 * m + 14
    d, w = oswald('NAMESTEAD', wx, base, size, 0.04)
    d2, w2 = oswald('.dev', wx + w + 2, base, size, 0.02)
    body.append(f'<path d="{d}" fill="{CREAM}"/><path d="{d2}" fill="{CYAN}"/>')

    # status pill
    label, n = mono([('LIVE', MINT)], 0, 0, size=12)
    pw = 30 + n * 7.2 + 14
    px = W - PAD - pw
    py = base - CAP * size / 2 - 13
    body.append(
        f'<rect x="{num(px)}" y="{num(py)}" width="{num(pw)}" height="26" rx="13" fill="none" stroke="{MINT}" stroke-width="1.5"/>'
        f'<circle cx="{num(px + 16)}" cy="{num(py + 13)}" r="4.5" fill="{MINT}">{pulse(1.4)}</circle>'
        + mono([('LIVE', MINT)], px + 28, py + 17.5, size=12)[0]
    )
    body.append(mono([('// now shipping', LIME)], W - PAD - pw - 16 - 15 * 7.2, py + 17.5, size=12)[0])

    y = base + 42
    body.append(mono([('Free subdomains for developers.', CREAM)], PAD, y, size=18)[0])
    y += 26
    body.append(mono([('Claim a room. We’ll keep the building standing. Every rupee in and out, in public.', DIM)],
                     PAD, y, size=13)[0])

    # a looping curl against an example name
    y += 22
    bh = 62
    body.append(f'<rect x="{PAD}" y="{num(y)}" width="{W - 2 * PAD}" height="{bh}" rx="8" fill="{CHAR}" stroke="{LINE}"/>')
    cy1, cy2 = y + 25, y + 49
    segs = [('$ ', LIME), ('curl -sI https://', CREAM), ('yourname.portfilio.live', CYAN)]
    text, n = mono(segs, PAD + 16, cy1)
    cyc, typing, hold = 7.0, 1.5, 6.5
    vals = [num(i * CW) for i in range(n + 1)] + ['0']
    keys = [f'{i * typing / n / cyc:.4f}' for i in range(n + 1)] + [f'{hold / cyc:.4f}']
    body.append(
        f'<clipPath id="curl"><rect x="{PAD + 15}" y="{num(cy1 - FS)}" height="{FS + 6}" width="0">'
        f'<animate attributeName="width" values="{";".join(vals)}" keyTimes="{";".join(keys)}" calcMode="discrete" '
        f'begin="0.6s" dur="{cyc}s" repeatCount="indefinite"/></rect></clipPath>'
        f'<g clip-path="url(#curl)">{text}</g>'
    )
    resp, _ = mono([('HTTP/2 ', DIM), ('200', MINT), ('  https ', DIM), ('✓', MINT), ('  card ', DIM), ('✗', FAINT),
                    ('  pull request ', DIM), ('✗', FAINT), ('  ads ', DIM), ('✗', FAINT)], PAD + 16, cy2)
    body.append(
        f'<g opacity="0">{resp}<animate attributeName="opacity" values="0;1;0" '
        f'keyTimes="0;{(typing + 0.35) / cyc:.4f};{hold / cyc:.4f}" calcMode="discrete" begin="0.6s" '
        f'dur="{cyc}s" repeatCount="indefinite"/></g>'
    )

    # the five ranks, with a packet resolving down the chain
    y += bh + 40
    body.append(mono([('// five ranks, named after how the internet finds a website', FAINT)], PAD, y, size=12)[0])
    ly = y + 34
    x0, x1 = PAD + 50, W - PAD - 50
    body.append(f'<line x1="{x0}" y1="{num(ly)}" x2="{x1}" y2="{num(ly)}" stroke="{LINE}" stroke-width="3"/>')
    ranks = ['PING', 'RESOLVER', 'AUTHORITY', 'REGISTRY', 'ROOT']
    travel, cyc = 0.8, 5.0
    for i, r in enumerate(ranks):
        x = x0 + (x1 - x0) * i / 4
        p = travel * i / 4
        body.append(
            f'<circle cx="{num(x)}" cy="{num(ly)}" r="9" fill="{INK}" stroke="{CYAN}" stroke-width="2">'
            f'<animate attributeName="fill" values="{INK};{CYAN};{INK}" keyTimes="0;{p:.3f};{p + 0.16:.3f}" '
            f'calcMode="discrete" dur="{cyc}s" repeatCount="indefinite"/></circle>'
        )
        body.append(mono([(r, CREAM)], x, ly + 32, size=12, anchor='middle')[0])
    body.append(mono([('13 seats, A–M', FAINT)], x1, ly + 50, size=10, anchor='middle')[0])
    body.append(
        f'<circle cy="{num(ly)}" r="5" fill="{CREAM}"><animate attributeName="cx" values="{x0};{x1};{x1}" '
        f'keyTimes="0;{travel};1" dur="{cyc}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{travel};{travel + 0.05};1" dur="{cyc}s" '
        f'repeatCount="indefinite"/></circle>'
    )
    y = ly + 84
    body.append(mono([('money pays the rent. ', DIM), ('it never buys rank.', CREAM)], PAD, y)[0])

    # call to action
    cta = 'check it out → namestead.dev'
    cw = len(cta) * CW + 32
    cxp = W - PAD - cw
    body.append(
        f'<rect x="{num(cxp)}" y="{num(y - 22)}" width="{num(cw)}" height="34" rx="17" fill="{CYAN}"/>'
        + mono([(cta, NS_INK)], cxp + 16, y, size=FS)[0]
    )

    h = int(y + 34)
    return svg_doc(h, 'Namestead is live: free subdomains for developers at namestead.dev.',
                   window(h, 'namestead.dev · live') + ''.join(body))


if __name__ == '__main__':
    out = ROOT / 'assets'
    out.mkdir(exist_ok=True)
    (out / 'hero.svg').write_text(hero())
    (out / 'namestead.svg').write_text(namestead())
    print('wrote', out / 'hero.svg', 'and', out / 'namestead.svg')
