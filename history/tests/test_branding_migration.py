"""Check first-run migration from legacy localStorage key without changing display behavior."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_launch import launch_chromium
root = Path(__file__).resolve().parents[1]
html = (root / 'input_history.html').read_text('utf-8')
config = (root / 'user_config.js').read_text('utf-8')
core = (root / 'history_core.js').read_text('utf-8')
overlay = (root / 'overlay.js').read_text('utf-8')
# Only the compatibility key retains the prior internal product-specific token.
old_key='wolverine_input_history_v02_settings'
new_key='controller_input_history_settings'
assert old_key in overlay
assert 'window.ControllerHistoryDefaults' in config
assert 'window.ControllerInputHistoryDiagnostics' in overlay
with sync_playwright() as p:
    browser=launch_chromium(p)
    page=browser.new_page(viewport={'width':200,'height':400})
    errors=[]
    page.on('pageerror', lambda x: errors.append(str(x)))
    page.set_content(html)
    page.evaluate("""(key)=>{
       const db=new Map([[key,JSON.stringify({order:'oldest',width:300,showInterval:true,autoExpire:false,showHeader:false})]]);
       Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>db.has(k)?db.get(k):null,setItem:(k,v)=>db.set(k,v)}});
    }""",old_key)
    for source in (config,core,overlay):
        page.add_script_tag(content=source)
    page.wait_for_timeout(150)
    assert page.evaluate('window.ControllerInputHistoryDiagnostics !== undefined')
    assert page.locator('#history-header').evaluate('(e)=>getComputedStyle(e).display')=='none'
    assert page.locator('.order-choice[data-order="oldest"]').get_attribute('aria-pressed')=='true'
    assert page.locator('#interval-checkbox').is_checked()
    assert not page.locator('#expire-checkbox').is_checked()
    migrated = page.evaluate('(k)=>JSON.parse(localStorage.getItem(k))',new_key)
    assert migrated['order']=='oldest' and migrated['showInterval']==True and migrated['showHeader']==False
    assert not errors,errors
    browser.close()
print('PASS legacy setting migration, new namespaces, and 200x400 display')
