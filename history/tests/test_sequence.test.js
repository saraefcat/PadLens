'use strict';
const assert = require('node:assert/strict');
const {test} = require('node:test');
const {Reducer,formatSequence,visibleInterval,recentItems} = require('../history_core.js');
const input=(n)=>({event_type:'controller_button_down',virtual_code:n%2,time:n*80_000_000,device_index:7});
const up=(n)=>({event_type:'controller_button_up',virtual_code:n%2,time:n*80_000_000+30_000_000,device_index:7});

test('sequence display: 1, 9, 99, 100, 998, 999, 1000, 1001, 1998, 1999',()=>{
  const cases = [[1,'01'],[9,'09'],[99,'99'],[100,'100'],[998,'998'],[999,'999'],
    [1000,'01'],[1001,'02'],[1998,'999'],[1999,'01'],[9990,'999']];
  for (const [id,expectation] of cases) assert.equal(formatSequence(id),expectation);
});
test('invalid sequence IDs rejected',()=>{
  for (const id of [0,-1,1.5,NaN,Infinity,Number.MAX_SAFE_INTEGER+1]) {
    assert.throws(()=>formatSequence(id),RangeError);
  }
});
test('1000th event retains raw ID for adjacency, intervals and sorting',()=>{
  const r=new Reducer({maxItems:8});
  for(let n=1;n<=1001;n++) {
    r.ingest(input(n),n);
    r.ingest(up(n),n);
  }
  assert.deepEqual(r.items.slice(0,4).map(x=>x.id),[1001,1000,999,998]);
  assert.deepEqual(r.items.slice(0,4).map(x=>formatSequence(x.id)),['02','01','999','998']);
  assert.deepEqual(recentItems(r.items,3,'oldest').map(x=>formatSequence(x.id)),['999','01','02']);
  assert.equal(visibleInterval(r.items[1],r.items[2]),80);
  assert.equal(visibleInterval(r.items[0],r.items[1]),80);
});
test('clearing visible history does not reset wrapped sequence',()=>{
  const r=new Reducer();r.nextId=1000;
  r.ingest(input(1000),1000);
  r.clearItems();
  r.ingest(input(1001),1001);
  assert.equal(r.items[0].id,1001);
  assert.equal(formatSequence(r.items[0].id),'02');
  assert.equal(r.items[0].intervalMs,null);
});
