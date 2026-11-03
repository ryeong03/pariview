import re
from playwright.sync_api import sync_playwright
p='/Users/ryeong/Desktop/pariview/poster/PariView_A1.html'
SEL=['header','#s1','#s2','#s3','#s4','#s5']
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    pg=b.new_page(viewport={'width':2245,'height':3179});pg.goto('http://127.0.0.1:4195/poster/PariView_A1.html');pg.wait_for_function("document.body.dataset.layoutErrors!==undefined",timeout=60000)
    pg.add_style_tag(content='header,#s1,#s2,#s3,#s4,#s5{height:auto!important;overflow:visible!important}.poster{height:auto!important}');pg.wait_for_timeout(300)
    m=pg.evaluate("""(sels)=>{const mm=v=>Math.round(v/3.7795*10)/10;const o={};for(const s of sels){const e=document.querySelector(s);o[s]=e?mm(e.getBoundingClientRect().height):0}return o}""",SEL);b.close()
need={k:round(v+1,1) for k,v in m.items() if v>0}
gaps=len(need)+1; avail=841-18-16-20-gaps*4.6-10.5; total=sum(need.values())
print('need',need,'sum',round(total,1),'avail',round(avail,1),'spare',round(avail-total,1))
s=open(p,encoding='utf-8').read()
if total<=avail:
    need['#s2']=round(need['#s2']+(avail-total),1)
    s=re.sub(r'header \{ height: [\d.]+mm;',f"header {{ height: {need['header']}mm;",s)
    for k in [k for k in need if k!='header']:
        if re.search(re.escape(k)+r' \{ height: [\d.]+mm; \}',s): s=re.sub(re.escape(k)+r' \{ height: [\d.]+mm; \}',f"{k} {{ height: {need[k]}mm; }}",s)
        else: s=s.replace('</style>',f"  {k} {{ height: {need[k]}mm; }}\n</style>",1)
    open(p,'w',encoding='utf-8').write(s); print('heights set',need)
else: print('OVER by',round(total-avail,1))
