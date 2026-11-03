import {animate,createSpring} from './vendor/anime.esm.min.js';

export function initInteractions(isReduced){
 const active=new Map();
 const pressable='button:not(:disabled),a.primary,a.secondary';
 const cards='.profile-card,.scene-option,.mode-option,.research-card';
 const spring=()=>createSpring({stiffness:340,damping:23});
 function move(element,options){
  if(!element||isReduced())return;
  active.get(element)?.cancel();
  const animation=animate(element,{...options,ease:spring(),onComplete:()=>active.delete(element)});
  active.set(element,animation);
 }
 document.addEventListener('pointerover',event=>{
  if(event.pointerType==='touch')return;
  const target=event.target.closest(pressable);
  if(target&&!target.contains(event.relatedTarget))move(target,{scale:1.025});
  const card=event.target.closest(cards);
  if(card&&!card.contains(event.relatedTarget))move(card,{scale:1.015,y:-3});
 });
 document.addEventListener('pointerout',event=>{
  const target=event.target.closest(pressable);
  if(target&&!target.contains(event.relatedTarget))move(target,{scale:1,y:0});
  const card=event.target.closest(cards);
  if(card&&!card.contains(event.relatedTarget))move(card,{scale:1,y:0});
 });
 document.addEventListener('pointerdown',event=>move(event.target.closest(pressable),{scale:.96}));
 document.addEventListener('pointerup',event=>move(event.target.closest(pressable),{scale:1}));
 document.addEventListener('pointercancel',event=>move(event.target.closest(pressable),{scale:1,y:0}));
 document.addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key))move(event.target.closest(pressable),{scale:.96});});
 document.addEventListener('keyup',event=>{if(['Enter',' '].includes(event.key))move(event.target.closest(pressable),{scale:1});});
 document.addEventListener('input',event=>{
  if(event.target.type!=='range')return;
  const output=event.target.closest('.preference-group,.pv-rec-control')?.querySelector('output');
  if(output){output.style.display='inline-block';move(output,{scale:[1.08,1]});}
 });
 document.addEventListener('click',event=>{
  if(!event.target.closest('#save-settings,#apply-fit,[data-apply]')||isReduced())return;
  for(const mascot of window.__pariviewMascots||[]){
   const rect=mascot.renderer.domElement.getBoundingClientRect();
   if(rect.bottom>0&&rect.top<innerHeight&&rect.width)mascot.wave();
  }
 });
 new MutationObserver(records=>{
  for(const {target} of records){
   if(target.tagName!=='DIALOG'||!target.open||target.id==='fit-dialog')continue;
   move(target.firstElementChild,{opacity:[.55,1],y:[10,0],scale:[.985,1]});
  }
 }).observe(document.body,{subtree:true,attributes:true,attributeFilter:['open']});
 document.addEventListener('pariview-motion-change',()=>{
  if(!isReduced())return;
  for(const [element,animation] of active){animation.cancel();element.style.removeProperty('transform');element.style.removeProperty('opacity');}
  active.clear();
 });
 window.__pariviewInteractions={engine:'Anime.js spring + Three.js mascots',get active(){return active.size}};
}
