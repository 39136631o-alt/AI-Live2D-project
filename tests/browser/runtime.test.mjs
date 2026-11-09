import test from 'node:test';
import assert from 'node:assert/strict';
import {parameter,automaticPose} from '../../web/character.mjs';

test('game input is clamped and invalid inputs rejected',()=>{
  assert.equal(parameter('headAngle',90),5);
  assert.equal(parameter('eyeOpen',-1),0);
  assert.throws(()=>parameter('mouthOpen',NaN),TypeError);
  assert.throws(()=>parameter('mouthOpen','1'),TypeError);
  assert.throws(()=>parameter('invalid',0),RangeError);
});
test('blink closes at its midpoint and reopens',()=>{
  const opts={blink:true};const manual={mouthOpen:0,headAngle:0,hairSway:0,breath:0};
  assert.equal(automaticPose(0,opts,manual).eyeOpen,1);
  assert.ok(automaticPose(1.34,opts,manual).eyeOpen<.001);
  assert.equal(automaticPose(1.6,opts,manual).eyeOpen,1);
});
test('all automatic channels vary and manual channels stay fixed',()=>{
  const on={blink:true,talk:true,breathe:true,sway:true,hair:true};
  const manual={eyeOpen:.7,mouthOpen:.3,breath:.2,headAngle:1,hairSway:-2};
  const a=automaticPose(.1,on,manual),b=automaticPose(.8,on,manual);
  for(const key of ['mouthOpen','breath','headAngle','hairSway']) assert.notEqual(a[key],b[key]);
  assert.deepEqual(automaticPose(2,{},manual),manual);
});
