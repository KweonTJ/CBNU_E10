#!/usr/bin/env python3
"""Deterministic procedural terrazzo and ceiling maps (not survey photographs)."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / 'assets' / 'textures'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(10)
    for name, base in [('terrazzo_cream', (185, 183, 172)), ('terrazzo_green', (139, 157, 145))]:
        noise = rng.normal(0, 6, (512, 512, 1))
        data = np.clip(np.array(base)[None, None, :] + noise, 0, 255).astype('uint8')
        picture = Image.fromarray(data)
        draw = ImageDraw.Draw(picture)
        for _ in range(10000):
            x, y = rng.integers(0, 512, 2)
            size = int(rng.integers(1, 4))
            tone = int(rng.choice([75, 105, 130, 205, 225]))
            draw.ellipse((x, y, x + size, y + size), fill=(tone, tone, max(0, tone - 6)))
        picture.save(OUT / f'{name}.png')
    picture = Image.new('RGB', (512, 256), (221, 222, 218))
    draw = ImageDraw.Draw(picture)
    for y in range(10, 250, 12):
        for x in range(8, 505, 10):
            shade = int(rng.integers(153, 192))
            draw.ellipse((x, y, x + 1, y + 2), fill=(shade, shade, shade))
    picture.save(OUT / 'ceiling.png')
    # Brick tile covers 1.2 x 0.6 m: five bricks per row, eight courses.
    picture = Image.new('RGB', (600, 300), (143, 130, 118))
    draw = ImageDraw.Draw(picture)
    for row in range(8):
        shift = 60 if row%2 else 0
        for col in range(-1, 6):
            x, y = col*120+shift, row*37.5
            red = int(rng.integers(126, 166))
            color = (red, int(red*.53+rng.integers(0,12)), int(red*.43+rng.integers(0,12)))
            draw.rectangle((x+3,y+2,x+117,y+35.5),fill=color)
    data = np.array(picture).astype(float)
    data += rng.normal(0,3,(300,600,1))
    Image.fromarray(np.clip(data,0,255).astype('uint8')).save(OUT/'brick.png')
    picture = Image.new('RGBA',(512,256),(255,255,255,0))
    draw=ImageDraw.Draw(picture)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',190)
    draw.text((40,5),'E10',font=font,fill=(242,240,224,255))
    picture.save(OUT/'building_sign.png')
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    picture = Image.new('RGB', (512, 768), (220, 223, 220))
    draw = ImageDraw.Draw(picture)
    draw.rectangle((0, 0, 511, 145), fill=(23, 64, 105))
    font = ImageFont.truetype(font_path, 45)
    draw.text((28, 30), 'E10   3F', fill='white', font=font)
    for i in range(12):
        y = 180 + i * 44
        draw.rectangle((25, y, 72, y + 23), fill=(63, 77, 88))
        draw.rectangle((90, y + 6, 460, y + 15), fill=(118, 125, 127))
    picture.save(OUT / 'directory.png')
    picture = Image.new('RGB', (512, 768), '#f1f0df')
    draw = ImageDraw.Draw(picture)
    draw.rectangle((10, 10, 501, 757), outline='#185775', width=15)
    korean_fonts = list(Path('/usr/share/fonts').rglob('*CJK*'))
    if korean_fonts:
        font = ImageFont.truetype(str(korean_fonts[0]), 158)
        draw.text((75, 65), '정숙', fill='#a92731', font=font)
    else:
        font = ImageFont.truetype(font_path, 80)
        draw.text((50, 100), 'QUIET', fill='#a92731', font=font)
    draw.rectangle((35, 320, 477, 725), fill='#18647a')
    font = ImageFont.truetype(font_path, 38)
    draw.text((70, 400), 'RESEARCH\nIN PROGRESS', fill='white', font=font, spacing=28)
    picture.save(OUT / 'quiet.png')
    print(f'Wrote procedural material maps to {OUT}')


if __name__ == '__main__':
    main()
