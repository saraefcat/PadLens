'use strict';
const assert=require('node:assert/strict');
const {test}=require('node:test');
const {Reducer,normalizedEvent,parseMessageFrame,RateLimiter,EventBuffer,visibleInterval}=require('../history_core.js');
const M=1_000_000;
const e=(type,code,t=100,value=1,device=1)=>({event_type:type,virtual_code:code,time:t*M,virtual_value:value,device_index:device});

test('frames are validated and bounded before processing',()=>{
  assert.equal(parseMessageFrame('x'.repeat(4097)),null);
  assert.equal(parseMessageFrame(new Uint8Array([1,2,3])),null);
  assert.equal(parseMessageFrame('{bad'),null);
  assert.equal(parseMessageFrame('[]'),null);
  assert.equal(parseMessageFrame(JSON.stringify({event_type:'key_pressed',device_index:0})),null);
  assert.equal(parseMessageFrame(JSON.stringify(e('controller_button_down',0))).virtual_code,0);
  assert.equal(parseMessageFrame(JSON.stringify(e('controller_button_down',14))).virtual_code,14);
  assert.equal(parseMessageFrame(JSON.stringify(e('controller_button_down',15))),null);
  assert.equal(parseMessageFrame(JSON.stringify(e('controller_axis_motion',0))),null);
  assert.equal(parseMessageFrame(JSON.stringify(e('controller_axis_motion',4,100,'INJECT'))),null);
  assert.equal(parseMessageFrame(JSON.stringify(e('controller_axis_motion',4,100,999))),null);
  assert.equal(parseMessageFrame(JSON.stringify({...e('controller_button_down',0),device_index:'1'})),null);
  assert.equal(parseMessageFrame(JSON.stringify({...e('controller_button_down',0),virtual_code:'0'})),null);
  assert.equal(parseMessageFrame(JSON.stringify({...e('controller_button_down',0),time:0})).time,0);
});

test('idle axis noise and button-up do not steal automatic gamepad selection',()=>{
  const r=new Reducer();
  assert.equal(r.ingest(e('controller_axis_motion',0,10,.9,7)),false);
  assert.equal(r.ingest(e('controller_axis_motion',4,11,.05,7)),false);
  assert.equal(r.ingest(e('controller_button_up',0,12,0,7)),false);
  assert.equal(r.selectedDevice,null);
  assert.equal(r.ingest(e('controller_button_down',0,30,1,8)),true);
  assert.equal(r.selectedDevice,8);
  assert.equal(r.ingest(e('controller_button_down',1,50,1,7)),false);
  assert.deepEqual(r.items.map(x=>x.labels),[['A']]);
});

test('pressed details remain in memory despite combined display row',()=>{
  const r=new Reducer({chordWindowMs:28});
  r.ingest(e('controller_button_down',9,100));
  r.ingest(e('controller_button_down',0,118));
  assert.deepEqual(r.items[0].labels,['LB','A']);
  assert.deepEqual(r.items[0].presses,[{label:'LB',timeNs:100*M},{label:'A',timeNs:118*M}]);
  r.ingest(e('controller_button_down',1,200));
  assert.equal(visibleInterval(r.items[0],r.items[1]),100);
  r.clearItems();
  assert.equal(r.items.length,0);
});

test('holdback sorts burst events even when arrival batches straddle 45ms',()=>{
  const b=new EventBuffer(90,4);
  b.push(e('controller_button_up',0,130),0);
  b.push(e('controller_button_down',0,100),60);
  assert.deepEqual(b.drainDue(89),[]);
  assert.deepEqual(b.drainDue(90).map(x=>x.data.event_type),['controller_button_down','controller_button_up']);
  assert.equal(b.length,0);
  assert.equal(b.remainingDelay(90),null);
  for(let i=0;i<4;i++)assert.equal(b.push(e('controller_button_down',0,150+i),100),true);
  assert.equal(b.push(e('controller_button_down',0,155),100),false);
  b.clear();assert.equal(b.length,0);
});

test('rate limiter permits normal events and bounds flood per period',()=>{
  const r=new RateLimiter(3,1000);
  assert.equal(r.accept(100),true);assert.equal(r.accept(110),true);assert.equal(r.accept(120),true);
  assert.equal(r.accept(130),false);assert.equal(r.accept(1099),false);
  assert.equal(r.accept(1100),true);
});

test('limits cap retained history and anomalous delta values',()=>{
  const r=new Reducer({maxItems:100000});
  assert.equal(r.maxItems,32);
  r.ingest(e('controller_button_down',0,100));
  r.ingest(e('controller_button_down',1,101));
  const absurd=e('controller_button_down',2,90000000);
  r.ingest(absurd);
  assert.equal(r.items[0].intervalMs,null);
});

test('reordering puts missing and untrusted timestamps after timestamped events',()=>{
  const {reorder}=require('../history_core.js');
  const data=[
    {data:{time:'30'},seq:0},
    {data:{time:20},seq:1},
    {data:{time:null},seq:2},
    {data:{time:10},seq:3},
  ];
  assert.deepEqual(reorder(data).map(e=>e.seq),[3,1,0,2]);
});
