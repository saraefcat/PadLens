#!/usr/bin/env python3
"""Build functional Sara Controller variants with subtle View/Menu eye-shaped controls.

Dependencies for regeneration: Pillow and CairoSVG. No third-party artwork or
manufacturer logos; paths and shapes are independently authored vector geometry.
Run: python build_sara_overlay.py --output-dir <empty-directory>.
Reads the stable `controller_layout.json` without modifying it.
"""
from __future__ import annotations
import argparse, io, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ORIG=HERE/'controller_layout.json'
ATLAS=(2048,1510)
OVERLAY=(1280,720)
PAD=3
GOLD='#BCA15E'; LIGHT='#D2BD78'; OLIVE='#99915D'; DARK_GOLD='#79643C'
NAVY='#0D1626'; MID='#192538'; DEEP='#080F1B'; IVORY='#FFF2D3'; BLACK_PAW='#202226'
PROFILES={
 'sara':dict(body=.91,edge=.93,neutral=.84,active=.99,decoration=.90,glass=.96,eye=.99,ear=.97),
 'sara_rta':dict(body=.15,edge=.82,neutral=.20,active=.82,decoration=.75,glass=.55,eye=.92,ear=.33)
}
HEADER=f'''<defs>
<linearGradient id="coat" x1="0" y1="0" x2=".87" y2="1" gradientUnits="objectBoundingBox"><stop offset="0" stop-color="#18283B"/><stop offset=".46" stop-color="#0D1726"/><stop offset="1" stop-color="#070D18"/></linearGradient>
<linearGradient id="gold" x1="0" y1="0" x2=".9" y2=".9"><stop offset="0" stop-color="{LIGHT}"/><stop offset=".5" stop-color="{GOLD}"/><stop offset="1" stop-color="{DARK_GOLD}"/></linearGradient>
<radialGradient id="iris"><stop offset="0" stop-color="{LIGHT}"/><stop offset=".42" stop-color="{GOLD}"/><stop offset=".77" stop-color="{OLIVE}"/><stop offset="1" stop-color="{DARK_GOLD}"/></radialGradient>
<linearGradient id="press" x1="0" y1="0" x2=".85" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="{IVORY}"/></linearGradient>
</defs>'''

def svg(content,w,h):
    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError('Regeneration requires CairoSVG in the selected Python environment') from exc
    s=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{HEADER}{content}</svg>'
    result=cairosvg.svg2png(bytestring=s.encode('utf-8'),output_width=w*2,output_height=h*2)
    return Image.open(io.BytesIO(result)).convert('RGBA').resize((w,h),Image.Resampling.LANCZOS)

def label(x,y,t,size=25,color=IVORY,opacity=1,weight=700):
    # Using system font by family, without bundling any font file.
    return f'<text x="{x}" y="{y}" font-family="Arial,DejaVu Sans,sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="middle" dominant-baseline="middle" fill="{color}" fill-opacity="{opacity}">{t}</text>'

# The bottom and cheek contour is based on the user's rounded-cat design reference,
# without copying the 2D scene image or its other objects into the atlas.
SHELL='''M 255,198
C 208,194 165,238 144,305
C 113,400 102,480 124,561
C 141,623 181,651 216,617
C 255,578 260,562 333,565
C 449,583 539,576 640,578
C 741,576 831,583 947,565
C 1020,562 1025,578 1064,617
C 1099,651 1139,623 1156,561
C 1178,480 1167,400 1136,305
C 1115,238 1072,194 1025,198
C 980,191 943,182 890,195
C 813,203 744,187 640,193
C 536,187 467,203 390,195
C 337,182 300,191 255,198 Z'''

def trigger_track(x,y,p):
    """Static B-style oval trigger housing (outside the body, between ears)."""
    return f'''<rect x="{x+3}" y="{y+7}" width="186" height="30" rx="15"
         fill="{DEEP}" fill-opacity="{max(p['neutral'], p['body']*.75)}"
         stroke="{GOLD}" stroke-opacity="{p['edge']}" stroke-width="3"/>
        <rect x="{x+10}" y="{y+14}" width="172" height="16" rx="8"
         fill="{DARK_GOLD}" fill-opacity="{p['decoration']*.28}"/>
    '''


