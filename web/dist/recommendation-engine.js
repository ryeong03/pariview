// Shared, inspectable candidate policy — these rules are never labelled AI output
import {normalize} from './settings.js';

const outcomes = new Set(['a','b','equal','unsure','skip']);
export function prepareRecommendation(payload, catalog) {
  const settings = normalize(payload.currentSettings || {});
  const answers = {};
  for (const [key, choices] of Object.entries(catalog.inputs)) {
    if (key === 'concerns') answers[key] = [...new Set((Array.isArray(payload.answers?.[key]) ? payload.answers[key] : []).filter(x => Object.hasOwn(choices,x)))];
    else answers[key] = Object.hasOwn(choices,payload.answers?.[key]) ? payload.answers[key] : Object.keys(choices)[0];
  }
  const signals = new Set(Object.entries(answers).flatMap(([k,v]) => (Array.isArray(v) ? v : [v]).map(x => `${k}:${x}`)));
  const axes = new Set(catalog.comparisons.map(x => x.id));
  const history = new Map();
  for (const item of (Array.isArray(payload.comparisons) ? payload.comparisons : []).slice(-20)) {
    if (axes.has(item?.axis) && outcomes.has(item?.outcome)) history.set(item.axis,item.outcome);
  }
  const label = signal => { const [key,value] = signal.split(':'); return catalog.inputs[key][value]; };
  const reason = matches => matches.length ? `‘${matches.map(label).join('’, ‘')}’를 선택한 응답을 참고했어요` : '지금 설정을 유지하며 직접 비교할 수 있는 출발점이에요';
  const candidates = catalog.actions.filter(a => a.id === 'keep' || (
    a.matchAny.some(x => signals.has(x)) && !a.unlessAny.some(x => signals.has(x)) &&
    !['a','b','equal','skip'].includes(history.get(a.axis))
  )).map(a => {
    const changes = {};
    for (const [key,op] of Object.entries(a.adjust)) {
      const range = catalog.ranges[key];
      changes[key] = Object.hasOwn(op,'set') ? op.set : Math.max(range[0], Math.min(range[1], settings[key] + op.delta));
    }
    return {id:a.id,title:a.title,axis:a.axis,changes,sourceIds:a.sources,reason:reason(a.matchAny.filter(x=>signals.has(x)))};
  });
  const comparisons = catalog.comparisons.filter(c => !['a','b','equal','skip'].includes(history.get(c.id))).map(c => {
    const matches = c.matchAny.filter(x=>signals.has(x));
    const unsure = history.get(c.id) === 'unsure';
    return {id:c.id,axis:c.id,title:c.title,sourceIds:c.sources,priority:matches.length ? 2 : 0,
      reason:`${matches.length ? reason(matches)+' ' : ''}${unsure ? '앞서 판단을 보류한 항목이라 원할 때 다시 비교할 수 있어요' : '아직 선택하지 않은 항목이라 다음 비교 후보로 제안해요'}`};
  }).sort((a,b)=>b.priority-a.priority);
  return {settings,answers,candidates,comparisons,history:[...history].map(([axis,outcome])=>({axis,outcome}))};
}

