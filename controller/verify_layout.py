#!/usr/bin/env python3
"""Standalone v4.5 PNG atlas + Input Overlay JSON sanity check.

Requires Pillow, no OBS process and no external network resources.
"""
from pathlib import Path
import json
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parent
layout = json.loads((ROOT / 'controller_layout.json').read_text(encoding='utf-8'))
standard = Image.open(ROOT / 'controller_atlas.png').convert('RGBA')
light = Image.open(ROOT / 'controller_atlas_light.png').convert('RGBA')

assert layout['version'] == 508
assert len(layout['elements']) == 18
assert standard.size == light.size
assert ImageChops.subtract(light.getchannel('A'), standard.getchannel('A')).getbbox() is None, \
       'Light atlas must not be more opaque than standard at any pixel'

for e in layout['elements']:
    x, y, w, h = e['mapping']
    px, py = e['pos']
    assert x >= 0 and y >= 0 and x + w <= standard.width and y + h <= standard.height, e['id']
    assert px >= 0 and py >= 0 and px + w <= layout['overlay_width'] and py + h <= layout['overlay_height'], e['id']
    if e['type'] == 0:
        continue
    assert y + 2*h + 3 <= standard.height, e['id']
    neutral = standard.crop((x,y,x+w,y+h)).getchannel('A')
    active = standard.crop((x,y+h+3,x+w,y+2*h+3)).getchannel('A')
    assert active.getbbox() is not None, e['id']
    if e['type'] != 6:
        assert neutral.getbbox() is not None, e['id']
        assert ImageStat.Stat(active).mean[0] > ImageStat.Stat(neutral).mean[0], e['id']

by_id = {e['id']: e for e in layout['elements']}
assert by_id['dpad_up']['pos'] == [459,379]
assert by_id['r_stick']['pos'][1] + 65 == 475
assert by_id['lt']['direction'] == by_id['rt']['direction'] == 4
assert by_id['lt']['side'] == 0 and by_id['rt']['side'] == 1
assert by_id['a']['code'] == 0
assert by_id['lb']['code'] == 9
assert by_id['home_guide']['code'] == 5 and by_id['home_guide']['type'] == 2
assert by_id['home_guide']['pos'] == [597, 196]
print('PASS — 18 valid elements, mapped GUIDE pressed sprite, bounds and lighter light preset')
