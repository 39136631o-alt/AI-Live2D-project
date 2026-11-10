import {eyeGeometry, expressiveEye} from './eyes.mjs';
import {blinkAt, damp, envelope, spring, FrameMeter} from './motion.mjs';
/** Dependency-free layered SVG runtime. All public parameter values are clamped.
 * SVG transforms use explicit canvas pivots instead of CSS transform-box, for Safari.
 */
export const LIMITS = Object.freeze({eyeOpen:[0,1],mouthOpen:[0,1],breath:[0,1],headAngle:[-5,5],hairSway:[-4,4]});
export function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
export function parameter(name, value) {
  if (!Object.hasOwn(LIMITS,name)) throw new RangeError(`Unknown parameter: ${name}`);
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new TypeError('Expected a finite number');
  return clamp(value, ...LIMITS[name]);
}
export function automaticPose(t, options, manual) {
  const blink = blinkAt(t);
  return {
    eyeOpen: options.blink ? clamp(blink,0,1) : manual.eyeOpen,
    mouthOpen: options.talk ? .15+.8*Math.abs(Math.sin(t*7.8))*Math.abs(Math.sin(t*2.1)) : manual.mouthOpen,
    breath: options.breathe ? (Math.sin(t*1.8)+1)/2 : manual.breath,
    headAngle: options.sway ? Math.sin(t*.95)*1.6 + manual.headAngle : manual.headAngle,
    hairSway: options.hair ? Math.sin(t*1.2)*1.3 + manual.hairSway : manual.hairSway,
  };
}
const CHANNELS={eyeOpen:'blink',mouthOpen:'talk',breath:'breathe',headAngle:'sway',hairSway:'hair'};
function rotation(degrees,x,y) {return `rotate(${degrees.toFixed(4)} ${x} ${y})`;}

