import json,re,sys,glob,datetime as dt
MON={m:i for i,m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],1)}
def d(s):
    m=re.search(r'(\w{3}) (\d{1,2}), (\d{4})',s or '');
    return dt.date(int(m.group(3)),MON[m.group(1)],int(m.group(2))).isoformat() if m else None
def num(v):
    v=v.strip().replace(',','')
    return None if v in ('–','—','-','') else float(v)
def alloc(txt):
    i=txt.find('Asset Allocation\n'); seg=txt[i:i+800]
    out={}
    for k in ('Equity','Fixed Income','Preferred','Convertible','Cash','Other'):
        m=re.search(r'\n ?'+k+r'\t([^\t\n]+)\t([^\t\n]+)\t([^\t\n]+)',seg)
        if m: out[k]=[num(m.group(1)),num(m.group(2)),num(m.group(3))]
    hdr=re.search(r'Asset Class\t([^\n]*)',seg)
    return out,(hdr.group(1) if hdr else None)
def measures(txt):
    i=txt.find('Fixed Income Measures'); 
    if i<0: return None
    seg=txt[i:i+1500]; j=seg.find('As of'); 
    end=seg.find('\n',j) if j>=0 else len(seg)
    body=seg[:end]
    rows={}
    for m in re.finditer(r'\n([A-Za-z][A-Za-z ()\-]+?)\t([^\t\n]*)\t([^\t\n]*)',body):
        rows[m.group(1).strip()]={'investment':m.group(2).strip(),'category':m.group(3).strip()}
    foot=seg[j:end] if j>=0 else None
    hdr=re.search(r'Fixed Income Measures\n(.*?)\n\n',seg,re.S)
    return {'rows':rows,'footnote':foot,'header_block':seg[:seg.find('\n',seg.find('Effective'))] if 'Effective' in seg else seg[:200]}
def sectors(txt):
    i=txt.find('Sectors\tInvestment%'); 
    if i<0: return None
    seg=txt[i:i+600]; out={}
    for k in ('Government','Municipal','Corporate','Securitized','Cash & Equivalents','Derivative'):
        m=re.search(re.escape(k)+r'\t([^\t\n]+)\t([^\t\n]+)',seg)
        if m: out[k]={'investment':num(m.group(1)),'category':num(m.group(2))}
    return out
def holdings_date(txt):
    m=re.search(r'Holdings as of\s+(\w{3} \d{1,2}, \d{4})',txt); return d(m.group(1)) if m else None
def exposure(e):
    if not e or e.get('error') or not e.get('pages'): return None, (e or {}).get('error','missing')
    pg=e['pages']
    if len(pg)!=2 or any(isinstance(x,dict) for x in pg): return None,f'pages={len(pg)}'
    p1={'header':[c.replace('\n',' ') for c in pg[0][0]],'rows':pg[0][1:]}
    p2={'header':[c.replace('\n',' ') for c in pg[1][0]],'rows':pg[1][1:]}
    return (p1,p2),None
def parse(fn):
    r=json.load(open(fn)); o={'key':r['key'],'isin':r['isin'],'url':r['portfolio_url'],'title':r.get('title'),'read_at':r['read_at'],'error':r.get('error')}
    if r.get('error'): return o
    bt=r['bond_tab_text']
    o['alloc_bond'],o['alloc_header']=alloc(bt)
    o['alloc_equity_tab'],_=alloc(r['equity_tab_text'])
    o['measures']=measures(bt)
    o['sectors']=sectors(bt)
    o['holdings_as_of']=holdings_date(bt) or holdings_date(r['equity_tab_text'])
    o['economic_exposure_toggle']=r.get('economic_exposure_toggle')
    for k in ('ed','ytw'):
        e=r['exposure'][k]; t,err=exposure(e)
        o[k]={'p':t,'err':err,'foot':(e.get('footnotes') or [None])[0] if e else None,'active':e.get('active') if e else None,'pageInfo':e.get('pageInfo') if e else None}
    return o
if __name__=='__main__':
    for fn in sorted(glob.glob('raw/*.json')):
        o=parse(fn)
        if o.get('error'): print(o['key'],'ERR',o['error']); continue
        m=o['measures'] or {}
        print(o['key'],o['title'][:40],'| alloc',{k:v[0] for k,v in o['alloc_bond'].items()},'| hold',o['holdings_as_of'],'| meas',{k:v['investment'] for k,v in (m.get('rows') or {}).items() if k in('Effective Duration','Yield to Worst','Yield to Maturity','Modified Duration')},(m.get('footnote') or '')[:60],'| ED',o['ed']['err'],d(o['ed']['foot']),o['ed']['active'],'| YTW',o['ytw']['err'],d(o['ytw']['foot']),o['ytw']['active'],'| EE',o['economic_exposure_toggle'])
