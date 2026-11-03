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

export function defaultSelection(plan) {
  const actionIds = plan.candidates.filter(x=>x.id!=='keep').slice(0,3).map(x=>x.id);
  return {actionIds:actionIds.length ? actionIds : ['keep'],nextComparisonId:plan.comparisons[0]?.id || 'done'};
}

export function composeRecommendation(plan, catalog, selection=defaultSelection(plan), source='rules') {
  if (!selection || !Array.isArray(selection.actionIds) || selection.actionIds.length<1 || selection.actionIds.length>3 ||
      new Set(selection.actionIds).size!==selection.actionIds.length ||
      (selection.actionIds.includes('keep') && selection.actionIds.length!==1)) throw new Error('Invalid selection');
  const actions=selection.actionIds.map(id=>plan.candidates.find(x=>x.id===id));
  if (actions.some(x=>!x)) throw new Error('Unknown candidate');
  const nextComparison=plan.comparisons.find(x=>x.id===selection.nextComparisonId) || null;
  if (!nextComparison && !(selection.nextComparisonId==='done' && plan.comparisons.length===0)) throw new Error('Unknown comparison');
  const settings={...plan.settings};
  for(const action of actions) Object.assign(settings,action.changes);
  const sourceIds=[...new Set([...actions.flatMap(x=>x.sourceIds),...(nextComparison?.sourceIds || [])])];
  return {source:source==='ai'?'ai':'rules',evidenceVersion:catalog.version,selection,settings:normalize(settings),actions,nextComparison,
    sources:sourceIds.map(id=>catalog.sources[id]),boundary:catalog.boundary};
}
