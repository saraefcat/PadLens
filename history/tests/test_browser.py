"""Real Chromium rendering tests, injected from the actual v0.6 HTML and JS.

This runner avoids external file/network navigation where browser sandbox policy
prohibits it. URLSearchParams is given a demo query only inside the test copy of JS.
"""
from pathlib import Path
from urllib.parse import urlencode
import json
import re
from playwright.sync_api import sync_playwright
from browser_launch import launch_chromium

ROOT=Path(__file__).resolve().parents[1]
HTML=re.sub(r'<script src="[^"]+"></script>', '', (ROOT/'input_history.html').read_text('utf-8'))
CONFIG=(ROOT/'user_config.js').read_text('utf-8')
CORE=(ROOT/'history_core.js').read_text('utf-8')
OVERLAY=(ROOT/'overlay.js').read_text('utf-8')
ARTIFACT_DIR=ROOT.parent/'.local'/'browser-tests'
ARTIFACT_DIR.mkdir(parents=True,exist_ok=True)


def load(page,**params):
    page.set_content(HTML)
    page.evaluate("""() => {
      const memory = {};
      Object.defineProperty(window, 'localStorage', {configurable: true, value:{
        getItem: k => memory[k] ?? null, setItem: (k,v) => {memory[k] = v;}
      }});
    }""")
    page.add_script_tag(content=CONFIG)
    page.add_script_tag(content=CORE)
    query='?'+urlencode({'demo':1,**params})
    code=OVERLAY.replace('new URLSearchParams(location.search)', f'new URLSearchParams({json.dumps(query)})')
    assert code != OVERLAY
    page.add_script_tag(content=code)
    page.wait_for_timeout(150)


def screenshot_case(browser,name,width=300,height=510,header='off',timing='on',order='newest',preset=260):
    page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    load(page,header=header,timing=timing,order=order,width=preset)
    assert (page.locator('#history-header').evaluate('(e)=>getComputedStyle(e).display') == 'none') == (header=='off')
    assert page.locator('#items .event').count()>=2
    assert page.locator('#settings-btn').count()==1
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'horizontal crop'
    assert page.evaluate("document.querySelector('#items').getBoundingClientRect().bottom <= innerHeight"), 'vertical crop'
    assert not errors, errors
    page.screenshot(path=str(ARTIFACT_DIR/name),omit_background=True)
    page.close()

with sync_playwright() as p:
    browser=launch_chromium(p)
    screenshot_case(browser,'preview_header_off_260.png')
    screenshot_case(browser,'preview_header_on_260.png',header='on')
    screenshot_case(browser,'preview_header_off_200x400.png',width=200,height=400)
    screenshot_case(browser,'preview_header_off_240.png',width=240,height=510,preset=240)
    screenshot_case(browser,'preview_header_off_300.png',width=300,height=510,preset=300)
    page=browser.new_page(viewport={'width':200,'height':400})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    load(page,header='on',width=260,timing='on')
    gear=page.locator('#settings-btn')
    page.locator('main').hover(position={'x':180,'y':15})
    gear.click()
    assert page.locator('#settings-panel').is_visible()
    assert page.locator('#header-checkbox').is_checked()
    page.locator('#header-checkbox').uncheck()
    assert page.locator('#history-header').evaluate('(e)=>getComputedStyle(e).display') == 'none'
    assert gear.get_attribute('aria-expanded') == 'true'
    assert page.locator('#settings-connection').inner_text().startswith('接続状態：')
    page.screenshot(path=str(ARTIFACT_DIR/'preview_settings_header_off.png'),omit_background=True)
    page.locator('.order-choice[data-order="oldest"]').click()
    assert page.locator('.order-choice[data-order="oldest"]').get_attribute('aria-pressed')=='true'
    page.keyboard.press('Escape')
    assert gear.get_attribute('aria-expanded') == 'false'
    page.locator('main').hover(position={'x':180,'y':10})
    gear.click()
    page.locator('#header-checkbox').check()
    assert page.locator('#history-header').is_visible()
    page.locator('#interval-checkbox').uncheck()
    page.locator('#expire-checkbox').uncheck()
    page.locator('.width-choice[data-width="240"]').click()
    assert page.locator('main').evaluate('(e)=>Math.round(e.getBoundingClientRect().width)') == 200
    saved=page.evaluate("JSON.parse(localStorage.getItem('controller_input_history_settings'))")
    assert saved['showHeader'] is True
    assert saved['order']=='oldest' and saved['width']==240
    assert saved['showInterval'] is False and saved['autoExpire'] is False
    assert not errors, errors
    page.close()
    browser.close()
print('PASS: Chromium render + header ON/OFF + reopen settings + persistence + narrow view')
