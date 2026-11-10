import {LayeredCharacter} from './character.mjs';

const host=document.querySelector('#character-host');
const status=document.querySelector('#app-status');
const controls=[...document.querySelectorAll('button,input')];
controls.forEach(element=>element.disabled=true);
let character, greetingTimer, interactionIndex=0;
function sync() {
  for(const input of document.querySelectorAll('[data-option]')) input.checked=character.options[input.dataset.option];
  for(const input of document.querySelectorAll('[data-parameter]')) {
    const key=input.dataset.parameter;
    input.value=String(character.manual[key]);
    document.querySelector(`#${key}-value`).textContent=Number(input.value).toFixed(2)+(key==='headAngle'||key==='hairSway'?'°':'');
  }
  for(const button of document.querySelectorAll('[data-expression]')) button.setAttribute('aria-pressed',String(character.expression===button.dataset.expression));
}
try {
  const [art,metadata]=await Promise.all([fetch('assets/character/character.svg'),fetch('assets/character/manifest.json')]);
  if(!art.ok||!metadata.ok) throw new Error('素材載入失敗');
  const markup=await art.text();
  const doc=new DOMParser().parseFromString(markup,'image/svg+xml');
  if(doc.querySelector('parsererror')||doc.documentElement.localName!=='svg') throw new Error('SVG 格式錯誤');
  const svg=document.importNode(doc.documentElement,true);
  svg.setAttribute('aria-hidden','true'); svg.setAttribute('focusable','false');
  host.replaceChildren(svg);
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  character=new LayeredCharacter(svg,await metadata.json(),{reducedMotion:reduced});
  // Explicit integration/debug handle; the reusable runtime is independent of this UI.
  window.character=character;
  controls.forEach(element=>element.disabled=false);
  sync();
  status.textContent=`27 個圖層已載入 · ${reduced?'已減少自動動態':'可互動'}`;
  for(const input of document.querySelectorAll('[data-option]')) input.addEventListener('change',()=>character.setOptions({[input.dataset.option]:input.checked}));
  const automatic={eyeOpen:'blink',mouthOpen:'talk',headAngle:'sway',breath:'breathe',hairSway:'hair'};
  for(const input of document.querySelectorAll('[data-parameter]')) input.addEventListener('input',()=>{
    character.setOptions({[automatic[input.dataset.parameter]]:false});
    character.setExpression('neutral'); character.reactionEnd=0;character.setLook(0);
    character.setParameter(input.dataset.parameter,Number(input.value));sync();
  });
  for(const button of document.querySelectorAll('[data-expression]')) button.addEventListener('click',()=>{character.reactionEnd=0;character.setExpression(button.dataset.expression);sync();});
  const greet=()=>character.triggerReaction();
  const interact=()=>character.triggerReaction(['greeting','smile','surprise'][interactionIndex++%3]);
  for(const button of document.querySelectorAll('[data-reaction]')) button.addEventListener('click',()=>character.triggerReaction(button.dataset.reaction));
  character.addEventListener('performance',event=>{
    document.querySelector('#fps-value').textContent=event.detail.fps===null?(event.detail.paused?'暫停':'量測中'):`${event.detail.fps.toFixed(1)} FPS`;
  });
  host.addEventListener('click',interact);
  host.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();greet();}});
  host.addEventListener('pointermove',event=>{
    if(event.pointerType==='touch') return;
    const bounds=host.getBoundingClientRect();
    character.setLook((event.clientX-bounds.left)/bounds.width*2-1);
  });
  host.addEventListener('pointerleave',()=>character.setLook(0));
  document.querySelector('#greet').addEventListener('click',greet);
  character.addEventListener('interaction',()=>{
    const bubble=document.querySelector('#greeting');bubble.textContent=({greeting:'你好，很高興見到你。',wave:'嗨！在這裡喔。',smile:'今天也一起加油吧。',surprise:'咦？是你呀！'})[character.reactionType];bubble.classList.add('visible');
    clearTimeout(greetingTimer);greetingTimer=setTimeout(()=>bubble.classList.remove('visible'),2400);
  });
  document.querySelector('#pause').addEventListener('click',event=>{
    character.setPaused(!character.paused);
    event.currentTarget.textContent=character.paused?'繼續動畫':'暫停動畫';
    event.currentTarget.setAttribute('aria-pressed',String(character.paused));
    document.querySelector('#play-state').textContent=character.paused?'動畫已暫停':'即時動畫';
  });
  document.querySelector('#reset').addEventListener('click',()=>{
    interactionIndex=0;character.reset();character.setOptions({blink:true,talk:false,breathe:!reduced,sway:!reduced,hair:!reduced,idle:!reduced});
    character.setPaused(false);document.querySelector('#pause').textContent='暫停動畫';document.querySelector('#pause').setAttribute('aria-pressed','false');
    document.querySelector('#play-state').textContent='即時動畫';
    clearTimeout(greetingTimer);document.querySelector('#greeting').classList.remove('visible');sync();
  });
  window.addEventListener('pagehide',()=>character.dispose());
  window.addEventListener('pageshow',event=>{if(event.persisted) location.reload();});
} catch(error) {
  host.textContent='無法載入角色，請使用 HTTP 伺服器開啟此頁面後重新整理。';
  host.removeAttribute('role'); host.removeAttribute('tabindex');
  status.textContent=`載入失敗：${error.message}`;status.style.color='#e8a8ad';
}
