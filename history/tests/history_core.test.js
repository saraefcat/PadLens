const assert = require('node:assert/strict');
const {test} = require('node:test');
const {Reducer,reorder,normalizedEvent} = require('../history_core.js');
const M=1_000_000;
const ev=(event_type,virtual_code,virtual_value,time,device_index=7)=>({event_type,virtual_code,virtual_value,time,device_index});
test('down/up pairs yield one history item and repeated down is suppressed',()=>{
  const r=new Reducer();
  assert.equal(r.ingest(ev('controller_button_down',0,1,100*M)),true);
  assert.equal(r.ingest(ev('controller_button_down',0,1,101*M)),false);
  assert.equal(r.ingest(ev('controller_button_up',0,0,120*M)),false);
  assert.equal(r.ingest(ev('controller_button_down',0,1,300*M)),true);
  assert.deepEqual(r.items.map(x=>x.labels),[['A'],['A']]);
});
test('simultaneous shoulder + A is a chord, separated keypresses remain separate',()=>{
  const r=new Reducer({chordWindowMs:28});
  r.ingest(ev('controller_button_down',9,1,100*M));
  r.ingest(ev('controller_button_down',0,1,120*M));
  assert.deepEqual(r.items[0].labels,['LB','A']);
  r.ingest(ev('controller_button_down',1,1,300*M));
  assert.deepEqual(r.items[0].labels,['B']);
});
test('trigger hysteresis records one peak despite many axis changes',()=>{
  const r=new Reducer();
  r.ingest(ev('controller_axis_motion',4,.16,100*M));
  r.ingest(ev('controller_axis_motion',4,.25,101*M));
  r.ingest(ev('controller_axis_motion',4,.67,102*M));
  r.ingest(ev('controller_axis_motion',4,.65,103*M));
  r.ingest(ev('controller_axis_motion',4,.09,104*M));
  assert.equal(r.items.length,1);
  assert.equal(r.items[0].peak,67);
  r.ingest(ev('controller_axis_motion',4,.25,105*M));
  assert.equal(r.items.length,2);
});
test('multiple devices are not mixed; disconnect allows reacquisition',()=>{
  const r=new Reducer();
  r.ingest(ev('controller_button_down',0,1,100*M,7));
  r.ingest(ev('controller_button_down',1,1,101*M,8));
  assert.equal(r.items.length,1);
  r.ingest(ev('controller_device_removed',0,0,102*M,7));
  r.ingest(ev('controller_button_down',1,1,103*M,8));
  assert.equal(r.items.length,2);
});
test('buffer reorders LIFO transport by event timestamps',()=>{
  const messages=[{data:ev('controller_button_up',0,0,130*M),seq:0},{data:ev('controller_button_down',0,1,100*M),seq:1}];
  const r=new Reducer();
  for(const item of reorder(messages))r.ingest(item.data);
  assert.equal(r.items.length,1);
  assert.equal(r.pressed.size,0);
});
test('unknown and keyboard input ignored; expiration removes stale events',()=>{
  const r=new Reducer();
  assert.equal(normalizedEvent({event_type:'key_pressed'}),null);
  assert.equal(r.ingest(ev('controller_button_down',30,1,100*M)),false);
  r.ingest(ev('controller_button_down',0,1,101*M),1000);
  assert.equal(r.expire(10000,9000),true);
  assert.equal(r.items.length,0);
});

const {viewItems,visibleInterval} = require('../history_core.js');
test('start-to-start intervals in milliseconds are attached to newer event',()=>{
  const r = new Reducer({chordWindowMs:28});
  r.ingest(ev('controller_button_down',0,1,100*M),1);
  r.ingest(ev('controller_button_up',0,0,145*M),1);
  r.ingest(ev('controller_button_down',1,1,174*M),1);
  r.ingest(ev('controller_button_up',1,0,180*M),1);
  r.ingest(ev('controller_button_down',9,1,350*M),1);
  assert.equal(r.items[0].intervalMs,176);
  assert.equal(r.items[1].intervalMs,74);
  assert.equal(r.items[2].intervalMs,null);
  assert.equal(visibleInterval(r.items[0],r.items[1]),176);
  assert.deepEqual(viewItems(r.items,'oldest').map(x=>x.labels[0]),['A','B','LB']);
  assert.deepEqual(viewItems(r.items,'newest').map(x=>x.labels[0]),['LB','B','A']);
  assert.deepEqual(r.items.map(x=>x.labels[0]),['LB','B','A']); // presentation must not mutate history
});

