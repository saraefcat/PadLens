"""Chromium integration: render 999 -> 01 rollover using actual JS, check no clipping."""
from pathlib import Path
from urllib.parse import urlencode
import re
import json
from playwright.sync_api import sync_playwright
from browser_launch import launch_chromium

ROOT=Path(__file__).resolve().parents[1]
HTML=re.sub(r'<script src="[^"]+"></script>', '', (ROOT/'input_history.html').read_text('utf-8'))
CONFIG=(ROOT/'user_config.js').read_text('utf-8')
CORE=(ROOT/'history_core.js').read_text('utf-8')
OVERLAY=(ROOT/'overlay.js').read_text('utf-8')
ARTIFACT_DIR=ROOT.parent/'.local'/'browser-tests'
ARTIFACT_DIR.mkdir(parents=True,exist_ok=True)
# Set a test-only sequence starting near rollover and replay the last eight input
# events through the real browser intake. Bulk synthetic flooding is correctly
# rejected by v0.8's DoS protections; it is not an appropriate UI test.
ORIGINAL='samples.forEach(data => receive(data));'
assert ORIGINAL in OVERLAY
OVERLAY=OVERLAY.replace(ORIGINAL,"""
    history.nextId = 995;
    for (let n=995;n<=1002;n++) {
      receive(e('controller_button_down',0,n*80));
      receive(e('controller_button_up',0,n*80+30));
    }
""")

with sync_playwright() as p:
    browser=launch_chromium(p)
    cases=0
    for width in [200,240,260,300]:
        for order in ['newest','oldest']:
            page=browser.new_page(viewport={'width':width,'height':400},device_scale_factor=1)
            errors=[]
            page.on('pageerror',lambda exc: errors.append(str(exc)))
            page.set_content(HTML)
            page.evaluate("""() => {
              const memory = {};
              Object.defineProperty(window, 'localStorage', {configurable:true, value:{
                getItem:k=>memory[k] ?? null, setItem:(k,v)=>{memory[k]=v;}
              }});
            }""")
            page.add_script_tag(content=CONFIG)
            page.add_script_tag(content=CORE)
            qs='?'+urlencode(dict(demo=1,header='off',timing='on',order=order,width=width if width!=200 else 260))
            inject=OVERLAY.replace('new URLSearchParams(location.search)',f'new URLSearchParams({json.dumps(qs)})')
            page.add_script_tag(content=inject)
            page.wait_for_function("document.querySelectorAll('.event').length>2 && document.querySelector('.seq').textContent !== '01'",timeout=10000)
            labels=page.locator('.event .seq').all_inner_texts()
            # in newest-first 1002 is the latest -> 03; then 02,01,999.
            if order=='newest':
                assert labels[:4]==['03','02','01','999'],(width,order,labels)
            else:
                assert labels[-4:]==['999','01','02','03'],(width,order,labels)
            # When rows fit, make sure three-digit label is visible to actual browser layout.
            for row in page.locator('.event').all():
                seq_box=row.locator('.seq').bounding_box()
                key_box=row.locator('.keys').bounding_box()
                assert seq_box and key_box
                assert seq_box['x']+seq_box['width'] <= key_box['x']-.1, (width,order,seq_box,key_box)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width,order,'horizontal')
            assert page.evaluate('document.querySelector("#items").getBoundingClientRect().bottom <= innerHeight'),(width,order,'vertical')
            assert not errors,(width,order,errors)
            if width in [200,300] and order=='newest':
                page.screenshot(path=str(ARTIFACT_DIR/f'preview_wrap_{width}px.png'),omit_background=True)
            cases+=1
            page.close()
    browser.close()
print(f'PASS: {cases} real Chromium sequence roll-over & layout cases')
