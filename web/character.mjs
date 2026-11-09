/** Dependency-free layered SVG runtime. All public parameter values are clamped.
 * SVG transforms use explicit canvas pivots instead of CSS transform-box, for Safari.
 */
export const LIMITS = Object.freeze({eyeOpen:[0,1],mouthOpen:[0,1],breath:[0,1],headAngle:[-5,5],hairSway:[-4,4]});
export function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
export function parameter(name, value) {
  if (!(name in LIMITS)) throw new RangeError(`Unknown parameter: ${name}`);
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new TypeError('Expected a finite number');
  return clamp(value, ...LIMITS[name]);
}
export function automaticPose(t, options, manual) {
  const phase = t % 4.7;
  const blink = phase > 1.2 && phase < 1.48 ? Math.abs((phase-1.34)/.14) : 1;
  return {
    eyeOpen: options.blink ? clamp(blink,0,1) : manual.eyeOpen,
    mouthOpen: options.talk ? .15+.8*Math.abs(Math.sin(t*7.8))*Math.abs(Math.sin(t*2.1)) : manual.mouthOpen,
    breath: options.breathe ? (Math.sin(t*1.8)+1)/2 : manual.breath,
    headAngle: options.sway ? Math.sin(t*.95)*1.6 + manual.headAngle : manual.headAngle,
    hairSway: options.hair ? Math.sin(t*1.2)*1.3 + manual.hairSway : manual.hairSway,
  };
}
function rotation(degrees,x,y) {return `rotate(${degrees.toFixed(4)} ${x} ${y})`;}

