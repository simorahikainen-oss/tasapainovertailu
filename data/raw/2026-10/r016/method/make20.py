import json,copy,sys,glob
sys.path.insert(0,'/workspace/tv-repo/scripts'); sys.path.insert(0,'.')
import import_bond_tables as IB
from parse import parse
D='2026-11-20'
h=json.load(open('/workspace/tv-repo/history.json')); s=h['snapshots'][-1]
F={f['n']:f for f in h['funds']}; cur={f['n']:f for f in s['funds']}
B=json.load(open('bond_tables_batch10_all.json')); METHOD=B['method']
U={}; log=[]
def u(n): return U.setdefault(n,{'n':n})
for x in B['funds']:
    k=x['n']; n='VAGF' if k=='VAGF' else int(k[1:])
    old=copy.deepcopy(s['benchmark']['VAGF_bond_metrics'] if n=='VAGF' else cur[n]['bond_metrics'])
    new=old; dm=x['direct_measures']; foot=dm['as_of_label']; fdate=IB.date_from(foot)
    old_tab_date=(old.get('exposure_tables') or {}).get('effective_duration',{}).get('as_of')
    new['checked_at']=D; new['direct_measures_captured']=True; new['as_of_label']=dm['label']
    for key,lbl,dk in (('effective_duration_years','Effective Duration','effective_duration'),('yield_to_worst_pct','Yield to Worst','yield_to_worst')):
        v=dm[dk]; o=old.get(key) or {}
        if v is not None:
            if o.get('value')==v and o.get('as_of')==fdate: new[key]=o  # ennallaan: alkuperäinen havainto säilyy
            else: new[key]={'value':v,'as_of':fdate,'label':lbl,'check_status':'reported'}
        else:
            new[key]={'value':None,'as_of':None,'label':lbl,'check_status':'checked_absent'}
        if o.get('value')!=new[key]['value'] or (o.get('value') is not None and o.get('as_of')!=new[key]['as_of']):
            log.append(f"{k} {key}: {o.get('value')} ({o.get('as_of')}, {o.get('check_status')}) -> {new[key]['value']} ({new[key]['as_of']})")
    omn={kk:dm[kk] for kk in ('yield_to_maturity','modified_duration','weighted_coupon','weighted_price')}
    new['other_measures_not_used']=omn
    chg=[]
    if not (x['_same']['ed'] and x['_same']['ytw']):
        nd=IB.date_from(x['table_footnote'])
        old_et=old.get('exposure_tables') or {}
        new['exposure_tables']={'effective_duration':IB.table(x,'duration','effective_duration',METHOD),
                                'yield_to_worst':IB.table(dict(x,table_footnote=x['ytw_table_footnote']),'ytw','yield_to_worst',METHOD)}
        for t in new['exposure_tables'].values(): t['last_verified']=D
        if nd==old_tab_date:
            new['exposure_tables_superseded']={'replaced_at':D,'reason':'Morningstar päivitti saman päivän ('+nd+') taulukon soluarvoja; aiempi luenta säilyy revisioarkistossa (r015).',
                                               'previous_values':{kk:{'as_of':vv.get('as_of'),'values':vv.get('values'),'subtotal_weight':vv.get('subtotal_weight')} for kk,vv in old_et.items()}}
            chg.append(f"Fixed Income Exposure Analysis -taulukot: Morningstar korjasi saman päivän ({nd}) solujen arvoja; uusi luenta tallennettu, aiempi säilytetty")
        else:
            new.pop('exposure_tables_superseded',None)
            chg.append(f"Fixed Income Exposure Analysis -taulukot päivittyivät ({old_tab_date} → {nd})")
        log.append(f"{k} tables {old_tab_date} -> {nd}")
    else:
        chg.append('taulukot ennallaan (sama as_of ja arvot)')
        for t in (new.get('exposure_tables') or {}).values(): t['last_verified']=D
    meas_note=('Fixed Income Measures -taulukko näkyy (Investment-sarake: Effective Duration '+(str(dm['effective_duration']) if dm['effective_duration'] is not None else '–')+
               ', Yield to Worst -riviä '+('on' if dm['yield_to_worst'] is not None else 'ei')+'; '+foot+')')
    add=f"20.11.2026 kuun 20. päivän tarkistus: luettu uudelleen headless Chromella (julkinen sivu, Bond-välilehti, taulukkonäkymä, kaikki sivut); {meas_note}; {'; '.join(chg)}."
    new['note']=((old.get('note') or '').strip()+' | '+add).strip(' |')
    u(n)['bond_metrics']=new
