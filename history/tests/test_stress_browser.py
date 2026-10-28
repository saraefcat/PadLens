"""No-network browser stress check: bounded queue/rate + late packet recovery."""
from pathlib import Path
import re
from playwright.sync_api import sync_playwright
from browser_launch import launch_chromium
R=Path(__file__).resolve().parents[1]
HTML=re.sub(r'<script src="[^"]+"></script>', '', (R/'input_history.html').read_text('utf-8'))
with sync_playwright() as p:
    browser=launch_chromium(p)
    page=browser.new_page(viewport={'width':200,'height':400})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(HTML)
    page.evaluate('''() => {
       Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:()=>null,setItem:()=>{}}});
       class FakeWS {
         constructor(url){this.handlers={};window.fakeSocket=this;queueMicrotask(()=>this.emit('open',{}));}
         addEventListener(k,fn){(this.handlers[k]??=[]).push(fn);}
         emit(k,x){for(const f of (this.handlers[k]??[]))f(x);}
       }
       window.WebSocket=FakeWS;
    }''')
    for file in ['user_config.js','history_core.js','overlay.js']:
        page.add_script_tag(content=(R/file).read_text('utf-8'))
    # Flood faster than the UI needs to process; discard instead of growing unbounded.
    page.evaluate('''() => {
       const prefix={event_type:'controller_axis_motion',device_index:1,virtual_code:4,virtual_value:.4,time:10000000000};
       const packet=JSON.stringify(prefix);
       for(let n=0;n<2600;n++)fakeSocket.emit('message',{data:packet});
    }''')
    stats=page.evaluate('ControllerInputHistoryDiagnostics()')
    assert stats['queued'] <= 512, stats
    assert stats['rateLimited']>0 or stats['overflow']>0,stats
    # Different timestamp order across the flush window must not corrupt continuity.
    page.wait_for_timeout(1100)
    page.evaluate('''() => {
       const packet=(type,code,t,v=1)=>({data:JSON.stringify({event_type:type,device_index:1,virtual_code:code,virtual_value:v,time:t*1000000})});
       fakeSocket.emit('message',packet('controller_button_down',0,100));
       fakeSocket.emit('message',packet('controller_button_up',0,120,0));
    }''')
    page.wait_for_timeout(140)
    before=page.locator('.event').count()
    assert before>=1,before
    page.evaluate('''() => {
       fakeSocket.emit('message',{data:JSON.stringify({event_type:'controller_button_down',device_index:1,virtual_code:1,virtual_value:1,time:90000000})});
    }''')
    page.wait_for_timeout(140)
    assert page.evaluate('ControllerInputHistoryDiagnostics().late')>=1
    page.evaluate('''() => {
       fakeSocket.emit('message',{data:JSON.stringify({event_type:'controller_button_down',device_index:1,virtual_code:1,virtual_value:1,time:210000000})});
    }''')
    page.wait_for_timeout(140)
    assert 'B' in page.locator('.event').first.inner_text()
    assert not errors,errors
    browser.close()
print('PASS: Browser flood is bounded and late event resets timing continuity')