// AI path with a written sentence: matchAny is waived; unlessAny and decided comparisons still use the real answers.
// Mirrors ai/domain.py ai_plan(). The rules fallback always uses the original plan.
export const EXPERIENCE_REASON = '적은 문장을 참고해 고른 준비된 설정이에요';
export function planForAI(plan, catalog, experience='') {
  const modeIds = ['keep'];
  if (!String(experience).trim()) return {...plan, open:false, modeIds};
  const signals = new Set(Object.entries(plan.answers).flatMap(([k,v]) => (Array.isArray(v) ? v : [v]).map(x => `${k}:${x}`)));
  const decided = new Set(plan.history.filter(h => ['a','b','equal','skip'].includes(h.outcome)).map(h => h.axis));
  const known = new Map(plan.candidates.map(c => [c.id,c]));
  const candidates = catalog.actions.filter(a => a.id === 'keep' || (!a.unlessAny.some(x => signals.has(x)) && !decided.has(a.axis))).map(a => {
    if (known.has(a.id)) return {...known.get(a.id), matched:true};
    const changes = {};
    for (const [key,op] of Object.entries(a.adjust)) {
      const range = catalog.ranges[key];
      changes[key] = Object.hasOwn(op,'set') ? op.set : Math.max(range[0], Math.min(range[1], plan.settings[key] + op.delta));
    }
    return {id:a.id,title:a.title,axis:a.axis,changes,sourceIds:a.sources,reason:EXPERIENCE_REASON,matched:false};
  });
  if (plan.answers.goal !== 'original') modeIds.push(...(catalog.startingModes || []).map(m => m.id));
  return {...plan, candidates, open:true, modeIds};
}

export function defaultSelection(plan) {
  const actionIds = plan.candidates.filter(x=>x.id!=='keep').slice(0,3).map(x=>x.id);
  return {actionIds:actionIds.length ? actionIds : ['keep'],nextComparisonId:plan.comparisons[0]?.id || 'done',startingModeId:'keep'};
}

export function composeRecommendation(plan, catalog, selection=defaultSelection(plan), source='rules') {
  if (!selection || !Array.isArray(selection.actionIds) || selection.actionIds.length<1 || selection.actionIds.length>3 ||
      new Set(selection.actionIds).size!==selection.actionIds.length ||
      (selection.actionIds.includes('keep') && selection.actionIds.length!==1)) throw new Error('Invalid selection');
  const actions=selection.actionIds.map(id=>plan.candidates.find(x=>x.id===id));
  if (actions.some(x=>!x)) throw new Error('Unknown candidate');
  // Two chosen actions may not set the same key to different values (e.g. soft vs clear contrast)
  const seen={};
  for (const action of actions) for (const [key,value] of Object.entries(action.changes)) {
    if (Object.hasOwn(seen,key) && seen[key]!==value) throw new Error('Conflicting candidates');
    seen[key]=value;
  }
  // Older two-field selections mean "keep the current mode"; an open AI plan must name a mode explicitly
  if (Object.keys(selection).some(k=>!['actionIds','nextComparisonId','startingModeId'].includes(k))) throw new Error('Unsupported selection field');
  if (selection.startingModeId===null) throw new Error('Invalid starting mode');
  // Only a verified AI response may choose a mode; rules always keep the current one
  const modeIds=source==='ai' ? (plan.modeIds || ['keep']) : ['keep'];
  if (selection.startingModeId===undefined && plan.open && source==='ai') throw new Error('Missing starting mode');
  const startingModeId=selection.startingModeId ?? 'keep';
  if (!modeIds.includes(startingModeId)) throw new Error('Unknown starting mode');
  const nextComparison=plan.comparisons.find(x=>x.id===selection.nextComparisonId) || null;
  if (!nextComparison && !(selection.nextComparisonId==='done' && plan.comparisons.length===0)) throw new Error('Unknown comparison');
  const settings={...plan.settings};
  for(const action of actions) Object.assign(settings,action.changes);
  // Only the mode label changes; preset values are never applied wholesale
  if (startingModeId!=='keep') settings.profileId=startingModeId;
  const startingMode=startingModeId==='keep' ? null : (catalog.startingModes || []).find(m=>m.id===startingModeId) || null;
  const sourceIds=[...new Set([...actions.flatMap(x=>x.sourceIds),...(nextComparison?.sourceIds || [])])];
  return {source:source==='ai'?'ai':'rules',evidenceVersion:catalog.version,selection:{...selection,startingModeId},settings:normalize(settings),actions,nextComparison,startingMode,
    sources:sourceIds.map(id=>catalog.sources[id]),boundary:catalog.boundary};
}
