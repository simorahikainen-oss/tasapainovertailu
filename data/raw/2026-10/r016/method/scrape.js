// Reads Morningstar Global (en-nd) public portfolio + quote pages with headless Chrome (no sign-in).
const puppeteer=require('puppeteer-core');const fs=require('fs');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const targets=JSON.parse(fs.readFileSync(process.env.TARGETS||'targets.json'));
async function readExposure(p,metric){
  return p.evaluate(async(metric)=>{
    const sl=ms=>new Promise(r=>setTimeout(r,ms));
    const h=[...document.querySelectorAll('h1,h2,h3,h4,span,div')].find(e=>e.children.length==0 && e.innerText.trim()==='Fixed Income Exposure Analysis');
    if(!h) return {error:'no FIEA heading'};
    let s=h; for(let i=0;i<8;i++){ s=s.parentElement; if(s.querySelectorAll('button[aria-label]').length) break;}
    const comp=s.parentElement;
    const btn=[...s.querySelectorAll('button')].find(x=>x.innerText.trim()===metric); if(!btn) return {error:'no metric button'};
    btn.click(); await sl(2000);
    // ensure rows = Credit Rating (first 'Credit Rating' button in second group is default)
    if(!comp.querySelector('table')){ const tb=[...s.querySelectorAll('button')].find(x=>/Table/.test(x.getAttribute('aria-label')||'')); if(tb){tb.click(); await sl(2500);} }
    // go to page 1
    for(let k=0;k<5;k++){const pv=[...comp.querySelectorAll('button')].find(x=>x.getAttribute('aria-label')==='Prev'); if(pv&&!pv.disabled){pv.click(); await sl(1200);} else break;}
    const pages=[];
    for(let k=0;k<6;k++){
      const t=comp.querySelector('table'); if(!t){pages.push({error:'no table'});break;}
      pages.push([...t.rows].map(r=>[...r.cells].map(c=>c.innerText.trim())));
      const nx=[...comp.querySelectorAll('button')].find(x=>x.getAttribute('aria-label')==='Next');
      if(nx&&!nx.disabled){nx.click(); await sl(1500);} else break;
    }
    const foot=(comp.innerText.match(/As of[^\n]*/g)||[]);
    const pageInfo=(comp.innerText.match(/of \d+/g)||[]);
    const active=[...s.querySelectorAll('button')].filter(x=>/active/.test(x.className)).map(x=>x.innerText.trim());
    return {metric,active,pages,footnotes:foot,pageInfo,text:comp.innerText};
  },metric);
}
(async()=>{
const b=await puppeteer.connect({browserURL:'http://localhost:9333',defaultViewport:{width:1440,height:1100}});
for(const tg of targets){
  const out={key:tg.key,isin:tg.isin,portfolio_url:tg.url,quote_url:tg.url.replace('/portfolio','/quote'),read_at:new Date().toISOString()};
  const fn=`raw/${tg.key}.json`;
  if(fs.existsSync(fn) && !process.env.FORCE){console.log('skip',tg.key);continue;}
  const p=await b.newPage();
  try{
    await p.goto(tg.url,{waitUntil:'networkidle2',timeout:90000}); await sleep(2500);
    out.title=await p.title();
    out.equity_tab_text=await p.evaluate(()=>document.body.innerText);
    const ok=await p.evaluate(()=>{const e=[...document.querySelectorAll('button')].find(x=>x.innerText.trim()==='Bond'); if(e){e.click();return true}return false});
    out.bond_tab_clicked=ok; await sleep(4000);
    out.bond_tab_text=await p.evaluate(()=>document.body.innerText);
    out.economic_exposure_toggle=await p.evaluate(()=>/Economic Exposure/i.test(document.body.innerText));
    out.exposure={ed:await readExposure(p,'Effective Duration'), ytw:await readExposure(p,'Yield To Worst')};
    await p.goto(out.quote_url,{waitUntil:'networkidle2',timeout:90000}); await sleep(2000);
    out.quote_title=await p.title();
    out.quote_text=await p.evaluate(()=>document.body.innerText);
  }catch(e){out.error=String(e);}
  await p.close();
  fs.writeFileSync(fn,JSON.stringify(out,null,1));
  console.log(tg.key,out.title,out.error||'',out.exposure&&out.exposure.ed.pages&&out.exposure.ed.pages.length, out.exposure&&out.exposure.ytw.pages&&out.exposure.ytw.pages.length);
  await sleep(3000);
}
b.disconnect();
})();