def trigger_fill(p):
    """One full-width active bar, cropped horizontally by Input Overlay type=6.

    Its left-to-right proportional fill intentionally has a straight cut at
    intermediate inputs; the stationary B-style housing remains visible.
    """
    s=f'''<rect x="10" y="14" width="172" height="16" rx="8"
          fill="{IVORY}" fill-opacity="{p['active']}"/>
        <rect x="11" y="15" width="170" height="5" rx="2.5"
          fill="{LIGHT}" fill-opacity="{p['active']*.55}"/>'''
    return svg(s,192,46)


def body(p):
    edge=p['edge']; alpha=p['body']; dec=p['decoration']
    # Single outside contour only. No parallel decoration lines at shoulders,
    # sides or the lower grips (the regions marked red by the user).
    s=f'''<path d="{SHELL}" fill="url(#coat)" fill-opacity="{alpha}"
        stroke="{GOLD}" stroke-opacity="{edge}" stroke-width="4"
        stroke-linejoin="round"/>'''
    # No extra facial eye/nose artwork: View/Menu are subtle eyes, HOME is the nose.
    for side in (-1,1):
        if side<0:
            lines=['M 539 307 Q 508 302 467 292','M 537 322 Q 495 322 456 322','M 539 337 Q 503 342 469 352']
        else:
            lines=['M 741 307 Q 772 302 813 292','M 743 322 Q 785 322 824 322','M 741 337 Q 777 342 811 352']
        for path in lines:
            s+=f'<path d="{path}" fill="none" stroke="{GOLD}" stroke-opacity="{dec*.82}" stroke-width="2" stroke-linecap="round"/>'
    # Rounded B-style LT/RT bars, centered BETWEEN the cat ears and located
    # completely above the static head outline. Labels are on the body layer.
    for n in ('lt','rt'):
        x,y=POS[n]
        s+=trigger_track(x,y,p)
        s+=label(x+96,y-12,n.upper(),23,LIGHT,p['glass'])
    for x,y in [(322,359),(785,465)]:
        s+=f'<circle cx="{x}" cy="{y}" r="82" fill="{DEEP}" fill-opacity="{p["neutral"]*.58}" stroke="{GOLD}" stroke-opacity="{edge}" stroke-width="3"/>'
        s+=f'<circle cx="{x}" cy="{y}" r="72" fill="none" stroke="{LIGHT}" stroke-opacity="{dec*.46}" stroke-width="1.7"/>'
    s+=f'<circle cx="470" cy="474" r="89" fill="{DEEP}" fill-opacity="{p["neutral"]*.53}" stroke="{GOLD}" stroke-opacity="{edge}" stroke-width="2.5"/>'
    return svg(s,*OVERLAY)


def ear(p,pressed,side):
    # Short, round-tipped ears nest into the existing curved head silhouette.
    w,h=156,136
    mirror=f'translate({w} 0) scale(-1 1)' if side=='rb' else ''
    stroke=IVORY if pressed else GOLD
    s=f'''<g transform="{mirror}">
        <path d="M 6 128 C 15 98 43 52 67 27 Q 80 11 93 27 C 119 56 145 96 150 128
                 Q 83 115 6 128 Z" fill="url(#coat)" fill-opacity="{max(p['ear'],p['body'])}"/>
        <path d="M 6 128 C 15 98 43 52 67 27 Q 80 11 93 27 C 119 56 145 96 150 128"
              fill="none" stroke="{stroke}" stroke-opacity="{p['edge']}" stroke-width="{5 if pressed else 3.5}" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M 34 114 Q 52 72 80 48 Q 109 75 128 114 Q 83 109 34 114 Z"
              fill="{IVORY if pressed else DARK_GOLD}" fill-opacity="{p['active']*.92 if pressed else p['decoration']*.76}"/>
       </g>'''
    # Explicit letters remain visible at OBS stream scale.
    s+=label(78,104,'LB' if side=='lb' else 'RB',21,DEEP if pressed else IVORY,1 if pressed else p['glass'])
    return svg(s,w,h)



