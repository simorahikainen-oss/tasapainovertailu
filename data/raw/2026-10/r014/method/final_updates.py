import json,glob,sys
sys.path.insert(0,'.')
from parse import parse
h=json.load(open('/workspace/tv-repo/history.json')); s=h['snapshots'][-1]
F={f['n']:f for f in h['funds']}; cur={f['n']:f for f in s['funds']}
bond={u['n']:u for u in json.load(open('bond_updates.json'))}
P={json.load(open(fn))['key']:parse(fn) for fn in glob.glob('raw/*.json')}
U={}
def u(n): return U.setdefault(n,{'n':n})
UB='https://unitedbankers.fi/api/products/file?id=fb876b21-fb92-ec11-bad2-005056ab348e&lang=fi'
u(5)['allocation_primary']={'equity_pct':33.2,'fixed_income_pct':33.5,'other_pct':33.3,'as_of':'2026-10-31','source':'kuukausikatsaus','source_url':UB,
 'note':'UB Smart kuukausiraportti lokakuu 2026 (s. 3 "Kaikkien sijoitusten omaisuusluokkajakauma"): Osakkeet 33,2 %, Korkosijoitukset 33,5 %, Reaaliomaisuus 32,0 %, Käteinen 1,3 % (other_pct = reaaliomaisuus + käteinen). Morningstar 31.10.2026 (osake 15,13 / korko 66,98) poikkeaa >10 %-yks. (reaaliomaisuusrahastot luokittuvat eri tavoin); virallinen raportti tarkistettu ja käytetty. Edellinen 30.9. luku kahdella desimaalilla, nyt yhdellä – pieni muutos osin pyöristystä. Luettu 15.11.2026.'}
u(5)['flags']=[{'type':'source_anomaly','note':'Morningstar 31.10.2026: osake 15,13 / korko 66,98 ristiriidassa UB:n virallisen kuukausiraportin 31.10.2026 (33,2/33,5, reaaliomaisuus 32,0) kanssa; käytetään UB:n raporttia (tarkistettu 15.11.2026).'}]
def ms(n,asof,extra):
    a=P[f'n{n}']['alloc_bond']; g=lambda k,i: (a.get(k) or [None,None,None])[i]
    x=u(n); x['as_of']=asof; x['source_url']=F[n]['ms_url']
    x['morningstar_raw']={'stocks':g('Equity',0),'bonds':g('Fixed Income',0),'cash':g('Cash',0),'other':g('Other',0),'preferred':g('Preferred',0),'convertible':g('Convertible',0)}
    x['long']={'equity':g('Equity',2),'fixed_income':g('Fixed Income',2),'preferred':g('Preferred',2),'convertible':g('Convertible',2),'cash':g('Cash',2),'other':g('Other',2)}
    x['note']=extra
ms(6,'2026-10-31','Morningstar portfolio-sivu (Bond-välilehti Asset Allocation net/long): salkku 31.10.2026 (Holdings as of Oct 31, 2026; Fixed Income Measures ja Exposure Analysis as of Oct 31, 2026). Luettu 15.11.2026.')
ms(12,'2026-09-30','Morningstar portfolio-sivu (Bond-välilehti Asset Allocation net/long): salkku 30.9.2026 (Holdings as of Sep 30, 2026; Measures/Exposure Analysis as of Sep 30, 2026) – uudempi kuin aiempi 31.8., ei vielä 31.10. Danske factsheet (omistusanalyysi per 30.9.2026) kaaviona. Luettu 15.11.2026.')
NF='https://fundsnow.os.fundconnect.com/api/v1/public/printer/solutions/default/dynamic-factsheet?&language=fi-FI&currency=EUR&clientID=FIIF&shelves=FIIF&isin=FI4000400098'
u(17)['allocation_primary']={'equity_pct':53.42,'fixed_income_pct':46.58,'other_pct':0.0,'as_of':'2026-09-30','source':'kuukausikatsaus (factsheet)','source_url':NF,
 'note':'Nordean factsheet (haettu 15.11.2026, "Perustuu rahaston sijoituksiin 30.09.2026"): Osakkeet 53,42 %, Korkosijoitukset 46,58 %, Muut 0,00 %. Uusin virallinen kuukausitieto; Morningstar 30.9.2026 osake 76,14 / korko 26,32 epäuskottava (kuten aiemmin), ei käytetty. Edellinen 30.6. luku puolivuosikatsauksesta (muu 7,88 %) – eri dokumentti, muutos osin luokitteluero. Factsheetin modifioitu duraatio 2,60 ja efektiivinen tuotto 5,11 % (31.10.) EIVÄT ole effective duration / YTW, ei käytetty.'}
