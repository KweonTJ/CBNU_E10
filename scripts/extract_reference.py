#!/usr/bin/env python3
"""Extract review frames; keep the source video outside the repository/vault."""
import argparse
import json
from pathlib import Path

import cv2
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', type=Path, default=Path('/home/a/Downloads/CBNU-E10.mp4'))
    parser.add_argument('--output', type=Path, default=ROOT / 'reference')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise RuntimeError(f'Cannot open {args.video}')
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    frames = []
    for second in range(0, int(duration), 2):
        cap.set(cv2.CAP_PROP_POS_MSEC, second * 1000)
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError(f'Cannot decode frame at {second}s')
        picture = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        name = f'frame_{second:03d}s.jpg'
        picture.save(args.output / name, quality=90)
        frames.append((second, name, picture))
    cap.release()
    for start in range(0, len(frames), 12):
        group = frames[start:start + 12]
        sheet = Image.new('RGB', (4 * 480, 3 * 300), '#161d25')
        draw = ImageDraw.Draw(sheet)
        for index, (second, name, picture) in enumerate(group):
            thumb = picture.copy()
            thumb.thumbnail((480, 270))
            x, y = index % 4 * 480, index // 4 * 300
            sheet.paste(thumb, (x, y + 25))
            draw.text((x + 10, y + 6), f'{second:02d}s', fill='white')
        sheet.save(args.output / f'contact_{start // 12 + 1:02d}.jpg', quality=94)
    metadata = {'source_video': str(args.video), 'duration_s': duration, 'fps': fps,
                'frames': [{'time_s': s, 'file': n} for s, n, _ in frames]}
    (args.output / 'video_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(f'Extracted {len(frames)} frames, duration={duration:.3f}s, fps={fps:.6f}')


if __name__ == '__main__':
    main()
