import * as THREE from 'three';
import {animate} from './vendor/anime.esm.min.js';

// A small coral falcon, drawn as rounded 3D forms with black contour details.
// The two characters share one model; the studio variant adds a hat and wand.
export function createFalcon(host,{wizard=false,reduced=()=>false}={}){
 const canvas=host.querySelector('canvas');let renderer;
 try{renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:true,preserveDrawingBuffer:true});}catch{return null;}
 renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0,0);renderer.outputColorSpace=THREE.SRGBColorSpace;
 renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;
 const scene=new THREE.Scene(),bird=new THREE.Group();scene.add(bird);
 const camera=new THREE.OrthographicCamera(-2.1,2.1,2.5,-2.1,.1,50);camera.position.set(0,.4,12);camera.lookAt(0,.15,0);
 scene.add(new THREE.AmbientLight('#ffffff',2));const key=new THREE.DirectionalLight('#fff7ed',3);key.position.set(-3,6,8);scene.add(key);
 const fill=new THREE.DirectionalLight('#d9e4ff',1.3);fill.position.set(4,2,-3);scene.add(fill);
 const mat=(color,roughness=.75)=>new THREE.MeshStandardMaterial({color,roughness,metalness:0});
 const coral=mat('#ff604e'),coralDark=mat('#cd5145'),cream=mat('#fff5df'),ink=mat('#181a1d'),gold=mat('#ffb52e'),hatmat=mat('#292b36');
 function oval(parent,x,y,z,sx,sy,sz,material){const mesh=new THREE.Mesh(new THREE.SphereGeometry(1,40,32),material);mesh.position.set(x,y,z);mesh.scale.set(sx,sy,sz);parent.add(mesh);return mesh;}
 function tube(parent,points,r=.025,material=ink){const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));const mesh=new THREE.Mesh(new THREE.TubeGeometry(curve,32,r,8,false),material);parent.add(mesh);return mesh;}
 function flatShape(parent,draw,material,depth=.1){const shape=new THREE.Shape();draw(shape);const geo=new THREE.ExtrudeGeometry(shape,{depth,bevelEnabled:true,bevelSize:.04,bevelThickness:.04,bevelSegments:3,steps:1,curveSegments:24});const mesh=new THREE.Mesh(geo,material);parent.add(mesh);return mesh;}
 // Rounded coral silhouette with tiny swept feathers and circular glasses.
 const points=[];for(let i=0;i<=36;i++){const t=Math.PI*i/36,y=-.68+1.5*(1-Math.cos(t))/2;const radius=Math.sin(t)*(.91-.17*Math.sin(t-Math.PI/2));points.push(new THREE.Vector2(Math.max(0,radius),y));}
 const body=new THREE.Mesh(new THREE.LatheGeometry(points,56),coral);body.scale.set(1,1.47,.76);bird.add(body);
 oval(bird,0,.72,.08,.77,.73,.63,coral);
 if(!wizard){for(let i=0;i<2;i++){const f=oval(bird,-.1+i*.16,1.37+i*.035,-.05,.075,.16,.10,coral);f.rotation.z=-.7;}}
 const face=new THREE.Group();face.position.set(0,.61,.67);bird.add(face);
 [-1,1].forEach(side=>{
  oval(face,side*.29,.10,.004,.245,.25,.035,cream);
  const ring=new THREE.Mesh(new THREE.TorusGeometry(.245,.031,12,64),ink);ring.position.set(side*.29,.10,.05);face.add(ring);
  const pupil=oval(face,side*.29+(wizard?-.025:.025),.10,.07,.054,.077,.023,ink);pupil.userData.eye=true;
  oval(face,side*.29+(wizard?-.014:.036),.128,.091,.013,.016,.007,mat('#ffffff'));
 });
 tube(face,[[-.045,.12,.06],[0,.13,.08],[.045,.12,.06]],.028);
 tube(face,[[-.535,.15,.03],[-.68,.20,-.09],[-.73,.14,-.28]],.024);tube(face,[[.535,.15,.03],[.68,.20,-.09],[.73,.14,-.28]],.024);
 // The small rounded beak is centered and has a soft smile.
 oval(face,0,-.20,.045,.09,.105,.075,gold);
 tube(face,[[-.04,-.20,.115],[0,-.235,.124],[.04,-.20,.115]],.012,coralDark);
 const wingL=new THREE.Group();wingL.position.set(-.7,.18,.02);bird.add(wingL);
 const wingR=new THREE.Group();wingR.position.set(.7,.18,.02);bird.add(wingR);
 const left=oval(wingL,-.1,-.25,.1,.25,.56,.24,coral);left.rotation.z=-.25;
 const right=oval(wingR,.15,.05,.1,.25,.53,.24,coral);right.rotation.z=-.7;
 tube(wingL,[[-.13,-.18,.33],[-.2,-.48,.30],[-.11,-.64,.19]],.021);
 tube(wingR,[[.15,-.08,.32],[.31,.11,.30],[.31,.28,.17]],.021);
 for(const side of [-1,1]){
  tube(bird,[[side*.31,-.85,.02],[side*.34,-1.22,.08],[side*.48,-1.28,.27]],.055,ink);
  oval(bird,side*.38,-1.3,.21,.22,.10,.19,ink);
 }
 // A thin curved tail with two visible feather tips.
 oval(bird,-.39,-.69,-.42,.23,.35,.12,coral).rotation.z=-.45;
 let wand,star;
 if(wizard){
  const brim=oval(bird,0,1.29,.03,1.03,.075,.64,hatmat);brim.rotation.z=-.07;
  const crown=flatShape(bird,s=>{s.moveTo(-.65,1.3);s.lineTo(-.34,2.15);s.quadraticCurveTo(-.17,2.47,.07,2.28);s.quadraticCurveTo(.32,2.13,.65,2.18);s.lineTo(.29,1.91);s.lineTo(.56,1.29);s.closePath();},hatmat,.34);crown.position.z=-.17;
  tube(bird,[[-.55,1.49,.30],[0,1.45,.37],[.48,1.45,.30]],.06,coralDark);
  const buckle=new THREE.Mesh(new THREE.TorusGeometry(.1,.026,8,4),gold);buckle.position.set(.13,1.46,.43);buckle.rotation.z=Math.PI/4;bird.add(buckle);
  // The wand lives in the raised right wing so it moves with the wave; a small fist wraps its handle
  wand=new THREE.Group();wand.position.set(.415,.293,.2);wand.rotation.z=-.25;wingR.add(wand);
  tube(wand,[[0,-.2,0],[0,.85,0]],.035,ink);tube(wand,[[0,.68,0],[0,.89,0]],.037,cream);
  star=flatShape(wand,s=>{for(let i=0;i<8;i++){const r=i%2?.045:.14,a=Math.PI*i/4;const x=Math.sin(a)*r,y=1.04+Math.cos(a)*r;i?s.lineTo(x,y):s.moveTo(x,y);}s.closePath();},gold,.035);
  star.position.z=.04;
  oval(wingR,.44,.39,.27,.105,.09,.095,coral);
  tube(wingR,[[.36,.42,.33],[.43,.47,.35],[.52,.42,.33]],.018);
  tube(wingR,[[.37,.35,.33],[.45,.33,.35],[.53,.37,.32]],.016);
 }
 const shadow=new THREE.Mesh(new THREE.CircleGeometry(.85,64),new THREE.MeshBasicMaterial({color:'#ddd8d5',transparent:true,opacity:.24,depthWrite:false}));shadow.rotation.x=-Math.PI/2;shadow.scale.y=.42;shadow.position.y=-1.43;scene.add(shadow);
 const facing=wizard?-.25:.25;bird.rotation.y=facing;bird.position.y=wizard?-.36:0;
 let visible=true,anim=null;const eyes=[];bird.traverse(o=>{if(o.userData.eye)eyes.push(o);});
 function render(){renderer.render(scene,camera);}
 function resize(){const box=host.getBoundingClientRect();if(!box.width||!box.height)return;renderer.setSize(box.width,box.height,false);const h=wizard?4.9:4.15,w=h*box.width/box.height;camera.left=-w/2;camera.right=w/2;camera.top=h/2;camera.bottom=-h/2;camera.updateProjectionMatrix();render();}
 new ResizeObserver(resize).observe(host);new IntersectionObserver(e=>visible=e[0].isIntersecting).observe(host);resize();
 function wave(){if(reduced())return;anim?.cancel();const state={p:0};anim=animate(state,{p:1,duration:1300,ease:'linear',onUpdate:()=>{const t=state.p;wingR.rotation.z=Math.sin(t*Math.PI*4)*.18*(1-t);bird.rotation.y=facing+Math.sin(t*Math.PI)*.15;if(wand)wand.rotation.z=-.25+Math.sin(t*Math.PI*2)*.13;if(star)star.scale.setScalar(1+Math.sin(t*Math.PI)*.22);render();}});}
 const blink=setInterval(()=>{if(reduced()||!visible||document.hidden)return;const state={p:0};animate(state,{p:1,duration:280,ease:'linear',onUpdate:()=>{const s=1-Math.sin(state.p*Math.PI)*.92;eyes.forEach(e=>e.scale.y=.077*s);render();}});},7000);
 host.addEventListener('pointerenter',wave);host.addEventListener('click',wave);
 document.addEventListener('pariview-motion-change',()=>{anim?.cancel();wingR.rotation.z=0;bird.rotation.y=facing;if(wand)wand.rotation.z=-.25;eyes.forEach(e=>e.scale.y=.077);render();});
 host.classList.add('mascot-ready');wave();
 const api={renderer,scene,camera,bird,render,resize,wave,engine:'Three.js '+THREE.REVISION+' + Anime.js 4.1.3',wizard,dispose(){clearInterval(blink);renderer.dispose();}};
 window.__pariviewMascots??=[];window.__pariviewMascots.push(api);return api;
}
