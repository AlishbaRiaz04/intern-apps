from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent.parent
out_dir = root / 'assets' / 'generated'
out_dir.mkdir(parents=True, exist_ok=True)

# Create a simple branded icon with a snake-like motif
for size in [48, 72, 96, 144, 192]:
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bg = (16, 32, 16, 255)
    draw.rounded_rectangle((2, 2, size - 2, size - 2), radius=size // 6, fill=(30, 120, 60, 255))
    # snake body
    body = [(size // 2 + 6, size // 2 - 4), (size // 2 + 16, size // 2 - 4), (size // 2 + 26, size // 2 + 6), (size // 2 + 14, size // 2 + 16), (size // 2 - 6, size // 2 + 16)]
    draw.line(body, fill=(130, 255, 80, 255), width=max(6, size // 10), joint='curve')
    # head
    draw.ellipse((size // 2 + 18, size // 2 - 8, size // 2 + 30, size // 2 + 4), fill=(220, 255, 180, 255))
    draw.ellipse((size // 2 + 23, size // 2 - 3, size // 2 + 26, size // 2 + 0), fill=(20, 20, 20, 255))
    img.save(out_dir / f'icon_{size}.png')

# Create splash image
splash = Image.new('RGBA', (1024, 1024), (16, 24, 18, 255))
draw = ImageDraw.Draw(splash)
# Outer rounded panel
panel = (60, 60, 964, 964)
draw.rounded_rectangle(panel, radius=80, fill=(24, 48, 36, 255))
# Snake
body_points = [(260, 560), (360, 560), (460, 650), (620, 650), (720, 560), (840, 560)]
draw.line(body_points, fill=(120, 255, 90, 255), width=70, joint='curve')
# Head
head = (840, 560)
draw.ellipse((780, 500, 900, 620), fill=(220, 255, 180, 255))
# Eyes
for x, y in [(810, 530), (835, 530)]:
    draw.ellipse((x, y, x + 18, y + 18), fill=(20, 20, 20, 255))
# Food
for x, y in [(270, 300), (370, 330), (500, 280)]:
    draw.ellipse((x - 36, y - 36, x + 36, y + 36), fill=(255, 80, 80, 255))
# Text
try:
    from PIL import ImageFont
    font = ImageFont.load_default()
    draw.text((220, 100), 'Snake App', fill=(255, 255, 255, 255), font=font)
except Exception:
    pass
splash.save(out_dir / 'splash.png')
print('Generated assets in', out_dir)
