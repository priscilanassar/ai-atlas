"""The original dense globe outline, with unique works spread across its mesh."""
from math import sqrt
from random import Random


def build_globe_tiles(projects):
    resolution = 61
    random = Random(42)
    while True:
        tiles = []
        half = (resolution - 1) / 2
        for row in range(resolution):
            y = (row - half) / half
            for column in range(resolution):
                x = (column - half) / half
                radius = sqrt(x * x + y * y)
                if radius > 1:
                    continue
                meridian = .52 * sqrt(max(0, 1 - y * y))
                if not (radius > .88 or abs(x) < .055 or
                        abs(abs(x) - meridian) < .06 or
                        min(abs(y), abs(y - .5), abs(y + .5)) < .055):
                    continue
                tiles.append(dict(project=None, x=round(50 + x * 44, 3),
                                  y=round(50 + y * 44, 3),
                                  size=round(88 / (resolution - 1) * .96, 3),
                                  tone=random.randrange(8), number=f'{len(tiles) + 1:03}'))
        if len(tiles) >= len(projects):
            break
        resolution += 2
    for index, project in enumerate(projects):
        slot = round(index * (len(tiles) - 1) / max(1, len(projects) - 1))
        tiles[slot]['project'] = project
    return tiles