u(17)['flags']=[{'type':'source_anomaly','note':'Morningstar 30.9.2026: osake 76,14 / korko 26,32 ristiriidassa Nordean virallisen factsheetin 30.9.2026 (53,42/46,58) kanssa; käytetään Nordean lukua (tarkistettu 15.11.2026).'}]
AK='https://misc.aktia.fi/data-service/documents/investment/Rahastot/Kuukausiraportit/Kuukausiraportti_Aktia_VH50.pdf'
u(22)['allocation_primary']={'equity_pct':51.6,'fixed_income_pct':46.2,'other_pct':2.2,'as_of':'2026-10-31','source':'kuukausikatsaus','source_url':AK,
 'note':'Morningstar ei läpivalaise (98,1 % muut, 30.9.); Aktian kuukausiraportti 31.10.2026 (s. 4 omaisuusluokat): osakesijoitukset 51,6 %, korkosijoitukset 46,2 %, käteinen 2,2 % (raportin mukaan tiedot hakemispäivän tilanteesta, raportin päiväys 31.10.2026). Luettu 15.11.2026.'}
# costs: fund size refresh where Morningstar quote fundSize and surveyedFundSize agree (<1 %) and date newer
skip={5:'fundSize 100 887 105 (12.11.) ja surveyedFundSize 116 956 422 eroavat 14 %; UB:n raportti 115,97 M€ (31.10.) – ei päivitetty',
      8:'fundSize 295 189 090 (31.10.), mutta sivulla rahastokoko "—", osuussarja 276,8 M ja yhtiön AUM 276,1 M€ (31.8.) – ristiriitainen, ei päivitetty'}
cost_log=[]
for fn in sorted(glob.glob('rawq/n*.json')):
    d=json.load(open(fn)); n=int(d['key'][1:]); q=d.get('sal_quote')
    if not q or n in skip: continue
    c=cur[n].get('costs') or {}
    fs,sv,dt=q.get('fundSize'),q.get('surveyedFundSize'),(q.get('fundSizeDate') or '')[:10]
    if not fs or not sv or abs(fs/sv-1)>0.01 or q.get('baseCurrencyId')!='EUR': continue
    if dt<= (c.get('fund_size_as_of') or ''): continue
    p={'fund_size':fs,'fund_size_currency':'EUR','fund_size_as_of':dt,'fund_size_type':'fund','fetched_at':'2026-11-15',
       'source':'Morningstar Global quote 15.11.2026: Fund Size (fundSize/fundSizeDate); juoksevat kulut ennallaan (screener OngoingCharge, haettu aiemmin)',
       'source_url':d['url']}
    if n==18:
        p['ongoing_cost_pct']=round(q['onGoingCharge']*100,2)
        p['source']='Morningstar Global quote 15.11.2026: Fund Size (fundSize/fundSizeDate) ja Ongoing Costs (onGoingCharge, pvm '+(q.get('onGoingChargeDate') or '')[:10]+'); screener OngoingCharge puuttui'
        p['note']='Juoksevat kulut Morningstar Global -sivun Ongoing Costs (aiemmin puuttui); rahastokoko päivitetty (aiempi 31.12.2025).'
    u(n)['costs']=p; cost_log.append((n,c.get('fund_size'),c.get('fund_size_as_of'),fs,dt,p.get('ongoing_cost_pct')))
for n,b in bond.items(): u(n)['bond_metrics']=b['bond_metrics']
out=[U[k] for k in sorted(U,key=lambda z:(isinstance(z,str),z if not isinstance(z,str) else 0))]
# VAGF last
json.dump(out,open('updates_r014.json','w'),ensure_ascii=False,indent=1)
for c in cost_log: print('cost',c)
print(len(out),[x['n'] for x in out])
for k in (6,12): print(k,U[k]['morningstar_raw'],U[k]['long'])
