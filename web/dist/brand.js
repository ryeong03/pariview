import * as THREE from 'three';
import {SVGLoader} from './vendor/SVGLoader.js';
import {animate} from './vendor/anime.esm.min.js';

// One letter-free master drawing: SVG for print, extruded geometry for the web.
export async function createBrand(host, reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches) {
 const canvas=host.querySelector('canvas');
 if(!canvas)return null;
 let renderer;
 try{renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:true,preserveDrawingBuffer:true});}catch{return null;}
 renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0,0);
 renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;
 const scene=new THREE.Scene(),group=new THREE.Group();scene.add(group);
 const camera=new THREE.PerspectiveCamera(24,1,.1,1000);camera.position.set(0,0,230);
 scene.add(new THREE.AmbientLight('#e6e5ff',2.5));
 const key=new THREE.DirectionalLight('#ffffff',3);key.position.set(-30,60,100);scene.add(key);
 const fill=new THREE.DirectionalLight('#817aff',4);fill.position.set(80,-10,20);scene.add(fill);
 const isWord=host.dataset.wordmark==='true';
 const svg=await fetch(isWord?'assets/pariview-wordmark.svg':'assets/pariview-symbol.svg').then(r=>r.text());
 const parsed=new SVGLoader().parse(svg);const pieces=[];
 for(const path of parsed.paths){
  for(const shape of SVGLoader.createShapes(path)){
   const geo=new THREE.ExtrudeGeometry(shape,{depth:3,bevelEnabled:true,bevelSegments:3,steps:1,bevelSize:.65,bevelThickness:.65,curveSegments:20});
   if(!isWord){geo.translate(-60,-38,-1.5);geo.scale(1,-1,1);}
   const material=new THREE.MeshPhysicalMaterial({color:host.dataset.tone==='dark'?(isWord?'#17181b':'#fa0030'):'#f6f5ff',metalness:.12,roughness:.32,clearcoat:.8,side:THREE.DoubleSide,emissive:host.dataset.tone==='dark'?'#000000':'#c5c3d1',emissiveIntensity:.15});
   const mesh=new THREE.Mesh(geo,material);group.add(mesh);pieces.push(mesh);
  }
 }
 if(isWord){const bounds=new THREE.Box3().setFromObject(group),center=bounds.getCenter(new THREE.Vector3()),size=bounds.getSize(new THREE.Vector3()),scale=120/size.x;pieces.forEach(p=>{p.geometry.translate(-center.x,-center.y,-center.z);p.geometry.scale(scale,-scale,1);});}
 group.rotation.x=-.08;group.rotation.y=-.07;
 let animation;
 function render(){renderer.render(scene,camera);}
 function resize(){const r=host.getBoundingClientRect();if(!r.width||!r.height)return;renderer.setSize(r.width,r.height,false);camera.aspect=r.width/r.height;const width=126,height=isWord?32:72;camera.position.z=Math.max(height/2,width/2/camera.aspect)/Math.tan(12*Math.PI/180)+12;camera.updateProjectionMatrix();render();}
 new ResizeObserver(resize).observe(host);resize();
 function settle(){animation?.cancel();group.rotation.set(-.08,-.07,0);pieces.forEach(p=>p.position.set(0,0,0));render();}
 function reveal(){if(reduced()){settle();return;}pieces.forEach((p,i)=>{p.position.x=i===0?-15:i===1?15:0;p.position.z=i===2?-7:0;animate(p.position,{x:0,z:0,duration:850,delay:i*90,ease:'out(4)',onUpdate:render});});}
 host.addEventListener('pointerenter',()=>{if(reduced())return;animation?.cancel();animation=animate(group.rotation,{y:.23,x:.12,duration:500,ease:'out(3)',onUpdate:render});});
 host.addEventListener('pointerleave',()=>{animation?.cancel();if(reduced()){settle();return;}animation=animate(group.rotation,{y:-.09,x:-.12,duration:650,ease:'out(3)',onUpdate:render});});
 host.addEventListener('click',reveal);document.addEventListener('pariview-motion-change',settle);
 host.classList.add('brand-ready');reveal();
 const api={renderer,scene,camera,group,settle,reveal,engine:'Three.js '+THREE.REVISION+' + Anime.js 4.1.3'};
 if(isWord)window.__wordmark3D=api;else window.__brand3D=api;return api;
}
