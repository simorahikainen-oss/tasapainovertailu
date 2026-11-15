import json,copy,sys
sys.path.insert(0,'/workspace/tv-repo/scripts')
import import_bond_tables as IB
h=json.load(open('/workspace/tv-repo/history.json')); s=h['snapshots'][-1]
cur={f['n']:f for f in s['funds']}
B=json.load(open('bond_tables_batch9_all.json'))
METHOD=B['method']
ups=[]; log=[]
for x in B['funds']:
    k=x['n']; n='VAGF' if k=='VAGF' else int(k[1:])
    old=copy.deepcopy(s['benchmark']['VAGF_bond_metrics'] if n=='VAGF' else cur[n]['bond_metrics'])
    dm=x['direct_measures']; foot=dm['as_of_label']; fdate=IB.date_from(foot)
    old_tab_date=(old.get('exposure_tables') or {}).get('effective_duration',{}).get('as_of')
    new=old
    new['checked_at']='2026-11-15'; new['direct_measures_captured']=True
    new['as_of_label']=dm['label']
    for key,lbl,dk in (('effective_duration_years','Effective Duration','effective_duration'),('yield_to_worst_pct','Yield to Worst','yield_to_worst')):
        v=dm[dk]; o=old.get(key) or {}
        if v is not None:
            asof=fdate
            new[key]={'value':v,'as_of':asof,'label':lbl,'check_status':'reported'}
        else:
            new[key]={'value':None,'as_of':None,'label':lbl,'check_status':'checked_absent'}
        if o.get('value')!=new[key]['value'] or (o.get('value') is not None and o.get('as_of')!=new[key]['as_of']):
            log.append(f"{k} {key}: {o.get('value')} ({o.get('as_of')}, {o.get('check_status')}) -> {new[key]['value']} ({new[key]['as_of']})")
    new['other_measures_not_used']={kk:dm[kk] for kk in ('yield_to_maturity','modified_duration','weighted_coupon','weighted_price')}
    chg=[]
    if not (x['_same']['ed'] and x['_same']['ytw']):
        new['exposure_tables']={'effective_duration':IB.table(x,'duration','effective_duration',METHOD),
                                'yield_to_worst':IB.table(dict(x,table_footnote=x['ytw_table_footnote']),'ytw','yield_to_worst',METHOD)}
        chg.append(f"Fixed Income Exposure Analysis -taulukot päivittyivät ({old_tab_date} → {IB.date_from(x['table_footnote'])})")
        log.append(f"{k} tables {old_tab_date} -> {IB.date_from(x['table_footnote'])}")
    else:
        chg.append('taulukot ennallaan (sama as_of ja arvot)')
    if old.get('exposure_tables'):
        for t in new['exposure_tables'].values(): t.setdefault('last_verified','2026-11-15')
    meas_note=('Fixed Income Measures -taulukko näkyy (Investment-sarake: Effective Duration '+(str(dm['effective_duration']) if dm['effective_duration'] is not None else '–')+
               ', Yield to Worst -riviä '+('on' if dm['yield_to_worst'] is not None else 'ei')+'; '+foot+')')
    add=f"15.11.2026 täyskuukausiajo: tarkistettu uudelleen headless Chromella (julkinen sivu, Bond-välilehti, taulukkonäkymä, kaikki sivut); {meas_note}; {'; '.join(chg)}."
    new['note']=((old.get('note') or '').strip()+' | '+add).strip(' |')
    ups.append({'n':n,'bond_metrics':new})
json.dump(ups,open('bond_updates.json','w'),ensure_ascii=False,indent=1)
print('\n'.join(log))