export class LayeredCharacter extends EventTarget {
  constructor(svg, manifest, {reducedMotion=false}={}) {
    super();
    this.svg=svg; this.manifest=manifest;
    this.manual={eyeOpen:1,mouthOpen:0,breath:0,headAngle:0,hairSway:0};
    this.options={blink:true,talk:false,breathe:!reducedMotion,sway:!reducedMotion,hair:!reducedMotion};
    this.layers=manifest.layers.map(layer=>{
      const node=svg.querySelector(`#${layer.id}`);
      if (!node) throw new Error(`Missing layer ${layer.id}`);
      return {...layer,node};
    });
    this.time=0; this.hair=0; this.velocity=0; this.look=0; this.paused=false;
    this.expression='neutral'; this.reactionEnd=0; this.frame=null; this.previous=null; this.disposed=false;
    this.onVisibility=()=> {this.previous=null; if(document.hidden) this.stopFrame(); else this.startFrame();};
    document.addEventListener('visibilitychange',this.onVisibility);
    this.render(); this.startFrame();
  }
  setParameter(name,value) {this.manual[name]=parameter(name,value);this.render();}
  setOptions(options) {
    for (const [key,value] of Object.entries(options)) {
      if (!(key in this.options) || typeof value!=='boolean') throw new TypeError(`Invalid option ${key}`);
      this.options[key]=value;
    }
    this.render();
  }
  setExpression(value) {
    if(!['neutral','happy','surprised'].includes(value)) throw new RangeError('Invalid expression');
    this.expression=value;this.render();
  }
  setLook(value) {if(Number.isFinite(value)) this.look=clamp(value,-1,1);}
  triggerReaction() {
    this.reactionEnd=this.time+2.4;
    this.render();
    this.dispatchEvent(new CustomEvent('interaction',{detail:{type:'greeting'}}));
  }
  setPaused(value) {
    this.paused=Boolean(value); this.previous=null;
    if(this.paused) this.stopFrame(); else this.startFrame();
    this.render();
  }
  reset() {
    this.time=0;this.hair=0;this.velocity=0;this.look=0;this.reactionEnd=0;
    this.expression='neutral';this.manual={eyeOpen:1,mouthOpen:0,breath:0,headAngle:0,hairSway:0};this.render();
  }
  stopFrame() {if(this.frame!==null) cancelAnimationFrame(this.frame);this.frame=null;}
  startFrame() {
    if(this.disposed || this.paused || document.hidden || this.frame!==null) return;
    this.frame=requestAnimationFrame(stamp=>{
      this.frame=null;
      const dt=this.previous===null?0:clamp((stamp-this.previous)/1000,0,.05);
      this.previous=stamp; this.time+=dt;
      const pose=this.pose();
      // Damped spring follows the head with inertia. This is not Cubism physics.
      const target=clamp(pose.hairSway-pose.headAngle*.35,-4,4);
      this.velocity+=(target-this.hair)*24*dt-this.velocity*8*dt;
      this.hair=clamp(this.hair+this.velocity*dt,-4,4);
      this.render();this.startFrame();
    });
  }
  pose() {
    const p=automaticPose(this.time,this.options,this.manual);
    const reacting=this.reactionEnd>this.time;
    const expression=reacting?'happy':this.expression;
    p.headAngle=clamp(p.headAngle+this.look*1.5,-5,5);
    if(expression==='surprised') p.mouthOpen=Math.max(.8,p.mouthOpen);
    if(expression==='happy') p.mouthOpen=Math.max(.45,p.mouthOpen);
    return {...p,expression,reacting};
  }
  render() {
    const p=this.pose();
    const lift=p.breath*2.4;
    const body=`translate(0 ${-lift}) translate(300 449) scale(${1+p.breath*.002} ${1+p.breath*.004}) translate(-300 -449)`;
    const head=rotation(p.headAngle,300,218);
    for(const layer of this.layers) {
      let tr=layer.rig==='static'?'':body;
      if(layer.rig==='head') tr+=` ${head}`;
      if(layer.rig.startsWith('hair')) {
        const sign=layer.rig.endsWith('L')?1:-1;
        const swing=this.options.hair?this.hair:p.hairSway;
        tr+=` ${head} ${rotation(clamp(swing*sign,-4,4),...layer.pivot)}`;
      }
      if(layer.rig==='armL') tr+=` ${rotation(p.breath*.25,225,260)}`;
      if(layer.rig==='armR') tr+=` ${rotation(-p.breath*.3-(p.reacting?Math.sin(this.time*8)*2:0),375,260)}`;
      layer.node.setAttribute('transform',tr.trim());
    }
    for (const side of ['left','right']) {
      const x=side==='left'?270:330;
      const open=this.svg.querySelector(`#eye_open_${side}`);
      const closed=this.svg.querySelector(`#eye_closed_${side}`);
      const eye=p.expression==='happy'?.15:p.eyeOpen;
      open.setAttribute('transform',`translate(${x} 156) scale(1 ${Math.max(.04,eye)}) translate(${-x} -156)`);
      open.setAttribute('opacity',eye<.12?'0':'1');
      closed.setAttribute('opacity',eye<.25?'1':'0');
      this.svg.querySelector(`#brow_${side}`).setAttribute('transform',`${body} ${head} translate(0 ${p.expression==='surprised'?-4:p.expression==='happy'?-1:0})`);
    }
    const mouth=this.svg.querySelector('#mouth_open');
    mouth.setAttribute('opacity',String(p.mouthOpen));
    mouth.setAttribute('transform',`translate(300 196) scale(1 ${.1+.9*p.mouthOpen}) translate(-300 -196)`);
    this.svg.querySelector('#mouth_closed').setAttribute('opacity',String(1-p.mouthOpen));
    this.svg.dataset.expression=p.expression;
    this.svg.dataset.eyeOpen=p.eyeOpen.toFixed(3);
    this.svg.dataset.mouthOpen=p.mouthOpen.toFixed(3);
    this.svg.dataset.time=this.time.toFixed(3);
  }
  dispose() {this.disposed=true;this.stopFrame();document.removeEventListener('visibilitychange',this.onVisibility);}
}
