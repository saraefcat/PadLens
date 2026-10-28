"""Validate real browser integration with a deterministic fake WebSocket.
No network requests or host app interaction. This tests browser-side intake only.
"""
from pathlib import Path
import re
from playwright.sync_api import sync_playwright
from browser_launch import launch_chromium
R=Path(__file__).resolve().parents[1]
HTML=re.sub(r'<script src="[^"]+"></script>', '', (R/'input_history.html').read_text('utf-8'))
CONFIG=(R/'user_config.js').read_text('utf-8')
CORE=(R/'history_core.js').read_text('utf-8')
OVERLAY=(R/'overlay.js').read_text('utf-8')
with sync_playwright() as p:
    browser=launch_chromium(p)
    page=browser.new_page(viewport={'width':200,'height':400})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(HTML)
    page.evaluate('''() => {
       const store = {};
       Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>store[k]??null,setItem:(k,v)=>{store[k]=v;}}});
       class FakeWS {
         constructor(url){this.url=url;this.handlers={};window.fakeSocket=this;queueMicrotask(()=>this.emit('open',{}));}
         addEventListener(key,fn){(this.handlers[key]??=[]).push(fn);}
         emit(key,data){for(const fn of (this.handlers[key]??[])) fn(data);}
       }
       window.WebSocket=FakeWS;
    }''')
    page.add_script_tag(content=CONFIG)
    page.add_script_tag(content=CORE)
    page.add_script_tag(content=OVERLAY)
    page.wait_for_timeout(25)
    assert page.locator('#status').inner_text()=='接続', page.locator('#status').inner_text()
    assert page.locator('#items .event').count()==0
    page.evaluate('''() => {
      // Large content and malformed payload must not pollute the display.
      fakeSocket.emit('message',{data:'X'.repeat(5000)});
      fakeSocket.emit('message',{data:'{broken'});
      fakeSocket.emit('message',{data:JSON.stringify({event_type:'key_pressed',keycode:42})});
      const x = (type,code,ms,value=1)=>JSON.stringify({event_type:type,virtual_code:code,device_index:1,time:10000000000+ms*1000000,virtual_value:value});
      // Reverse delivery order in a single burst: must display one press only.
      fakeSocket.emit('message',{data:x('controller_button_up',0,135,0)});
      fakeSocket.emit('message',{data:x('controller_button_down',0,100,1)});
    }''')
    page.wait_for_timeout(140)
    assert page.locator('#items .event').count()==1, page.locator('#items').inner_text()
    assert 'A' in page.locator('#items .event').first.inner_text()
    assert page.evaluate('ControllerInputHistoryDiagnostics().oversize')==1
    assert page.evaluate('ControllerInputHistoryDiagnostics().malformed')==2
    # Send unrelated device axis noise, then button input from selected device;
    # only the chosen gamepad may produce another historical row.
    page.evaluate('''() => {
      const x = (type,code,ms,value=1,device=1)=>JSON.stringify({event_type:type,virtual_code:code,device_index:device,time:10000000000+ms*1000000,virtual_value:value});
      fakeSocket.emit('message',{data:x('controller_axis_motion',4,200,0.06,99)});
      fakeSocket.emit('message',{data:x('controller_button_down',1,250,1,1)});
    }''')
    page.wait_for_timeout(140)
    assert page.locator('#items .event').count()==2, page.locator('#items').inner_text()
    assert not errors, errors
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert page.evaluate("document.querySelector('#items').getBoundingClientRect().bottom <= innerHeight")
    browser.close()
print('PASS: Chromium fake-WS integration, malformed/oversize rejection, burst sorting, display')
