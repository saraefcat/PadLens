'use strict';
const assert = require('node:assert/strict');
const {test} = require('node:test');
const {normalizeWidth,recentItems,visibleInterval} = require('../history_core.js');

test('width presets are limited to 240/260/300 with 260 default',()=>{
  for(const w of [240,260,300]) {
    assert.equal(normalizeWidth(w),w);
    assert.equal(normalizeWidth(String(w)),w);
  }
  for(const invalid of [120,220,301,460,'auto','100%',Infinity,null]) assert.equal(normalizeWidth(invalid),260);
});
test('clipping-fit candidates always retain most recent rows',()=>{
  const items=Array.from({length:8},(_,i)=>({id:8-i,labels:[String(8-i)]}));
  assert.deepEqual(recentItems(items,4,'newest').map(x=>x.id),[8,7,6,5]);
  assert.deepEqual(recentItems(items,4,'oldest').map(x=>x.id),[5,6,7,8]);
  assert.deepEqual(recentItems(items,0,'oldest'),[]);
  assert.deepEqual(items.map(x=>x.id),[8,7,6,5,4,3,2,1]);
});
test('intervals remain tied to actual consecutive events when older rows are omitted',()=>{
  const items=[{id:12,intervalMs:100},{id:11,intervalMs:24},{id:10,intervalMs:38}];
  const rows=recentItems(items,2,'oldest');
  assert.deepEqual(rows.map(x=>x.id),[11,12]);
  assert.equal(visibleInterval(rows[1],rows[0]),100);
  assert.equal(visibleInterval(rows[0],items[2]),24);
  assert.equal(visibleInterval(rows[0],{id:8}),null);
});