export class LayeredCharacter extends EventTarget {
  constructor(svg, manifest, {reducedMotion=false}={}) {
    super();
    this.svg=svg; this.manifest=manifest;
    this.manual={eyeOpen:1,mouthOpen:0,breath:0,headAngle:0,hairSway:0};
    this.options={blink:true,talk:false,breathe:!reducedMotion,sway:!reducedMotion,hair:!reducedMotion,idle:!reducedMotion};
    this.layers=manifest.layers.map(layer=>{
      const node=svg.querySelector(`#${layer.id}`);
      if (!node) throw new Error(`Missing layer ${layer.id}`);
      return {...layer,node};
    });
    this.nodes=Object.fromEntries(['eye_open_left','eye_closed_left','eye_open_right','eye_closed_right','brow_left','brow_right','mouth_open','mouth_closed',...['left','right'].flatMap(side=>['eye_aperture','eye_white','eyelid_upper','eyelid_lower','eyelid_closed'].map(name=>`${name}_${side}`))].map(id=>[id,svg.querySelector(`#${id}`)]));
    if(Object.values(this.nodes).some(n=>!n)) throw new Error('Missing facial animation nodes');
    this.waveAngle=0;this.reducedMotion=reducedMotion;this.meter=new FrameMeter();
    this.secondary={hair:{value:0,velocity:0},cloth:{value:0,velocity:0}};
    this.current=null;this.expressionMix={happy:1,closedSmile:0,halfLidded:0,surprised:0};this.reactionType='greeting';
    this.time=0; this.hair=0; this.velocity=0; this.look=0; this.paused=false;
    this.expression='happy'; this.reactionEnd=0; this.frame=null; this.previous=null; this.disposed=false;
    this.onVisibility=()=> {this.previous=null; this.meter.reset(); if(document.hidden) this.stopFrame(); else this.startFrame();};
    document.addEventListener('visibilitychange',this.onVisibility);
    this.render(); this.startFrame();
  }
  setParameter(name,value) {this.manual[name]=parameter(name,value);this.render();}
  setOptions(options) {
    for (const [key,value] of Object.entries(options)) {
      if (!Object.hasOwn(this.options,key) || typeof value!=='boolean') throw new TypeError(`Invalid option ${key}`);
      this.options[key]=value;
    }
    this.render();
  }
  setExpression(value) {
    if(!['neutral','happy','closedSmile','halfLidded','surprised'].includes(value)) throw new RangeError('Invalid expression');
    this.expression=value;
    if(this.paused) for(const key of Object.keys(this.expressionMix)) this.expressionMix[key]=value===key?1:0;
    this.render();
  }
  setLook(value) {if(Number.isFinite(value)) this.look=clamp(value,-1,1);}
  triggerReaction(type='greeting') {
    if(!['greeting','wave','smile','surprise'].includes(type)) throw new RangeError('Invalid reaction');
    this.reactionType=type;
    this.reactionEnd=this.time+2.4;
    this.render();
    this.dispatchEvent(new CustomEvent('interaction',{detail:{type}}));
  }
  setPaused(value) {
    this.paused=Boolean(value); this.previous=null;this.meter.reset();
    this.dispatchEvent(new CustomEvent('performance',{detail:{fps:null,paused:this.paused}}));
    if(this.paused) this.stopFrame(); else this.startFrame();
    this.render();
  }
  reset() {
    this.waveAngle=0;this.current=null;this.expressionMix={happy:1,closedSmile:0,halfLidded:0,surprised:0};
    this.secondary={hair:{value:0,velocity:0},cloth:{value:0,velocity:0}};this.meter.reset();
    this.time=0;this.hair=0;this.velocity=0;this.look=0;this.reactionEnd=0;
    this.expression='happy';this.manual={eyeOpen:1,mouthOpen:0,breath:0,headAngle:0,hairSway:0};this.render();
  }
  stopFrame() {if(this.frame!==null) cancelAnimationFrame(this.frame);this.frame=null;}
  startFrame() {
    if(this.disposed || this.paused || document.hidden || this.frame!==null) return;
    this.frame=requestAnimationFrame(stamp=>{
      this.frame=null;
      const dt=this.previous===null?0:clamp((stamp-this.previous)/1000,0,.05);
      this.previous=stamp; this.time+=dt;
      const pose=this.pose();
      const reaction=envelope(this.time-(this.reactionEnd-2.4));
      const waveTarget=pose.reacting&&['greeting','wave'].includes(this.reactionType)&&!this.reducedMotion?reaction*(-83+Math.sin((this.time-this.reactionEnd+2.4)*10)*10):0;
      this.waveAngle=damp(this.waveAngle,waveTarget,18,dt);
      this.hair=spring(this.secondary.hair,clamp(pose.hairSway-pose.headAngle*.3,-4,4),dt);
      spring(this.secondary.cloth,this.options.idle?Math.sin(this.time*.9)*.6-pose.headAngle*.08:0,dt,15,7);
      if(!this.current) this.current={...pose};
      for(const key of Object.keys(LIMITS)) {
        // Manual sliders stay exact; only autonomous targets interpolate.
        const channel=CHANNELS[key];
        this.current[key]=this.options[channel]?damp(this.current[key],pose[key],key==='eyeOpen'?65:14,dt):pose[key];
      }
      for(const key of Object.keys(this.expressionMix)) this.expressionMix[key]=damp(this.expressionMix[key],pose.expression===key?1:0,12,dt);
      const fps=this.meter.sample(stamp);
      if(fps!==null) this.dispatchEvent(new CustomEvent('performance',{detail:{fps,paused:false}}));
      this.render();this.startFrame();
    });
  }
  pose() {
    const p=automaticPose(this.time,this.options,this.manual);
    const reacting=this.reactionEnd>this.time;
    const expression=reacting?(this.reactionType==='surprise'?'surprised':'happy'):this.expression;
    p.headAngle=clamp(p.headAngle+this.look*1.5,-5,5);
    return {...p,expression,reacting};
  }
  render() {
    const target=this.pose();
    const p={...target};
    if(this.current) for(const key of Object.keys(LIMITS)) {
      const channel=CHANNELS[key];
      if(this.options[channel]) p[key]=this.current[key];
    }
    p.mouthOpen=Math.max(p.mouthOpen,.22*this.expressionMix.closedSmile,.8*this.expressionMix.surprised);
    const idle=this.options.idle&&!this.reducedMotion?Math.sin(this.time*.7)*.22:0;
    const wave=this.waveAngle;
    const lift=p.breath*2.4;
    const body=`${rotation(idle,300,449)} translate(0 ${-lift}) translate(300 449) scale(${1+p.breath*.002} ${1+p.breath*.004}) translate(-300 -449)`;
    const head=rotation(p.headAngle,300,218);
    for(const layer of this.layers) {
      let tr=layer.rig==='static'?'':body;
      if(layer.rig==='head') tr+=` ${head}`;
      if(layer.rig.startsWith('hair')) {
        const sign=layer.rig.endsWith('L')?1:-1;
        const swing=this.options.hair?this.hair:p.hairSway;
        tr+=` ${head} ${rotation(clamp(swing*sign,layer.rig.startsWith('hairFront')?-1.8:-2.6,layer.rig.startsWith('hairFront')?1.8:2.6),...layer.pivot)}`;
      }
      if(layer.rig==='armL') tr+=` ${rotation(p.breath*.25,225,260)}`;
      if(layer.rig==='armR') tr+=` ${rotation(-p.breath*.3+wave,375,260)}`;
      if(layer.id==='costume_train'||layer.id==='costume_skirt') tr+=` ${rotation(this.secondary.cloth.value*(layer.id==='costume_train'?1:.35),300,430)}`;
      this.write(layer.node,'transform',tr.trim());
    }
    for (const side of ['left','right']) {
      const x=side==='left'?270:330;
      const open=this.nodes[`eye_open_${side}`];
      const closed=this.nodes[`eye_closed_${side}`];
      const eye=expressiveEye(p.eyeOpen,this.expressionMix);
      const shape=eyeGeometry(x,eye.openness,eye.smile);
      this.write(this.nodes[`eye_aperture_${side}`],'d',shape.aperture);
      this.write(this.nodes[`eye_white_${side}`],'d',shape.aperture);
      this.write(this.nodes[`eyelid_upper_${side}`],'d',shape.upper);
      this.write(this.nodes[`eyelid_lower_${side}`],'d',shape.lower);
      this.write(this.nodes[`eyelid_closed_${side}`],'d',shape.closed);
      // Fade only the last 2% of aperture; no squashing of pupil/highlights.
      const visibility=clamp(eye.openness/.02,0,1);
      this.write(open,'opacity',String(visibility));
      this.write(closed,'opacity',String(1-visibility));
      this.write(this.nodes[`brow_${side}`],'transform',`${body} ${head} translate(0 ${-4*this.expressionMix.surprised-this.expressionMix.happy})`);
    }
    const mouth=this.nodes.mouth_open;
    this.write(mouth,'opacity',String(p.mouthOpen));
    this.write(mouth,'transform',`translate(300 196) scale(1 ${.1+.9*p.mouthOpen}) translate(-300 -196)`);
    this.write(this.nodes.mouth_closed,'opacity',String(1-p.mouthOpen));
    this.svg.dataset.expression=p.expression;
    this.svg.dataset.eyeOpen=p.eyeOpen.toFixed(3);
    this.svg.dataset.mouthOpen=p.mouthOpen.toFixed(3);
    this.svg.dataset.time=this.time.toFixed(3);
  }
  write(node,name,value) {
    const cache=node.__animationAttributes??=(Object.create(null));
    if(cache[name]!==value){node.setAttribute(name,value);cache[name]=value;}
  }
  dispose() {this.disposed=true;this.stopFrame();document.removeEventListener('visibilitychange',this.onVisibility);}
}
