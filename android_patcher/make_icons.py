"""Builds the Android launcher icons from icon_source.webp (the artwork the project owner supplied).
usage: py make_icons.py
 - res/mipmap-*dpi/ic_launcher.png      full artwork, for Android 7 and as the round/legacy fallback
 - res/drawable-nodpi/ic_launcher_foreground.png   artwork scaled into the adaptive-icon safe zone (Android 8+)
 - res/values/colors.xml                background colour of the adaptive icon (the gold frame colour)"""
import sys
from pathlib import Path
from PIL import Image

H = Path(__file__).parent
src = Image.open(H / 'icon_source.webp').convert('RGBA')
print('source', src.size, 'corner alpha', src.getpixel((2, 2))[3])
RES = H / 'app/src/main/res'

# legacy / fallback icons
for name, px in (('mdpi', 48), ('hdpi', 72), ('xhdpi', 96), ('xxhdpi', 144), ('xxxhdpi', 192)):
    d = RES / f'mipmap-{name}'
    d.mkdir(parents=True, exist_ok=True)
    src.resize((px, px), Image.LANCZOS).save(d / 'ic_launcher.png')

# adaptive foreground: 108dp canvas drawn at 4x (432 px); the visible mask is about 72dp, so the artwork goes into the centre 66 %
canvas = 432
art = int(canvas * 0.66)
fg = Image.new('RGBA', (canvas, canvas), (0, 0, 0, 0))
fg.alpha_composite(src.resize((art, art), Image.LANCZOS), ((canvas - art) // 2, (canvas - art) // 2))
(RES / 'drawable-nodpi').mkdir(parents=True, exist_ok=True)
fg.save(RES / 'drawable-nodpi/ic_launcher_foreground.png')

# frame colour = the gold border, sampled in the middle of the left edge
w, h = src.size
samples = [src.getpixel((x, h // 2)) for x in range(int(w * 0.015), int(w * 0.04))]
r = sum(s[0] for s in samples) // len(samples); g = sum(s[1] for s in samples) // len(samples); b = sum(s[2] for s in samples) // len(samples)
colour = '#%02X%02X%02X' % (r, g, b)
(RES / 'values').mkdir(parents=True, exist_ok=True)
(RES / 'values/colors.xml').write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">%s</color>\n</resources>\n' % colour, encoding='utf-8')
print('background colour', colour)
