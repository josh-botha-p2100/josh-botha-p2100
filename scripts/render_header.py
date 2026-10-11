"""Render the self-contained profile animation. Requires Pillow."""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1000, 310
BLUE = (0, 102, 204)
INK = (15, 30, 49)
BG = (250, 252, 255)
FONT_DIR = Path('C:/Windows/Fonts')


def font(size, bold=False):
    local = FONT_DIR / ('segoeuib.ttf' if bold else 'segoeui.ttf')
    if local.exists():
        return ImageFont.truetype(str(local), size)
    return ImageFont.truetype('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf', size)


def path_y(x, lane, phase=0):
    t = (x - 635) / 330
    amplitude = 33 * (1 - t) + 7
    return 148 + (lane - 3) * (22 - 12 * t) + amplitude * math.sin(t * 5.5 + lane * .48 + phase)


def render(phase):
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((48, 48), 'PROJECT2100 / DEVELOPER', font=font(14, True), fill=BLUE)
    d.text((44, 89), 'Josh Botha', font=font(60, True), fill=INK)
    d.text((48, 176), 'Software. Data. AI.', font=font(25), fill=(55, 74, 98))
    d.text((48, 250), 'Building useful things, one commit at a time.', font=font(15), fill=(95, 111, 130))

    # Seven data paths resolve into a coordinated flow. Motion loops smoothly.
    for lane in range(7):
        color = tuple(round(BG[i] * .68 + BLUE[i] * .32) for i in range(3))
        pts = [(x, path_y(x, lane)) for x in range(635, 966, 2)]
        d.line(pts, fill=color, width=2)
        t = (phase + lane / 7) % 1
        x = 637 + 324 * t
        y = path_y(x, lane)
        # Soft fade at endpoints avoids popping at the loop boundary.
        strength = min(1, t * 8, (1 - t) * 8)
        dot = tuple(round(BG[i] * (1 - strength) + BLUE[i] * strength) for i in range(3))
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=dot)
    return im


if __name__ == '__main__':
    out = ROOT / 'assets'
    out.mkdir(exist_ok=True)
    frames = [render(i / 70) for i in range(70)]
    # A shared palette avoids animation flicker and keeps the download small.
    palette = frames[0].quantize(colors=96)
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    frames[0].save(out / 'profile-header.gif', save_all=True, append_images=frames[1:], duration=80, loop=0, optimize=True, disposal=1)
    render(0).save(out / 'profile-header.png', optimize=True)
    with Image.open(out / 'profile-header.gif') as check:
        assert check.n_frames == 70
        assert check.size == (W, H)
    print(f'{out / "profile-header.gif"}: {(out / "profile-header.gif").stat().st_size:,} bytes, 70 frames')
