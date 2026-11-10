/** Eyelids deform the aperture; iris and pupil never scale or translate during blink. */
import {clamp} from './motion.mjs';
export function eyeGeometry(x, openness, smile=0) {
  const a=clamp(openness,0,1), s=clamp(smile,0,1);
  const bend=2-8*s;
  const upper=`M${x-20} 156 Q${x} ${156+bend-22*a} ${x+20} 156`;
  const lower=`M${x+20} 156 Q${x} ${156+bend+22*a} ${x-20} 156`;
  return {aperture:`${upper} Q${x} ${156+bend+22*a} ${x-20} 156 Z`,upper,lower,
    closed:`M${x-20} 156 Q${x} ${156+bend} ${x+20} 156`};
}
export function expressiveEye(open, weights) {
  const happy=weights.happy??0, closed=weights.closedSmile??0, half=weights.halfLidded??0;
  return {openness:clamp(open,0,1)*clamp(1-.06*happy-closed-.5*half,0,1),
    smile:clamp(happy+closed,0,1)};
}
