#!/usr/bin/env python3
"""Offline structural and visual-state checks for the Sara B-trigger controller skin.

Does not require OBS. Tests cannot verify actual plugin rendering or gamepad events.
"""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path
from PIL import Image, ImageChops, ImageStat, ImageDraw
from build_sara_overlay import simulate, OVERLAY, SIZE, POS

ROOT = Path(__file__).resolve().parent
orig = json.loads((ROOT/'controller_layout.json').read_text('utf-8'))
layout = json.loads((ROOT/'controller_layout_sara.json').read_text('utf-8'))
assert layout['overlay_width']==1280 and layout['overlay_height']==720
assert layout['version']==508
old = {e['id']:e for e in orig['elements']}
new = {e['id']:e for e in layout['elements']}
assert set(old)==set(new) and len(old)==18
for name in old:
    for field in ('id','type','code','side','trigger_mode','direction','stick_radius'):
        assert old[name].get(field)==new[name].get(field),(name,field)
assert new['lb']['code']==9 and new['rb']['code']==10
assert new['home_guide']['code']==5
assert new['lt']['type']==new['rt']['type']==6
assert new['l_stick']['type']==new['r_stick']['type']==5
assert new['lt']['pos']==[437,125] and new['rt']['pos']==[651,125]
assert new['view']['pos']==[526,246] and new['menu']['pos']==[686,246]
assert new['view']['mapping'][2:]==new['menu']['mapping'][2:]==[70,48]
assert abs((new['view']['pos'][0]+35)+(new['menu']['pos'][0]+35)-2*(new['home_guide']['pos'][0]+36))<=2
assert new['home_guide']['pos'][1]==331
# The two new trigger tracks sit exactly between, and cannot overlap, the ears.
for left,right in [('lb','lt'),('rt','rb'),('lt','rt')]:
    le,re = new[left],new[right]
    a=le['pos']; b=re['pos']
    aw,ah=le['mapping'][2:];bw,bh=re['mapping'][2:]
    assert a[0]+aw <= b[0] or b[0]+bw <= a[0] or a[1]+ah <= b[1] or b[1]+bh <= a[1],(left,right)
assert new['lt']['pos'][1]+46 < 198 and new['rt']['pos'][1]+46 < 198

images={}
for mode in ('sara','sara_rta'):
    file=ROOT/f'controller_atlas_{mode}.png'
    with Image.open(file) as x:
        assert x.mode=='RGBA' and x.size==(2048,1510) and x.format=='PNG'
        atlas=x.copy()
    images[mode]=atlas
    allowed=Image.new('L',atlas.size)
    drawer=ImageDraw.Draw(allowed)
    for e in layout['elements']:
        name=e['id'];x,y,w,h=e['mapping'];px,py=e['pos']
        assert 0<=x and 0<=y and x+w<=2048 and y+h<=1510
        assert 0<=px and 0<=py and px+w<=1280 and py+h<=720
        drawer.rectangle((x,y,x+w-1,y+h-1),fill=255)
        if e['type']==0:continue
        assert y+2*h+3<=1510
        drawer.rectangle((x,y+h+3,x+w-1,y+2*h+2),fill=255)
        idle=atlas.crop((x,y,x+w,y+h))
        active=atlas.crop((x,y+h+3,x+w,y+2*h+3))
        assert active.getchannel('A').getbbox() is not None,(mode,name,'active blank')
        if e['type']==6:
            assert idle.getchannel('A').getbbox() is None,(mode,name,'neutral trigger non-empty')
            for fraction in (0.2,0.48,0.81,1.0):
                cw=round(w*fraction)
                assert active.crop((0,0,cw,h)).getchannel('A').getbbox() is not None
        else:
            assert idle.getchannel('A').getbbox() is not None,(mode,name,'neutral blank')
            assert ImageChops.difference(idle,active).getbbox() is not None,(mode,name,'same states')
            assert ImageStat.Stat(active.getchannel('A')).mean[0] > ImageStat.Stat(idle.getchannel('A')).mean[0],(mode,name,'not brighter')
    assert ImageChops.subtract(atlas.getchannel('A'),allowed).getbbox() is None,(mode,'unmapped pixels')
    for xy in [(0,0),(1279,0),(0,719),(1279,719)]:
        assert atlas.getchannel('A').getpixel(xy)==0
    for side in ('l_stick','r_stick'):
        e=new[side];x,y,w,h=e['mapping']
        color=atlas.getpixel((x+64,y+h+3+79))
        assert max(color[:3]) < 85,(mode,side,'pressed paw not dark',color)
    for key in ('lt','rt'):
        e=new[key]
        assert e['direction']==4 and e['trigger_mode'] is False
        x,y,w,h=e['mapping']
        a=atlas.crop((x,y+h+3,x+w,y+2*h+3))
        bbox=a.getchannel('A').getbbox()
        assert bbox[0] < 24 and bbox[2] > 166,(mode,key,bbox)
    idle=simulate(atlas,layout)
    assert idle.size==OVERLAY
    pressed=simulate(atlas,layout,buttons={'lb','rb','home_guide','a','r_stick'},axes={'l_stick':(.6,-.33)},triggers={'lt':.48,'rt':.81})
    assert ImageChops.difference(idle,pressed).getbbox() is not None
    for name in ('l_stick','r_stick'):
        e=new[name]
        cx=e['pos'][0]+e['mapping'][2]/2;cy=e['pos'][1]+e['mapping'][3]/2
        radius=e['stick_radius'];capradius=58
        targets=('a','b','x','y','view','menu','home_guide') if name=='r_stick' else ('dpad_up','dpad_down','dpad_left','dpad_right')
        for target in targets:
            e2=new[target];tx=e2['pos'][0]+e2['mapping'][2]/2;ty=e2['pos'][1]+e2['mapping'][3]/2
            tr=(31 if target in ('a','b','x','y','home_guide') else 29 if target.startswith('dpad_') else 24)
            assert math.hypot(cx-tx,cy-ty)>radius+capradius+tr,(name,target,'stick movement collision')
alpha1=images['sara'].getpixel((640,525))[3]
alpha2=images['sara_rta'].getpixel((640,525))[3]
assert 200<=alpha1<=240 and 25<=alpha2<=65 and alpha2<alpha1
print('PASS — 18 input definitions, 2 RGBA atlases, ear press states, B trigger gauges, mouth/HOME, stick movement clearance, RTA alpha')
print(f'Body alpha regular/RTA: {alpha1}/{alpha2}')
for name in ('controller_atlas_sara.png','controller_atlas_sara_rta.png','controller_layout_sara.json'):
 print(name,hashlib.sha256((ROOT/name).read_bytes()).hexdigest())