def circle_button(p,pressed,txt,d=82):
    op=p['active'] if pressed else p['neutral']
    co=IVORY if pressed else DEEP
    edge=IVORY if pressed else GOLD
    txtcolor=DEEP if pressed else IVORY
    s=f'''<circle cx="{d/2}" cy="{d/2}" r="{d/2-6}" fill="{co}" fill-opacity="{op}" stroke="{edge}" stroke-opacity="{p['edge']}" stroke-width="3"/>
    <circle cx="{d/2}" cy="{d/2}" r="{d/2-12}" fill="none" stroke="{GOLD}" stroke-opacity="{p['decoration']*.6}" stroke-width="1.5"/>'''
    s+=label(d/2,d/2+2,txt,34,txtcolor,1 if pressed else p['glass'])
    return svg(s,d,d)

def dpad(p,pressed,direction):
    d=60; op=p['active'] if pressed else p['neutral']
    s=f'<rect x="3" y="3" width="54" height="54" rx="10" fill="{IVORY if pressed else DEEP}" fill-opacity="{op}" stroke="{IVORY if pressed else GOLD}" stroke-opacity="{p["edge"]}" stroke-width="2.3"/>'
    paths={'up':'M 30 12 L 13 42 L 47 42 Z', 'down':'M 13 18 L 47 18 L 30 48 Z','left':'M 12 30 L 43 12 L 43 48 Z','right':'M 48 30 L 17 12 L 17 48 Z'}
    s+=f'<path d="{paths[direction]}" fill="{DEEP if pressed else LIGHT}" fill-opacity="{1 if pressed else p["glass"]}"/>'
    return svg(s,60,60)

def paw(p,pressed):
    d=128; op=p['active'] if pressed else p['neutral']
    s=f'<circle cx="64" cy="64" r="58" fill="{IVORY if pressed else MID}" fill-opacity="{op}" stroke="{IVORY if pressed else GOLD}" stroke-opacity="{p["edge"]}" stroke-width="3.5"/>'
    s+=f'<circle cx="64" cy="64" r="47" fill="none" stroke="{GOLD}" stroke-opacity="{p["decoration"]*.7}" stroke-width="1.8"/>'
    pad=BLACK_PAW if pressed else GOLD
    s+=f'<path d="M 41 83 C 40 72 50 65 57 62 C 62 57 70 57 75 62 C 82 65 91 74 87 83 C 85 92 77 91 67 88 C 57 87 47 93 41 87 Z" fill="{pad}" fill-opacity="{1 if pressed else p["glass"]}"/>'
    for x,y,rx,ry,rot in [(34,59,8,12,-24),(50,43,8,12,-12),(77,43,8,12,12),(94,59,8,12,24)]:
        s+=f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" transform="rotate({rot} {x} {y})" fill="{pad}" fill-opacity="{1 if pressed else p["glass"]}"/>'
    return svg(s,d,d)

def small(p,pressed,symbol):
    """View/Menu as understated, mirrored almond-shaped cat eyes.

    The original overlapping-rectangles and menu-lines icons remain readable.
    These are the *only* eyes: no static eye graphic is drawn on the shell.
    """
    w,h=70,48
    op=p['active'] if pressed else p['neutral']
    ink=DEEP if pressed else LIGHT
    fill=IVORY if pressed else DEEP
    edge=IVORY if pressed else GOLD
    # The two points gently taper without an aggressive feline pupil or eyelash.
    # The slight upper/lower asymmetry gives a soft gaze rather than cartoon eyes.
    path=('M 5 22 C 20 12 43 10 65 24 C 45 38 23 36 5 22 Z'
          if symbol=='view' else
          'M 5 24 C 27 10 50 12 65 22 C 47 36 25 38 5 24 Z')
    s=f'<path d="{path}" fill="{fill}" fill-opacity="{op}" stroke="{edge}" stroke-opacity="{p["edge"]}" stroke-width="2.5" stroke-linejoin="round"/>'
    # Use the controls themselves as the eye detail, not separate pupils.
    if symbol=='view':
        s+=f'<rect x="24" y="17" width="13" height="12" rx="1" fill="none" stroke="{ink}" stroke-width="2"/><rect x="31" y="22" width="13" height="12" rx="1" fill="none" stroke="{ink}" stroke-width="2"/>'
    else:
        for y in (18,24,30):
            s+=f'<path d="M 25 {y} H 45" fill="none" stroke="{ink}" stroke-width="2.5" stroke-linecap="round"/>'
    return svg(s,w,h)

