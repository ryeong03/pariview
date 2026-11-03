/** Synthetic preference evaluation of the actual browser engine. No participant records. */
import {createAdaptiveFit,FIT_BOUNDS,ADAPTIVE_FIT_CONFIG} from '../../web/dist/adaptive-fit.js';
import {defaults} from '../../web/dist/settings.js';
import {readFileSync,mkdirSync,writeFileSync,createWriteStream} from 'node:fs';
import {createHash} from 'node:crypto';
import {createGzip} from 'node:zlib';
import {once} from 'node:events';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const HERE=path.dirname(fileURLToPath(import.meta.url));
const opt=name=>process.argv.find(x=>x.startsWith(`--${name}=`))?.split('=').slice(1).join('=');
const N=Number(opt('n')||500),SEED=20261104;
const OUT=path.resolve(opt('out')||HERE);
const AXES=['brightness','contrast','volume'];
const BOUNDS={brightness:[45,100],contrast:[65,110],volume:[0,70]};
const SCENARIOS=[
 {id:'deterministic',tau:0,lapse:0},
 {id:'matched',tau:.08,lapse:.10},
 {id:'noisy',tau:.16,lapse:.20},
 {id:'nonresponse',tau:.08,lapse:.10,equal:.10,unsure:.10,skip:.05},
 {id:'asymmetric',tau:.08,lapse:.10,asymmetric:true}
];
function rng(seed){let a=seed>>>0;return()=>{a+=0x6D2B79F5;let t=a;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};}
function norm(axis,value){const [lo,hi]=BOUNDS[axis];return(value-lo)/(hi-lo);}
function utility(x,theta,scenario){return -((x-theta)**2)*(scenario.asymmetric?(x<theta?1.5:.6):1);}
function respond(q,theta,scenario,noise,nonresponse){
 let cutoff=scenario.equal||0;if(nonresponse<cutoff)return'equal';
 cutoff+=scenario.unsure||0;if(nonresponse<cutoff)return'unsure';
 cutoff+=scenario.skip||0;if(nonresponse<cutoff)return'skip';
 const lo=Math.min(q.a,q.b),hi=Math.max(q.a,q.b);
 const ul=utility(norm(q.axis,lo),theta[q.axis],scenario),uh=utility(norm(q.axis,hi),theta[q.axis],scenario);
 const probability=scenario.tau===0?(ul===uh?.5:ul>uh?1:0):scenario.lapse/2+(1-scenario.lapse)/(1+Math.exp(-(ul-uh)/scenario.tau));
 const chosen=noise<probability?lo:hi;return chosen===q.a?'a':'b';
}
function point(settings,uncertainty,truth,round){
 const estimate=Object.fromEntries(AXES.map(k=>[k,settings[k]]));
 for(const axis of AXES){if(!Number.isFinite(estimate[axis])||estimate[axis]<BOUNDS[axis][0]||estimate[axis]>BOUNDS[axis][1])throw Error('Invalid estimate '+axis);}
 return{round,estimate,nmae:AXES.reduce((s,k)=>s+Math.abs(norm(k,estimate[k])-truth[k]),0)/3,
        intervals:Object.fromEntries(AXES.map(k=>{const u=uncertainty?.[k];return[k,u?{lower:u.normalizedLower,upper:u.normalizedUpper,width:u.normalizedWidth,contains:truth[k]>=u.normalizedLower&&truth[k]<=u.normalizedUpper}:null];}))};
}
const enginePath=path.resolve(HERE,'../../web/dist/adaptive-fit.js');
const engineHash=()=>createHash('sha256').update(readFileSync(enginePath)).digest('hex');
const startHash=engineHash();
const settingsHash=createHash('sha256').update(readFileSync(path.resolve(HERE,'../../web/dist/settings.js'))).digest('hex');
const truthRng=rng(SEED),truths=Array.from({length:N},()=>Object.fromEntries(AXES.map(k=>[k,truthRng()])));
mkdirSync(OUT,{recursive:true});
const gzip=createGzip({level:9}),dest=createWriteStream(path.join(OUT,'synthetic-records.jsonl.gz'));
gzip.pipe(dest);const completed=once(dest,'finish');
let records=0;
for(const [conditionIndex,scenario] of SCENARIOS.entries()){
 for(let index=0;index<N;index++){
  const truth=truths[index],responseRng=rng(SEED+100003*(conditionIndex+1)+7919*index);
  const draws=Array.from({length:5},()=>({noise:responseRng(),nonresponse:responseRng()}));
  const paired={data_kind:'synthetic',case_id:index+1,scenario:scenario.id,truth,policies:{}};
  for(const policy of ['adaptive','fixed']){
   const fit=createAdaptiveFit({settings:{...defaults},budget:5,seed:SEED+3571*index,policy,context:{source:'synthetic-preference-simulation'}});
   const initial=fit.result();const points=[point(initial.settings,initial.uncertainty,truth,0)],questions=[];
   for(let round=0;round<5;round++){
    const q=fit.peek();if(!q)throw Error(`Stopped before budget: ${policy}/${round}`);
    const outcome=respond(q,truth,scenario,draws[round].noise,draws[round].nonresponse);
    fit.answer(q.id,outcome);const result=fit.result();
    points.push(point(result.settings,result.uncertainty,truth,round+1));
    questions.push({id:q.id,axis:q.axis,a:q.a,b:q.b,placement:q.placement,informationGain:q.expectedInformationGain,outcome});
   }
   const result=fit.result();
   if(fit.peek()!==null)throw Error('Expected budget stop');
   paired.policies[policy]={points,questions,counts:result.counts,stopReason:result.stopReason};
  }
  // Historical UI reference: only 3 numeric questions; rounds 4–5 were boolean.
  const legacy={...defaults},legacyPoints=[point(legacy,null,truth,0)];
  const pairs=[['brightness',65,90],['contrast',78,105],['volume',22,45]];
  for(let round=0;round<5;round++){
   if(round<3){const [axis,a,b]=pairs[round],q={axis,a,b};const outcome=respond(q,truth,scenario,draws[round].noise,draws[round].nonresponse);if(outcome==='a'||outcome==='b')legacy[axis]=q[outcome];}
   legacyPoints.push(point(legacy,null,truth,round+1));
  }
  paired.legacy_reference={points:legacyPoints,numeric_comparisons:3,boolean_comparisons:2};
  if(!gzip.write(JSON.stringify(paired)+'\n'))await once(gzip,'drain');records++;
 }
 console.log(`${scenario.id}: ${N} synthetic cases × 2 policies complete`);
}
gzip.end();await completed;
if(engineHash()!==startHash)throw Error('Engine changed during run; repeat using a stable version');
const metadata={kind:'synthetic_algorithm_evaluation',created_at:new Date().toISOString(),seed:SEED,n_per_condition:N,scenarios:SCENARIOS,
 config:ADAPTIVE_FIT_CONFIG,exported_bounds:FIT_BOUNDS,evaluation_bounds:BOUNDS,engine_sha256:startHash,settings_sha256:settingsHash,
 initial_settings:{brightness:defaults.brightness,contrast:defaults.contrast,volume:defaults.volume},comparisons:5,
 primary_policies:['adaptive','fixed'],records,actual_participant_records:0,
 interpretation:'Finite-budget normalized setting error under declared synthetic preference models; not comfort, clinical benefit, or a five-trial convergence guarantee'};
writeFileSync(path.join(OUT,'simulation-metadata.json'),JSON.stringify(metadata,null,2)+'\n');
console.log(JSON.stringify({records,n_per_condition:N,engine_sha256:startHash,output:OUT}));
