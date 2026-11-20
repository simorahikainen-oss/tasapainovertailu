const puppeteer=require('puppeteer-core');const fs=require('fs');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const targets=JSON.parse(fs.readFileSync('targets.json'));
(async()=>{
const b=await puppeteer.connect({browserURL:'http://localhost:9333',defaultViewport:{width:1440,height:1100}});
let first=true;
for(const tg of targets){
  const fn=`rawq/${tg.key}.json`; if(fs.existsSync(fn)&&!process.env.FORCE) continue;
  const url=tg.url.replace('/portfolio','/quote'); const out={key:tg.key,isin:tg.isin,url,read_at:new Date().toISOString(),sal_quote:null};
  const p=await b.newPage();
  p.on('response',async r=>{const u=r.url(); if(/sal-service\/v1\/(fund|etf)\/quote\/v\d+\//.test(u)){try{out.sal_quote=await r.json(); out.sal_quote_endpoint=u.split('?')[0];}catch(e){}}});
  try{
    await p.goto(url,{waitUntil:'networkidle2',timeout:90000}); await sleep(2500);
    await p.evaluate(()=>{const e=[...document.querySelectorAll('button,a')].find(x=>/Individual Investor/.test(x.innerText)); if(e) e.click();}); await sleep(5000);
    out.title=await p.title(); out.text=await p.evaluate(()=>document.body.innerText);
  }catch(e){out.error=String(e)}
  await p.close(); fs.writeFileSync(fn,JSON.stringify(out,null,1));
  const m=(out.text||'').match(/Fund Size[^\n]*\n+([^\n]*)/); const oc=(out.text||'').match(/Ongoing Costs\n+([^\n]*)/);
  console.log(tg.key,out.title,m&&m[1],oc&&oc[1],!!out.sal_quote,out.error||'');
  await sleep(2500);
}
b.disconnect();})();
