const assert = require('node:assert/strict');
const {test} = require('node:test');
const {Reducer} = require('../history_core.js');

test('generic HOME label preserves SDL GUIDE code 5', () => {
  const model = new Reducer();
  model.ingest({event_type:'controller_button_down', virtual_code:5,
                virtual_value:1, device_index:7, time:100000000});
  assert.deepEqual(model.items[0].labels,['Home']);
  assert.equal(model.items[0].presses.length, 1);
});
