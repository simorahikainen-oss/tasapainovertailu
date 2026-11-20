import json,glob,sys
sys.path.insert(0,'.')
from parse import parse,d
h=json.load(open('/workspace/tv-repo/history.json')); s=h['snapshots'][-1]
cur={f['n']:f for f in s['funds']}; cur['VAGF']={'bond_metrics':s['benchmark'].get('VAGF_bond_metrics')}
batch=[]; report=[]
for fn in sorted(glob.glob('raw/*.json')):
    o=parse(fn); k=o['key']
    if k=='SPYI': continue
    n='VAGF' if k=='VAGF' else int(k[1:])
    m=o['measures']['rows']; foot=o['measures']['footnote']
    def mv(lbl):
        v=(m.get(lbl) or {}).get('investment')
        return None if v in (None,'–','—','') else float(v)
    dm={'effective_duration':mv('Effective Duration'),'yield_to_worst':mv('Yield to Worst'),
        'modified_duration':mv('Modified Duration'),'yield_to_maturity':mv('Yield to Maturity'),
        'weighted_coupon':mv('Weighted Coupon'),'weighted_price':mv('Weighted Price'),
        'label':'Fixed Income Measures Investment column; '+repr(foot)+('' if 'Yield to Worst' in m else ' No Yield to Worst row.'),
        'as_of_label':foot}
    (p1,p2)=o['ed']['p']; (y1,y2)=o['ytw']['p']
    assert o['ed']['foot']==o['ytw']['foot'] or True
    x={'n':k if k=='VAGF' else k,'isin':o['isin'] if k!='VAGF' else None,'url':o['url'],'title_verified':True,'page_title':o['title'],
       'table_footnote':o['ed']['foot'],'ytw_table_footnote':o['ytw']['foot'],
       'direct_measures':dm,'duration_p1':p1,'duration_p2':p2,'ytw_p1':y1,'ytw_p2':y2,
       'allocation_table_bond_tab':o['alloc_bond'],'allocation_header':o['alloc_header'],'holdings_as_of':o['holdings_as_of'],
       'economic_exposure_toggle':o['economic_exposure_toggle'],'bond_sectors':o['sectors']}
    # compare with stored
    b=(cur[n].get('bond_metrics') or {})
    et=b.get('exposure_tables') or {}
    def vals(p1,p2):
        num=lambda v: None if v in ('–','-','') else float(v)
        return [[num(v) for v in a[1:]]+[num(v) for v in bb[1:-1]] for a,bb in zip(p1['rows'],p2['rows'])]
    same_ed=et.get('effective_duration',{}).get('values')==vals(p1,p2) and et.get('effective_duration',{}).get('as_of')==d(o['ed']['foot'])
    same_y=et.get('yield_to_worst',{}).get('values')==vals(y1,y2) and et.get('yield_to_worst',{}).get('as_of')==d(o['ytw']['foot'])
    old_ed=(b.get('effective_duration_years') or {}); old_y=(b.get('yield_to_worst_pct') or {})
    same_dm=(old_ed.get('value')==dm['effective_duration']) and (old_y.get('value')==dm['yield_to_worst'])
    report.append((n,'tables_same' if same_ed and same_y else f"TABLES CHANGED ed:{et.get('effective_duration',{}).get('as_of')}->{d(o['ed']['foot'])} same={same_ed} ytw same={same_y}",
                   'dm_same' if same_dm else f"DM CHANGED ED {old_ed.get('value')}({old_ed.get('as_of')},{old_ed.get('check_status')})->{dm['effective_duration']} ({d(foot)}) YTW {old_y.get('value')}->{dm['yield_to_worst']}",
                   b.get('checked_at')))
    x['_same']={'ed':same_ed,'ytw':same_y,'dm':same_dm}
    batch.append(x)
json.dump({'read_at':'2026-11-20','method':'read via headless Chrome (public Morningstar Global en-nd portfolio page, Bond tab, Fixed Income Exposure Analysis table view toggle, all pages via Next); values from DOM text, no transcription','batch':'r016 20th-of-month check 20.11.2026','funds':batch},open('bond_tables_batch10_all.json','w'),ensure_ascii=False,indent=1)
for r in report: print(r)