def home(p,pressed):
    # The only visible nose is the functional HOME (SDL GUIDE code 5) sprite.
    d=72; op=p['active'] if pressed else p['neutral']
    s=f'<circle cx="36" cy="36" r="31" fill="{IVORY if pressed else DEEP}" fill-opacity="{op}" stroke="{IVORY if pressed else GOLD}" stroke-opacity="{p["edge"]}" stroke-width="3"/>'
    s+=f'<path d="M 20 27 Q 36 21 52 27 Q 54 30 48 37 L 39 44 Q 36 47 33 44 L 24 37 Q 18 31 20 27 Z" fill="{BLACK_PAW if pressed else LIGHT}" fill-opacity="{1 if pressed else p["glass"]}"/>'
    s+=f'<path d="M 36 45 V 50 M 36 50 Q 30 56 25 53 M 36 50 Q 42 56 47 53" stroke="{BLACK_PAW if pressed else GOLD}" stroke-opacity="{p["decoration"]}" stroke-width="2" stroke-linecap="round" fill="none"/>'
    return svg(s,d,d)


# Positions refer to the same 1280x720 overlay canvas, not the 2048px atlas.
# At least 3 px sprite packing gap after each normal/pressed pair.
POS={
'a':(915,416),'b':(974,362),'x':(856,362),'y':(915,308),
'dpad_up':(440,390),'dpad_down':(440,508),'dpad_left':(382,449),'dpad_right':(498,449),
'lb':(276,130),'rb':(848,130),
'view':(526,246),'menu':(686,246),'home_guide':(604,331),
'l_stick':(258,295),'r_stick':(721,401),
'lt':(437,125),'rt':(651,125)
}
SIZE={**{n:(70,70) for n in ('a','b','x','y')},
      **{n:(60,60) for n in ('dpad_up','dpad_down','dpad_left','dpad_right')},
      'lb':(156,136),'rb':(156,136),'view':(70,48),'menu':(70,48),
      'home_guide':(72,72),'l_stick':(128,128),'r_stick':(128,128),
      'lt':(192,46),'rt':(192,46)}

def sprite(n,p,pressed):
    if n in ('a','b','x','y'):return circle_button(p,pressed,n.upper(),d=70)
    if n.startswith('dpad_'):return dpad(p,pressed,n.split('_')[1])
    if n in ('lb','rb'):return ear(p,pressed,n)
    if n in ('l_stick','r_stick'):return paw(p,pressed)
    if n in ('view','menu'):return small(p,pressed,n)
    if n=='home_guide':return home(p,pressed)
    if n in ('lt','rt'):return trigger_fill(p) if pressed else Image.new('RGBA',SIZE[n])
    raise ValueError(n)

def create_layout():
    base=json.loads(ORIG.read_text(encoding='utf-8'))
    result=json.loads(json.dumps(base))
    # Packed static dimensions; pairs are normal + pressed, separated by 3 pixels.
    coords={}
    row_top=740
    xx=8
    order=['lb','rb','a','b','x','y','dpad_up','dpad_down','dpad_left','dpad_right','view','menu','home_guide']
    for n in order:
        w,h=SIZE[n];coords[n]=(xx,row_top,w,h);xx+=w+12
    xx=8;row_top=1090
    for n in ('l_stick','r_stick','lt','rt'):
        w,h=SIZE[n];coords[n]=(xx,row_top,w,h);xx+=w+12
    for e in result['elements']:
        n=e['id']
        if n=='body':e['mapping']=[0,0,*OVERLAY];e['pos']=[0,0];continue
        e['mapping']=list(coords[n]);e['pos']=list(POS[n])
        if n in ('lb','rb'):e['z_level']=2
    return result

