"""Build native SVG pixel art from the existing hand study, plus brand typography.
Pillow samples the source; shipped SVGs contain only vector paths and CSS.
"""
from pathlib import Path
from collections import defaultdict
from PIL import Image
import math
import random

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
FONT = '-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif'
BLUE = '#0066CC'
INK = '#0A0A0A'
PAPER = '#FAFBFC'


def svg(width, height, content, title, style=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{title}</title><style>text{{font-family:{FONT};fill:{INK}}}{style}</style>{content}</svg>'


def mark(x, y, size):
    return f'<g transform="translate({x} {y}) scale({size / 100})"><rect width="100" height="100" rx="9.5" fill="{BLUE}"/><path d="M-3 74.2 25.5 73.2 60 59.8 71.2 48.8 103 64.8M71.2 48.8 103 35.2" fill="none" stroke="white" stroke-width="6"/><path d="m77.5 48.9 25.5-11v24.1z" fill="{BLUE}"/></g>'


def build_header():
    image = Image.open(OUT / 'reaching-hands.png').convert('L').resize((280, 93), Image.Resampling.LANCZOS)
    rng = random.Random(2100)
    groups = defaultdict(list)
    for y in range(image.height):
        for x in range(image.width):
            value = image.getpixel((x, y))
            if value < 32:
                continue
            strength = min(1, (value - 24) / 185)
            if rng.random() > .2 + strength * .8:
                continue
            px, py = 18 + x * 3.3, 196 + y * 3.3
            size = 1.25 + 1.65 * strength
            # Cells reveal in a broken wave rather than a rectangular wipe.
            batch = min(23, int(x / 280 * 15 + rng.random() * 9))
            shade = min(4, int(strength * 5))
            groups[(batch, shade)].append(f'M{px:.1f},{py:.1f}h{size:.1f}v{size:.1f}h-{size:.1f}z')
    base = f'<rect width="960" height="540" fill="{PAPER}"/>'
    base += mark(38, 31, 24)
    base += '<text x="72" y="49" font-size="17" font-weight="600">Project2100</text><text x="922" y="49" text-anchor="end" font-size="13" style="fill:#6B7280">SYDNEY, AUSTRALIA</text>'
    base += '<text x="34" y="133" font-size="76" font-weight="600" letter-spacing="-4">Josh Botha<tspan fill="#0066CC">.</tspan></text>'
    base += '<text x="39" y="171" font-size="19" style="fill:#4B5563">Full-stack developer. Software, data and AI.</text>'
    base += '<path d="M38 514H922" stroke="#DCE5ED"/><text x="38" y="534" font-size="11" letter-spacing="1.3" style="fill:#0066CC">HUMAN IDEAS. USEFUL SOFTWARE.</text><text x="922" y="534" text-anchor="end" font-size="11" style="fill:#6B7280">Built one pixel at a time.</text>'
    motion = '.pixel{animation:assemble 1.05s cubic-bezier(.22,1,.36,1) both}@keyframes assemble{0%{opacity:0;transform:translate(18px,-18px)}38%{opacity:.55}100%{opacity:1;transform:none}}@media(prefers-reduced-motion:reduce){.pixel{animation:none}}'
    def art(progress=None):
        result = []
        for (batch, shade), paths in sorted(groups.items()):
            delay = batch / 23 * 1.85
            alpha = [.22, .38, .55, .77, 1][shade]
            if progress is not None and progress < delay:
                continue
            klass = '' if progress is not None else f'class="pixel" style="animation-delay:{delay:.3f}s"'
            result.append(f'<g {klass}><path d="{"".join(paths)}" fill="{BLUE}" opacity="{alpha}"/></g>')
        return ''.join(result)
    title = 'Josh Botha, full-stack developer at Project2100. Blue pixels assemble into two reaching hands.'
    (OUT / 'profile-hero.svg').write_text(svg(960, 540, base + art(), title, motion), encoding='utf-8')
    (OUT / 'profile-hero-static.svg').write_text(svg(960, 540, base + art(4), title), encoding='utf-8')
    mobile = f'<rect width="420" height="350" fill="{PAPER}"/>' + mark(22,20,20)
    mobile += '<text x="51" y="36" font-size="14" font-weight="600">Project2100</text><text x="397" y="35" text-anchor="end" font-size="10" style="fill:#6B7280">SYDNEY, AUSTRALIA</text>'
    mobile += '<text x="19" y="106" font-size="53" font-weight="600" letter-spacing="-2.6">Josh Botha<tspan fill="#0066CC">.</tspan></text><text x="23" y="137" font-size="14" style="fill:#4B5563">Full-stack developer. Software, data and AI.</text>'
    mobile += '<path d="M22 322H398" stroke="#DCE5ED"/><text x="22" y="341" font-size="10" letter-spacing=".6" style="fill:#0066CC">HUMAN IDEAS. USEFUL SOFTWARE.</text>'
    for static in [False, True]:
        part = f'<g transform="translate(0 90) scale(.4375)">{art(4) if static else art()}</g>'
        suffix = '-static' if static else ''
        (OUT / f'profile-hero-mobile{suffix}.svg').write_text(svg(420,350,mobile+part,title,'' if static else motion),encoding='utf-8')
    (ROOT / 'preview' / 'hero-mid.svg').write_text(svg(960, 540, base + art(1.1), title), encoding='utf-8')
    print('Hero:', sum(map(len, groups.values())), 'vector pixels,', (OUT / 'profile-hero.svg').stat().st_size, 'bytes')


def build_focus():
    body = f'<rect width="960" height="224" fill="{PAPER}"/>'
    body += '<text x="38" y="42" font-size="13" style="fill:#6B7280">WHAT I BUILD</text>'
    content = [
        ('01', 'Interfaces', 'Web apps and Office add-ins.', 'React / TypeScript / Next.js'),
        ('02', 'Intelligence', 'Reporting that makes data useful.', 'Power BI / SQL / Azure'),
        ('03', 'Automation', 'AI tools for everyday workflows.', 'Node.js / Functions / Agents'),
    ]
    for i, (n, title, subtitle, stack) in enumerate(content):
        x = 38 + i * 308
        body += f'<text x="{x}" y="87" font-size="13" style="fill:{BLUE}">{n}</text><text x="{x}" y="121" font-size="29" font-weight="600" letter-spacing="-.7">{title}</text><text x="{x}" y="155" font-size="14" style="fill:#4B5563">{subtitle}</text><text x="{x}" y="192" font-size="12" style="fill:{BLUE}">{stack}</text>'
    body += '<path d="M326 78v118M634 78v118" stroke="#DCE5ED"/>'
    (OUT / 'focus.svg').write_text(svg(960, 224, body, 'Interfaces: React, TypeScript and Next.js. Intelligence: Power BI, SQL and Azure. Automation: Node.js, Functions and agents.'), encoding='utf-8')
    mobile = f'<rect width="420" height="350" fill="{PAPER}"/><text x="23" y="28" font-size="11" style="fill:#6B7280">WHAT I BUILD</text>'
    for i, (n, title, subtitle, stack) in enumerate(content):
        y=67+i*100
        mobile += f'<text x="23" y="{y}" font-size="12" style="fill:{BLUE}">{n}</text><text x="54" y="{y}" font-size="25" font-weight="600">{title}</text><text x="54" y="{y+28}" font-size="13" style="fill:#4B5563">{subtitle}</text><text x="54" y="{y+52}" font-size="11" style="fill:{BLUE}">{stack}</text>'
    (OUT / 'focus-mobile.svg').write_text(svg(420,350,mobile,'What I build: interfaces, intelligence and automation.'),encoding='utf-8')


if __name__ == '__main__':
    build_header()
    build_focus()