test('chord preserves original row time and stores joined button without splitting intervals',()=>{
  const r=new Reducer({chordWindowMs:28});
  r.ingest(ev('controller_button_down',9,1,100*M),1);
  r.ingest(ev('controller_button_down',0,1,118*M),1);
  assert.equal(r.items.length,1);
  assert.deepEqual(r.items[0].labels,['LB','A']);
  assert.equal(r.items[0].startTimeNs,100*M);
  r.ingest(ev('controller_button_down',1,1,200*M),1);
  assert.equal(r.items[0].intervalMs,100);
});

test('trigger threshold event uses sample timestamp and ignores subsequent peak updates for delta',()=>{
  const r=new Reducer();
  r.ingest(ev('controller_button_down',0,1,100*M),1);
  r.ingest(ev('controller_axis_motion',4,.22,150*M),1);
  r.ingest(ev('controller_axis_motion',4,.81,164*M),1);
  r.ingest(ev('controller_button_down',10,1,177*M),1);
  assert.equal(r.items[0].intervalMs,27);
  assert.equal(r.items[1].intervalMs,50);
  assert.equal(r.items[1].peak,81);
});

test('missing or regressed timestamp does not fabricate milliseconds',()=>{
  const r=new Reducer();
  r.ingest(ev('controller_button_down',0,1,100*M),1);
  r.ingest(ev('controller_button_down',1,1,90*M),1);
  assert.equal(r.items[0].intervalMs,null);
  r.ingest(ev('controller_button_up',1,0,120*M),1);
  r.ingest(ev('controller_button_down',2,1,null),1);
  assert.equal(r.items[0].intervalMs,null);
  r.ingest(ev('controller_button_down',3,1,250*M),1);
  assert.equal(r.items[0].intervalMs,null);
});

test('reconnect and device removal reset continuity',()=>{
  const r=new Reducer();
  r.ingest(ev('controller_button_down',0,1,100*M),1);
  r.resetContinuity();
  r.ingest(ev('controller_button_down',1,1,140*M),1);
  assert.equal(r.items[0].intervalMs,null);
  r.ingest(ev('controller_device_removed',0,0,180*M),1);
  r.ingest(ev('controller_button_down',2,1,190*M),1);
  assert.equal(r.items[0].intervalMs,null);
});

test('only adjacent IDs can use the stored delta; expiration/removal does not mislabel',()=>{
  const r = new Reducer();
  r.ingest(ev('controller_button_down',0,1,100*M),1000);
  r.ingest(ev('controller_button_down',1,1,200*M),2000);
  r.ingest(ev('controller_button_down',2,1,300*M),3000);
  assert.equal(visibleInterval(r.items[0],r.items[1]),100);
  assert.equal(visibleInterval(r.items[0],r.items[2]),null);
  r.expire(10500,9000);
  assert.equal(r.items.length,2);
  assert.equal(visibleInterval(r.items[0],r.items[1]),100);
  assert.equal(visibleInterval(r.items[1],undefined),null);
});

test('input order accepts only allowed values',()=>{
  assert.throws(()=>viewItems([], 'surprise'), TypeError);
});

test('manual clear removes displayed items and resets time continuity, without resetting held button',()=>{
  const r=new Reducer();
  r.ingest(ev('controller_button_down',0,1,100*M),1000);
  assert.equal(r.items.length,1);
  r.clearItems();
  assert.equal(r.items.length,0);
  assert.equal(r.ingest(ev('controller_button_down',0,1,110*M),1010),false);
  r.ingest(ev('controller_button_up',0,0,115*M),1015);
  r.ingest(ev('controller_button_down',0,1,200*M),1020);
  assert.equal(r.items.length,1);
  assert.equal(r.items[0].intervalMs,null);
});
test('manual clear leaves max-items limit and expiry mechanism operative',()=>{
  const r=new Reducer({maxItems:2});
  r.ingest(ev('controller_button_down',0,1,100*M),1000);
  r.ingest(ev('controller_button_down',1,1,200*M),2000);
  r.ingest(ev('controller_button_down',2,1,300*M),3000);
  assert.equal(r.items.length,2);
  r.clearItems();
  assert.equal(r.items.length,0);
  r.ingest(ev('controller_button_down',3,1,400*M),4000);
  assert.equal(r.expire(14000,9000),true);
});
