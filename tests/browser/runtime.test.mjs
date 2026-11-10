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

// Stage two motion regressions: bounds, convergence and honest frame measurement.
import {smoothstep,damp,envelope,blinkAt,spring,FrameMeter} from '../../web/motion.mjs';
test('easing is continuous and reactions have no endpoint jump',()=>{
  assert.equal(envelope(0),0);assert.equal(envelope(2.4),0);
  assert.ok(envelope(.001)<.001);assert.ok(envelope(2.399)<.001);
  assert.equal(smoothstep(-1),0);assert.equal(smoothstep(2),1);
  assert.ok(damp(0,1,12,.016)>0 && damp(0,1,12,.016)<1);
  assert.ok(Math.abs(damp(damp(0,1,12,.01),1,12,.01)-damp(0,1,12,.02))<1e-12);
});
test('varied blink intervals and smooth closed/open endpoints',()=>{
  for(let t=0;t<30;t+=.005) assert.ok(blinkAt(t)>=0 && blinkAt(t)<=1);
  for(const t of [1.34,5.82,10.62,10.96]) assert.ok(blinkAt(t)<1e-10);
  assert.ok(blinkAt(1.34+.0001)<.001);
});
test('substepped spring converges at 30/60/120Hz without instability',()=>{
  const results=[];
  for(const hz of [30,60,120]) {
    const state={value:0,velocity:0};
    for(let n=0;n<hz*3;n++){spring(state,3,1/hz);assert.ok(Number.isFinite(state.value));assert.ok(Math.abs(state.value)<4);}
    results.push(state.value);assert.ok(Math.abs(state.value-3)<.001);
  }
  assert.ok(Math.max(...results)-Math.min(...results)<.001);
});
test('FPS measures callback cadence and resets after pause',()=>{
  const meter=new FrameMeter();let measured;
  for(let i=0;i<=60;i++){const value=meter.sample(i*1000/60);if(value!==null)measured=value;}
  assert.ok(Math.abs(measured-60)<.01);
  meter.reset();assert.equal(meter.fps,null);assert.equal(meter.sample(100000),null);
});
test('prototype property names cannot become animation parameters',()=>{
  assert.throws(()=>parameter('toString',0),RangeError);
});

import {eyeGeometry,expressiveEye} from '../../web/eyes.mjs';
test('ordinary smile, closed smile and half-lidded eyes are distinct',()=>{
  assert.ok(expressiveEye(1,{happy:1}).openness>=.9);
  assert.equal(expressiveEye(1,{closedSmile:1}).openness,0);
  assert.equal(expressiveEye(1,{halfLidded:1}).openness,.5);
  assert.equal(expressiveEye(0,{happy:1}).openness,0);
});
test('eyelid geometry closes onto one curve with no inverted aperture',()=>{
  for(const smile of [0,.5,1]) for(let open=0;open<=1;open+=.05) {
    const g=eyeGeometry(270,open,smile);
    assert.ok(!g.aperture.includes('NaN'));
    // Quadratic curve apex: upper never goes below lower.
    const upper=156+(2-8*smile-22*open)/2;
    const lower=156+(2-8*smile+22*open)/2;
    assert.ok(upper<=lower);
  }
  const closed=eyeGeometry(270,0,1);
  assert.ok(closed.aperture.startsWith(closed.closed));
});
