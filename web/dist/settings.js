export const defaults = {profileId:'everyday',brightness:85,contrast:90,saturation:100,warmth:0,volume:35,highCut:0,compression:true,notices:true,dialogueBoost:false,autoBrightness:false,captions:true,easyCaptions:false,captionSize:20,boldCaptions:false,breakReminder:false,backgroundReduction:0,transitionSoftening:false};
export const ranges = {brightness:[45,100],contrast:[65,110],saturation:[40,110],warmth:[0,60],volume:[0,70],highCut:[0,100],captionSize:[16,30],backgroundReduction:[0,60]};
export const toggles = ['compression','notices','dialogueBoost','autoBrightness','captions','easyCaptions','boldCaptions','breakReminder','transitionSoftening'];
export const modes = [
 {id:'gentle',title:'자극을 편안하게',en:'Sensory Sensitive',icon:'moon',color:'#da8c97',desc:'소리와 빛에<br>민감한 날이라면',features:['급격한 음량 변화 완화','배경음 40% 감소 설정','채도와 대비 완화','부드러운 장면 전환 설정'],values:{brightness:75,contrast:80,saturation:65,volume:25,highCut:55,compression:true,backgroundReduction:40,transitionSoftening:true}},
 {id:'focus',title:'이야기에 집중',en:'Focus Support',icon:'play',color:'#c7a150',desc:'이야기의 흐름을<br>따라가고 싶다면',features:['말소리 대역 강조','배경음 중간 감소 설정','장면 기록과 진행 위치','놓친 내용 다시 짚기'],values:{brightness:90,contrast:95,saturation:90,volume:30,compression:true,dialogueBoost:true,backgroundReduction:25}},
 {id:'clarity',title:'조금 더 또렷하게',en:'Clarity Assist',icon:'sun',color:'#65a88f',desc:'또렷하게 듣고<br>크게 보고 싶다면',features:['2–4kHz 말소리 대역 강조','음량 안정화와 대비 강화','어두운 장면 밝기 보정','크고 굵은 자막'],values:{brightness:100,contrast:110,saturation:100,volume:40,compression:true,dialogueBoost:true,autoBrightness:true,captionSize:26,boldCaptions:true}},
 {id:'soft',title:'부드럽게 시작',en:'Soft Discovery',icon:'glasses',color:'#69a7c4',desc:'부드러운 화면과<br>쉬운 말이 필요하다면',features:['부드러운 색감','쉬운 자막으로 내용 확인','작은 음량과 높은 소리 완화','장면 안내와 전환 완화 설정'],values:{brightness:80,contrast:80,saturation:75,volume:22,highCut:45,compression:true,easyCaptions:true,captionSize:24,transitionSoftening:true}},
 {id:'everyday',title:'평소처럼 편안하게',en:'Eye & Ear Ease',icon:'sound',color:'#a28bc1',desc:'평소 화면과 소리를<br>조금씩 맞추고 싶다면',features:['따뜻한 화면 색온도','급격한 소리 변화 완화','시청 중 쉬는 시간 안내','다시 조절하는 나의 기준'],values:{brightness:85,contrast:90,saturation:90,warmth:25,volume:35,highCut:10,compression:true,breakReminder:true}}
];
export function normalize(input={}) {
 const result={...defaults};
 for(const [k,[min,max]] of Object.entries(ranges)) if(Number.isFinite(input[k])) result[k]=Math.min(max,Math.max(min,input[k]));
 for(const k of toggles) if(typeof input[k]==='boolean') result[k]=input[k];
 if(modes.some(m=>m.id===input.profileId)) result.profileId=input.profileId;
 return result;
}
export function modeSettings(id,notices=true){const m=modes.find(m=>m.id===id)||modes[4];return {...defaults,...m.values,profileId:m.id,notices};}