# n19 allocation: Morningstar 31.10.2026 (uudempi kuin aiempi MS 30.9.)
P={json.load(open(fn))['key']:parse(fn) for fn in glob.glob('raw/*.json')}
def ms(n,asof,extra):
    a=P[f'n{n}']['alloc_bond']; g=lambda k,i: (a.get(k) or [None,None,None])[i]
    x=u(n); x['as_of']=asof; x['source_url']=F[n]['ms_url']
    x['morningstar_raw']={'stocks':g('Equity',0),'bonds':g('Fixed Income',0),'cash':g('Cash',0),'other':g('Other',0),'preferred':g('Preferred',0),'convertible':g('Convertible',0)}
    x['long']={'equity':g('Equity',2),'fixed_income':g('Fixed Income',2),'preferred':g('Preferred',2),'convertible':g('Convertible',2),'cash':g('Cash',2),'other':g('Other',2)}
    x['note']=extra
assert P['n19']['holdings_as_of']=='2026-10-31'
ms(19,'2026-10-31','Morningstar portfolio-sivu (Bond-välilehti Asset Allocation net/long): salkku 31.10.2026 (Holdings as of Oct 31, 2026; Fixed Income Measures ja Exposure Analysis as of Oct 31, 2026). Uudempi kuin aiempi MS 30.9. Obsidon virallinen fact sheet 30.9.2026 (julkaistu 11/2026): osakkeet 52,9 %, korot 32,4 % (lyhyt 3,8 + pitkä 5,0 + IG 12,0 + HY 8,1 + kehittyvät 3,5), muut 14,7 % – vanhempi kuin MS 31.10., ero MS 30.9. lukuun alle 10 %-yks.; 31.10. fact sheetia ei vielä löytynyt. Luettu 20.11.2026.')
# costs: fund size refresh (sama sääntö kuin r014)
skip={5:'fundSize ja surveyedFundSize eroavat >1 %',8:'rahastokoko ristiriitainen (r014)',20:'surveyedFundSize 1 597,6 ei vastaa fundSize-arvoa'}
cost_log=[]
for fn in sorted(glob.glob('rawq/n*.json')):
    d=json.load(open(fn)); n=int(d['key'][1:]); q=d.get('sal_quote')
    if not q or n in skip: continue
    c=cur[n].get('costs') or {}
    fs,sv,dt=q.get('fundSize'),q.get('surveyedFundSize'),(q.get('fundSizeDate') or '')[:10]
    if not fs or not sv or abs(fs/sv-1)>0.01 or q.get('baseCurrencyId')!='EUR': continue
    if dt<=(c.get('fund_size_as_of') or ''): continue
    p={'fund_size':fs,'fund_size_currency':'EUR','fund_size_as_of':dt,'fund_size_type':'fund','fetched_at':D,
       'source':'Morningstar Global quote 20.11.2026: Fund Size (fundSize/fundSizeDate); juoksevat kulut ennallaan (screener OngoingCharge, haettu aiemmin)','source_url':d['url']}
    u(n)['costs']=p; cost_log.append((n,c.get('fund_size'),c.get('fund_size_as_of'),fs,dt))
out=[U[k] for k in sorted(U,key=lambda z:(isinstance(z,str),z if not isinstance(z,str) else 0))]
json.dump(out,open('updates_r016.json','w'),ensure_ascii=False,indent=1)
print('\n'.join(log))
for c in cost_log: print('cost',c)
print(len(out))