def build(layout,p):
    atlas=Image.new('RGBA',ATLAS,(0,0,0,0))
    atlas.alpha_composite(body(p),(0,0))
    for e in layout['elements'][1:]:
        n=e['id'];x,y,w,h=e['mapping']
        normal=sprite(n,p,False);active=sprite(n,p,True)
        assert normal.size==active.size==(w,h)
        assert y+2*h+PAD<=ATLAS[1],(n,y,h)
        atlas.alpha_composite(normal,(x,y));atlas.alpha_composite(active,(x,y+h+PAD))
    return atlas

def simulate(atlas,layout,buttons=(),axes=None,triggers=None):
    """Preview only. Input Overlay plugin performs the actual input rendering."""
    axes=axes or {};triggers=triggers or {}
    canvas=Image.new('RGBA',OVERLAY,(0,0,0,0))
    for e in sorted(layout['elements'],key=lambda x:x['z_level']):
        n=e['id'];x,y,w,h=e['mapping'];px,py=e['pos']
        if e['type']==5:
            dx,dy=axes.get(n,(0,0));r=e['stick_radius'];px+=round(r*dx);py+=round(r*dy)
        if e['type']==6:
            part=max(0,min(w,round(w*triggers.get(n,0.0))))
            if part:canvas.alpha_composite(atlas.crop((x,y+h+PAD,x+part,y+2*h+PAD)),(px,py))
            continue
        sy=y+h+PAD if n in buttons else y
        canvas.alpha_composite(atlas.crop((x,sy,x+w,sy+h)),(px,py))
    return canvas

def scene(light=True):
    base=Image.new('RGBA',OVERLAY,((41,53,67,255) if light else (14,24,38,255)))
    dr=ImageDraw.Draw(base)
    for i in range(8):
        x=20+i*162
        clr=(61+i*2,76+i*2,86+i*2,255) if light else (24+i*2,34+i*2,46+i*2,255)
        dr.rounded_rectangle((x,137+(i%2)*70,x+99,595+(i%3)*15),radius=16,fill=clr)
    return base

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True,
                        help='New or empty directory outside controller/')
    args=parser.parse_args()
    output=args.output_dir.expanduser().resolve()
    if output==HERE or HERE in output.parents or output==HERE.parent:
        parser.error('Refusing to write to controller/ or the project root')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error('Output directory must be new or empty')
    try:
        import cairosvg  # noqa: F401 - verify before creating the output directory
    except ImportError:
        parser.error('CairoSVG is required to generate Sara images')
    output.mkdir(parents=True,exist_ok=True)
    layout=create_layout()
    with (output/'controller_layout_sara.json').open('w', encoding='utf-8', newline='\n') as handle:
        handle.write(json.dumps(layout,ensure_ascii=False,indent=2)+'\n')
    for name,p in PROFILES.items():
        atlas=build(layout,p)
        atlas.save(output/f'controller_atlas_{name}.png',optimize=True)
        for state in ('idle','input'):
            pressed={'lb','rb','a','dpad_up','r_stick','home_guide'} if state=='input' else set()
            axes={'l_stick':(.60,-.33),'r_stick':(-.34,.66)} if state=='input' else {}
            trigs={'lt':.48,'rt':.81} if state=='input' else {}
            image=simulate(atlas,layout,pressed,axes,trigs)
            image.save(output/f'{name}_{state}.png',optimize=True)
            back=Image.alpha_composite(scene(light=(name=='sara_rta')),image)
            back.convert('RGB').save(output/f'{name}_{state}_scene.jpg',quality=92,subsampling=0)
    print('Created Sara atlases, layout and previews in',output)

if __name__=='__main__':main()
