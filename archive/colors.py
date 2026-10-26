"""Estimate a cover's dominant visual color without a remote service."""
from collections import Counter
from colorsys import rgb_to_hsv
from PIL import Image, ImageOps


def detect_color(source):
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original).convert('RGB')
        image.thumbnail((96, 96))
        counts = Counter()
        for r, g, b in image.getdata():
            h, s, v = rgb_to_hsv(r / 255, g / 255, b / 255)
            hue = h * 360
            if v < .16:
                color = 'black'
            elif s < .16:
                color = 'white' if v > .85 else 'gray'
            elif 15 <= hue < 50 and v < .68:
                color = 'brown'
            elif hue < 15 or hue >= 345:
                color = 'pink' if s < .55 and v > .7 else 'red'
            elif hue < 45:
                color = 'orange'
            elif hue < 70:
                color = 'yellow'
            elif hue < 170:
                color = 'green'
            elif hue < 260:
                color = 'blue'
            elif hue < 295:
                color = 'purple'
            else:
                color = 'pink'
            counts[color] += 1
        colorful = Counter({k: v for k, v in counts.items() if k not in ('black', 'white', 'gray')})
        total = sum(counts.values())
        chromatic = sum(colorful.values())
        if chromatic > total * .45 and sum(v > chromatic * .18 for v in colorful.values()) >= 3:
            return 'multicolor'
        if chromatic > total * .25:
            return colorful.most_common(1)[0][0]
        return counts.most_common(1)[0][0]
