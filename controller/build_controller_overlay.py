#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path
import io
from PIL import Image, ImageDraw, ImageFont

SOURCE_DIR=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='Generate Controller Overlay assets in an empty output directory.')
parser.add_argument('--output-dir', type=Path, required=True,
                    help='Destination for generated PNG, JSON and preview images (must be empty).')
ROOT=parser.parse_args().output_dir.expanduser().resolve()
if ROOT == SOURCE_DIR:
    parser.error('Refusing to overwrite the checked-in Controller assets.')
if ROOT.exists():
    if not ROOT.is_dir() or any(ROOT.iterdir()):
        parser.error('Output directory must be an empty directory.')
import cairosvg
ROOT.mkdir(parents=True, exist_ok=True)
W,H=1280,720
ATLAS_W=2048
PAD=3
C_BORDER='#AFC5D2'
C_WHITE='#F3F7FB'
C_DARK='#101923'
C_TRIGGER='#F4F7FA'  # unified with button highlight

def svg(img_body:str,w:int,h:int)->Image.Image:
    data=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{img_body}</svg>'
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=data.encode('utf-8')))).convert('RGBA')

def rect(x,y,w,h,r=8,fill='#0E1C27',fo=.73,stroke='#BDCAD2',so=.7,sw=2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" fill-opacity="{fo}" stroke="{stroke}" stroke-opacity="{so}" stroke-width="{sw}" />'

def ellipse(cx,cy,r,fill=C_DARK,fo=.80,stroke=C_BORDER,so=.72,sw=2):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" fill-opacity="{fo}" stroke="{stroke}" stroke-opacity="{so}" stroke-width="{sw}" />'

def text(x,y,s,size=31,color=C_WHITE,opacity=1,weight=650,anchor='middle'):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="DejaVu Sans,Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}" fill-opacity="{opacity}">{s}</text>'

def load_font(size: int):
    # Available on Linux and many installations of Pillow on Windows.
    for name in ('DejaVuSans.ttf', 'Arial.ttf', 'arial.ttf',
                 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()

SHELL_PATH='M 224,170 C 165,160 136,196 118,259 C 101,314 80,448 69,523 C 57,616 93,670 152,658 C 203,647 223,576 271,568 C 334,555 401,566 471,573 C 586,585 690,585 806,573 C 876,566 944,555 1007,568 C 1055,576 1077,646 1133,658 C 1191,669 1227,617 1212,523 C 1200,446 1178,314 1161,261 C 1141,192 1111,160 1053,170 C 992,183 936,162 880,153 C 758,131 535,131 410,153 C 354,162 288,183 224,170 Z'

# Opacity presets. All input sprites change alpha, not just the shell fill.
# Percentages refer to direct component fills; outline and lettering are independent.
PROFILES = {
    'standard': dict(body=.15, shell_line=.85, neutral=.20, stick=.25,
                     pressed=.80, neutral_line=.70, stick_line=.64,
                     pressed_line=.86, letter=.88, static_letter=.84, track=.15),
    'light':    dict(body=.08, shell_line=.65, neutral=.10, stick=.15,
                     pressed=.65, neutral_line=.52, stick_line=.48,
                     pressed_line=.74, letter=.78, static_letter=.73, track=.08),
}

def base_art(p:dict)->Image.Image:
    b=[];a=b.append
    a(f'<path d="{SHELL_PATH}" fill="#182733" fill-opacity="{p["body"]}" stroke="#D2E0E8" stroke-opacity="{p["shell_line"]}" stroke-width="5.2" stroke-linecap="round" stroke-linejoin="round"/>')
    # Generic HOME icon is mapped to SDL GUIDE (code 5).
    # The inert lower centre icon is intentionally omitted.
    for name,x in [('LT',171),('RT',770)]:
        a(rect(x,55,340,57,17,'#0B141F',p['body'],'#D0DCE4',p['shell_line']*.93,2.7))
        a(text(x+40,92,name,25,C_WHITE,p['static_letter']))
        a(rect(x+87,78,232,17,8,'#6D8596',p['track'],'#8098A8',p['shell_line']*.33,1.0))
    for x,y in [(282,306),(798,475)]:
        a(ellipse(x,y,88,'#12232E',p['stick']*.43,'#AFC3CF',p['stick_line'],3.2))
        a(ellipse(x,y,73,'#111E28',p['stick']*.35,'#8FA5B4',p['stick_line']*.75,2.2))
    # D-pad backing aligned with right-stick centre; no changes in position.
    a(ellipse(489,475,95,'#0F1C27',p['neutral']*.6,'#AFC4D0',p['neutral_line']*.85,3.1))
    return svg(''.join(b),W,H)

def home_guide_button(p:dict, active=False)->Image.Image:
    """Generic HOME pictogram for SDL GUIDE (code 5). Both states are 84 px."""
    d=84; c=d/2
    fill = '#F2F6F9' if active else '#0F1A23'
    opacity = p['pressed'] if active else p['neutral']
    edge = p['pressed_line'] if active else p['neutral_line']
    logo_color = '#1A2933' if active else '#D5E4ED'
    logo_alpha = p['letter'] if active else p['static_letter']
    art = [
        ellipse(c,c,39,fill,opacity,'#FFFFFF' if active else '#CBDAE2',edge,3.2),
        ellipse(c,c,26,'#EDF3F7' if active else '#DCEAF3',
                p['pressed']*.85 if active else p['neutral']*.88,
                '#FFFFFF' if active else '#EFF6FB',edge*.85,1.8),
        # Original geometric drawing: roof, body and door; unrelated to manufacturer marks.
        f'<path d="M 23 43 L 42 27 L 61 43 M 29 40 V 60 H 55 V 40 '
        f'M 38 60 V 47 H 46 V 60" fill="none" stroke="{logo_color}" '
        f'stroke-opacity="{logo_alpha}" stroke-width="4.3" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
    ]
    return svg(''.join(art), d,d)

def circle_button(letter:str,p:dict,d:int=86,active=False)->Image.Image:
    m=d/2;a=[]
    if active:
        a.append(ellipse(m,m,m-7,'#EFF4F7',p['pressed'],'#FFFFFF',p['pressed_line'],3.0))
        a.append(ellipse(m,m,m-3,'none',0,'#E1EFF8',p['pressed_line']*.45,1.4))
        a.append(text(m,m+13,letter,38,'#172634',p['letter']*.98,750))
    else:
        a.append(ellipse(m,m,m-7,'#0D1821',p['neutral'],'#B7C8D3',p['neutral_line'],2.8))
        a.append(text(m,m+13,letter,38,C_WHITE,p['letter'],700))
    return svg(''.join(a),d,d)

def bumper(label:str,p:dict,w=168,h=58,active=False):
    fill='#F2F6F9' if active else '#0F1923'
    alpha=p['pressed'] if active else p['neutral']
    edge=p['pressed_line'] if active else p['neutral_line']
    col='#142532' if active else C_WHITE
    return svg(rect(5,5,w-10,h-10,13,fill,alpha,'#FFFFFF' if active else '#BACBD6',edge,2.7)+text(w/2,h/2+11,label,30,col,p['letter'],750),w,h)

def small_btn(symbol:str,p:dict,w=57,h=49,active=False):
    fill='#F0F4F7' if active else '#12232C'
    alpha=p['pressed'] if active else p['neutral']
    edge=p['pressed_line'] if active else p['neutral_line']
    col='#17222F' if active else C_WHITE
    return svg(rect(4,4,w-8,h-8,13,fill,alpha,'#FFFFFF' if active else '#B4C7D0',edge,2.1)+text(w/2,h/2+9,symbol,25,col,p['letter'],700),w,h)

def dpad_arrow(direction:str,p:dict,active=False):
    d={'up':'M 30 12 L 12 39 L 48 39 Z','down':'M 12 21 L 48 21 L 30 48 Z','left':'M 12 30 L 40 12 L 40 48 Z','right':'M 48 30 L 20 12 L 20 48 Z'}
    fill='#F3F6F8' if active else '#121D27'
    alpha=p['pressed'] if active else p['neutral']
    edge=p['pressed_line'] if active else p['neutral_line']
    # Triangle also remains partially transparent, including during press.
    ico=C_DARK if active else C_WHITE
    ico_alpha=p['letter'] if active else p['letter']
    return svg(rect(3.5,3.5,53,53,10,fill,alpha,'#FFFFFF' if active else '#A5BAC7',edge,2.1)+f'<path d="{d[direction]}" fill="{ico}" fill-opacity="{ico_alpha}"/>',60,60)

def stick_cap(p:dict,active=False):
    d=130;c=65
    face='#F0F5F9' if active else '#304654'
    sub='#EDF3F7' if active else '#3D5563'
    a=p['pressed'] if active else p['stick']*.51
    # Sub-circles are faint; never become an opaque disk when at rest.
    b=p['pressed']*.38 if active else p['stick']*.41
    core=p['pressed']*.16 if active else p['stick']*.19
    edge=p['pressed_line'] if active else p['stick_line']
    s=[ellipse(c,c,56,face,a,'#FFFFFF' if active else '#B1C6D0',edge,3.0)]
    s.append(ellipse(c,c,45,sub,b,'#CADAE4' if active else '#9BAFBD',edge*.52,1.8))
    s.append(ellipse(c,c,30,'#FFFFFF' if active else '#324956',core,'none',0,0))
    return svg(''.join(s),d,d)

def trigger_gauge(p:dict):
    # Exact original geometry; only RGBA opacity changes.
    return svg(rect(0.5,0.5,231,16,7,C_TRIGGER,p['pressed'],C_TRIGGER,p['pressed_line']*.7,0.5),232,17)

class Atlas:
    def __init__(self,body):
        self.im=Image.new('RGBA',(ATLAS_W,2048),(0,0,0,0))
        self.im.alpha_composite(body,(0,0))
        self.elements=[{'id':'body','mapping':[0,0,W,H],'pos':[0,0],'type':0,'z_level':0}]
        self.x=8;self.y=H+20;self.shelf_h=0;self.sprites={}
    def pair(self,id,normal,active,pos,type,code=None,side=None,stick_radius=None,trigger_mode=None,direction=None,z=2):
        tw,th=normal.size; tile_h=th*2+PAD
        if self.x+tw+8>ATLAS_W:
            self.x=8;self.y+=self.shelf_h+13;self.shelf_h=0
        if self.y+tile_h>=2048: raise RuntimeError(f'atlas full {id}')
        self.im.alpha_composite(normal,(self.x,self.y)); self.im.alpha_composite(active,(self.x,self.y+th+PAD))
        p={'id':id,'mapping':[self.x,self.y,tw,th],'pos':list(pos),'type':type,'z_level':z}
        if code is not None: p['code']=code
        if side is not None: p['side']=side
        if stick_radius is not None: p['stick_radius']=stick_radius
        if trigger_mode is not None: p['trigger_mode']=trigger_mode
        if direction is not None: p['direction']=direction
        self.elements.append(p); self.sprites[id]=(normal,active)
        self.x+=tw+12; self.shelf_h=max(self.shelf_h,tile_h)
    def finish(self,path):
        h=self.y+self.shelf_h+12
        self.im=self.im.crop((0,0,ATLAS_W,h)); self.im.save(path,optimize=True); return path

BUTTONS=[('a','A',0,(980,436)),('b','B',1,(1049,365)),('x','X',2,(911,365)),('y','Y',3,(980,292))]
DIRECTIONS=[('up',11,(459,379)),('down',12,(459,511)),('left',13,(393,445)),('right',14,(525,445))]

def make_atlas(profile_name:str,out:str):
    p=PROFILES[profile_name]
    aa=Atlas(base_art(p))
    for id,label,code,pos in BUTTONS:
        aa.pair(id,circle_button(label,p),circle_button(label,p,active=True),pos,2,code=code)
    for id,code,pos in DIRECTIONS:
        aa.pair('dpad_'+id,dpad_arrow(id,p),dpad_arrow(id,p,True),pos,2,code=code)
    for id,label,code,pos in [('lb','LB',9,(238,106)),('rb','RB',10,(874,106))]:
        aa.pair(id,bumper(label,p),bumper(label,p,active=True),pos,2,code=code)
    for id,label,code,pos in [('view','◻',4,(555,289)),('menu','≡',6,(661,289))]:
        aa.pair(id,small_btn(label,p),small_btn(label,p,active=True),pos,2,code=code)
    for id,side,pos in [('l_stick',0,(217,241)),('r_stick',1,(733,410))]:
        aa.pair(id,stick_cap(p),stick_cap(p,True),pos,5,side=side,stick_radius=27,z=3)
    for id,side,pos in [('lt',0,(258,78)),('rt',1,(857,78))]:
        aa.pair(id,Image.new('RGBA',(232,17)),trigger_gauge(p),pos,6,side=side,trigger_mode=False,direction=4,z=4)
    # Last tile: all pre-existing v4.3 texture mapping coordinates are unchanged.
    # GUIDE uses the same coordinates, dimensions and z-layer as before.
    aa.pair('home_guide',home_guide_button(p),home_guide_button(p,True),
            (597,196),2,code=5,z=2)
    path=ROOT/out
    aa.finish(path)
    layout={'default_height':0,'default_width':0,'elements':aa.elements,'flags':7,'overlay_height':H,'overlay_width':W,'space_h':0,'space_v':0,'version':508}
    return aa,layout

def preview(a:Atlas,states:dict,axes:dict,lt=0.0,rt=0.0):
    out=Image.new('RGBA',(W,H)); out.alpha_composite(a.im.crop((0,0,W,H)))
    for e in sorted(a.elements[1:],key=lambda e:e['z_level']):
        id=e['id']; normal,active=a.sprites[id]; x,y=map(int,e['pos'])
        if e['type']==5:
            dx,dy=axes.get(id,(0,0)); x+=int(dx*e['stick_radius']); y+=int(dy*e['stick_radius'])
        if e['type']==6:
            v=lt if id=='lt' else rt; cw=int(round(v*active.width))
            if cw: out.alpha_composite(active.crop((0,0,cw,active.height)),(x,y))
            continue
        out.alpha_composite(active if states.get(id,False) else normal,(x,y))
    return out

main,layout=make_atlas('standard','controller_atlas.png')
light,layout2=make_atlas('light','controller_atlas_light.png')
assert layout==layout2
(ROOT/'controller_layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
body=Image.open(ROOT/'controller_atlas.png').convert('RGBA')
for e in layout['elements']:
    x,y,w,h=e['mapping']; px,py=e['pos']
    assert x>=0 and y>=0 and x+w<=body.width and y+h<=body.height
    assert px>=0 and py>=0 and px+w<=W and py+h<=H
    if e['type']!=0:
        assert y+h+PAD+h<=body.height
        n=body.crop((x,y,x+w,y+h)); a=body.crop((x,y+h+PAD,x+w,y+h+PAD+h))
        assert a.getbbox(), e['id']
        if e['type']!=6: assert n.getbbox(), e['id']
        assert n.tobytes()!=a.tobytes(), e['id']
assert 410+65 == 475
for i,(n1,_,p1) in enumerate(DIRECTIONS):
    x1,y1=p1; box1=(x1,y1,x1+60,y1+60)
    for n2,_,p2 in DIRECTIONS[i+1:]:
        x2,y2=p2; box2=(x2,y2,x2+60,y2+60)
        ix=max(0,min(box1[2],box2[2])-max(box1[0],box2[0])); iy=max(0,min(box1[3],box2[3])-max(box1[1],box2[1]))
        assert ix==0 or iy==0, (n1,n2,ix,iy)

idle=preview(main,{},{}); idle.save(ROOT/'preview_idle.png')
test=preview(main,{'a':True,'lb':True,'r_stick':True,'dpad_up':True,'home_guide':True},{'l_stick':(.63,-.43),'r_stick':(-.4,.8)},lt=.48,rt=.81); test.save(ROOT/'preview_test.png')
back=Image.new('RGBA',(W,H),(45,62,76,255)); d=ImageDraw.Draw(back)
for i in range(7):
    x=24+i*199; d.rounded_rectangle((x,145+(i%2)*90,x+124,560+(i%3)*23),radius=19,fill=(60+i*2,78+i*2,88+i,255))
for name,im in [('preview_idle_on_scene.png',idle),('preview_test_on_scene.png',test)]:
    Image.alpha_composite(back,im).save(ROOT/name)
L=Image.open(ROOT/'preview_idle_on_scene.png').convert('RGB'); R=Image.open(ROOT/'preview_test_on_scene.png').convert('RGB')
comp=Image.new('RGB',(1280,786),(13,21,30)); d=ImageDraw.Draw(comp); font=load_font(20)
for i,(title,im) in enumerate([('IDLE',L),('INPUT TEST (LT 48% / RT 81%)',R)]):
    comp.paste(im.resize((640,360),Image.Resampling.LANCZOS),(i*640,82)); d.rectangle((i*640,62,i*640+640,82),fill=(13,21,30)); d.text((i*640+12,30),title,font=font,fill=(236,244,249))
comp.save(ROOT/'comparison.png')
print(ROOT)
