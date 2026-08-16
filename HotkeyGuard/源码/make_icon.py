# -*- coding: utf-8 -*-
"""生成应用图标：深色圆角方块 + 青色钥匙"""

from PIL import Image, ImageDraw

S = 256
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# 背景
d.rounded_rectangle([10, 10, S - 10, S - 10], radius=58, fill=(13, 18, 28, 255))

# 内圈青色描边（发光层次）
cx, cy = S / 2, S / 2 - 4
for r, w, col in [(56, 5, (34, 211, 238, 50)), (50, 4, (34, 211, 238, 110)), (46, 3, (34, 211, 238, 255))]:
    d.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], radius=r, outline=col, width=w)

# 钥匙：圆环 + 柄 + 齿
d.ellipse([cx - 32, cy - 36, cx + 32, cy + 28], outline=(34, 211, 238, 255), width=9)
d.rounded_rectangle([cx - 7, cy + 10, cx + 7, cy + 62], radius=7, fill=(34, 211, 238, 255))
d.rounded_rectangle([cx - 20, cy + 26, cx - 7, cy + 36], radius=4, fill=(34, 211, 238, 255))
d.rounded_rectangle([cx + 7, cy + 42, cx + 20, cy + 52], radius=4, fill=(34, 211, 238, 255))

img.save("icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.save("icon.png")
print("icon saved")
