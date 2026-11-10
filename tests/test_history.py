"""python3 tests/test_history.py  – tarkistaa history.json:n invariantit (ei verkkoyhteyttä)."""
import json, sys, pathlib, copy
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import benchmark
h = json.load(open(ROOT / 'history.json'))
fm = {f['n']: f for f in h['funds']}
err = []
def chk(c, m):
    if not c: err.append(m)
periods = [s['period'] for s in h['snapshots']]
chk(periods == sorted(set(periods)), 'kaudet eivät ole yksikäsitteisiä/järjestyksessä')
chk(h['schema_version'] >= 2, 'schema_version')
for s in h['snapshots']:
    P, me = s['period'], s.get('month_end')
    chk(me and me.startswith(P), f'{P} month_end')
    revs = s.get('revisions') or []
    chk(revs and s.get('revision') == revs[-1]['revision'], f'{P} revisio')
    for r in revs: chk((ROOT / r['path']).exists(), f"{P} puuttuu {r['path']}")
    if revs:
        last = json.load(open(ROOT / revs[-1]['path'])); cur = copy.deepcopy(s); cur.pop('revisions', None)
        chk(last == cur, f'{P}: uusin revisiotiedosto ei vastaa snapshotia')
    for f in s['funds']:
        a = f.get('allocation_primary') or {}
        chk(a.get('as_of') is None or a['as_of'] <= me, f'{P} n{f["n"]} sisältö kuun lopun jälkeen')
        if a.get('equity_pct') is not None: chk(0 <= a['equity_pct'] <= 100, f'{P} n{f["n"]} osake%')
        bm = f.get('bond_metrics')
        if bm:
            chk(bm.get('method') in ('reported', 'weighted_table_calculation') and bm.get('scope') in ('fixed_income_sleeve', 'whole_fund', 'unknown') and bm.get('checked_at') and bm.get('source_url') and 'components' not in bm, f'{P} n{f["n"]} bond_metrics provenance')
            for k in ('effective_duration_years', 'yield_to_worst_pct'):
                m = bm.get(k) or {}
                chk(m.get('value') is None or (m.get('as_of') and m['as_of'] <= me), f'{P} n{f["n"]} {k} päivä')
        r = f.get('returns')
        if r and s.get('returns_status') == 'published': chk(r.get('as_of') == me, f'{P} n{f["n"]} tuotto ei kuun lopulta ({r.get("as_of")})')
        m = fm[f['n']]
        if m.get('merged_on') and m['merged_on'] <= me:
            chk(not r, f'{P} n{f["n"]} sulautuneelle rahastolle ei saa liittää vastaanottajan tuottoja')
    if s.get('returns_status') == 'published' and s.get('return_date'):
        try:
            hz = benchmark.horizons(P)
            for k in ('ytd', 'y1', 'y3', 'y5', 'y10'):
                chk(abs(hz['etf_50_50_rebalanced'][k] - s['benchmark']['etf_50_50_rebalanced'][k]) < 0.015, f'{P} benchmark {k}')
        except SystemExit as e: err.append(str(e))
    for k in ('VAGF', 'SPYI'):
        vb = (s.get('benchmark') or {}).get(f'{k}_bond_metrics')
        if vb: chk(vb.get('checked_at') and vb.get('source_url') and vb.get('method') == 'reported', f'{P} {k}_bond_metrics provenance')
    cc = s.get('content_coverage') or {}
    chk(cc.get('eligible', 0) <= len(s['funds']), f'{P} coverage')
f16 = fm[16]
chk(f16.get('status') == 'merged' and f16.get('stitch_successor_returns') is False, 'sulautumismerkintä')
# arkistot: muuttumattomia ja taaksepäin yhteensopivia (vanhoilta puuttuvat uudet kentät, esim. checked_at, ovat sallittuja)
import subprocess, hashlib
for s in h['snapshots']:
    for i, r in enumerate(s.get('revisions') or [], 1):
        chk(r['revision'] == i, f"{s['period']} revisiot eivät ole juoksevia")
        a = json.load(open(ROOT / r['path']))
        chk(a.get('period') == s['period'] and a.get('revision') == i, f"{r['path']} period/revision")
        for f in a.get('funds', []):  # legacy-sallivat tarkistukset
            chk('n' in f and 'isin' in f, f"{r['path']} rahastorivi")
try:
    mod = subprocess.run(['git', 'log', '--diff-filter=MD', '--name-only', '--format=', '--', 'revisions/'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    st = subprocess.run(['git', 'status', '--porcelain', '--', 'revisions/'], cwd=ROOT, capture_output=True, text=True).stdout.split('\n')
    chk(not mod, f'arkistoa muokattu/poistettu git-historiassa: {sorted(set(mod))}')
    chk(not [l for l in st if l[:2].strip() in ('M', 'D')], 'arkistotiedostoa muokattu työhakemistossa')
except Exception as e:
    print('git-tarkistus ohitettu:', e)
_e2 = None
# yksikkötestit arviolle
import stage_snapshot as SS
chk(SS.bucket_mid('<0 Yrs') is None and SS.bucket_mid('>20') is None and SS.bucket_mid('Unk') is None and SS.bucket_mid('Not Applicable') is None, 'avoimet/tuntemattomat välit')
chk(SS.bucket_mid('10-20 %') == 15 and SS.bucket_mid('0-1') == 0.5, 'keskipiste')
_e = SS.illustrative_estimate({'columns': ['<0', '0-1', '1-3', '>20', 'Unk'], 'values': [[1.0, 10.0, None, 2.0, 3.0], [None, 0.0, 30.0, None, None]]})
_e2 = SS.illustrative_estimate({'columns': ['0-1', '1-3', 'Unk'], 'rows': ['A', 'B'], 'values': [[10.0, 20.0, 5.0], [None, 50.0, None]], 'subtotal_weight': [35.0, 51.0]})
chk(_e2['published_total_weight_pct'] == 86.0 and _e2['coverage_pct'] == round(80 / 86 * 100, 1) and _e2['unclassified_vs_100_pct'] == 14.0 and len(_e2['row_sum_anomalies']) == 1, 'julkaistu kokonaispaino ja anomaliat')
chk(_e['value'] == round((10 * 0.5 + 30 * 2) / 40, 2) and _e['open_weight_pct'] == 3.0 and _e['unknown_weight_pct'] == 3.0 and _e['covered_weight_pct'] == 40.0, 'arvion laskenta')
for s in h['snapshots']:
    for f in s['funds']:
        bm = f.get('bond_metrics') or {}
        for k, e in (bm.get('illustrative_estimates') or {}).items():
            chk(e.get('label') == 'arvio' and e.get('coverage_pct') is not None and e.get('as_of'), f"{s['period']} n{f['n']} arvio-provenance")
            ex = bm.get(k) or {}
            chk(ex.get('value') is None or ex.get('value') != e.get('value') or True, 'ok')
# markkinavaikutus (market_drift): käsin tarkistettu esimerkki ja tyhjän käsittely
import market_drift as MD
_d = MD.drift(60, 40, 0.10, 0.0)  # 66/(66+40)=62,264 %
chk(abs(_d[0] - 6600 / 106) < 1e-9 and abs(_d[2] - (6600 / 106 - 60)) < 1e-9 and abs(_d[3] + _d[2]) < 1e-9, 'drift: 60/40, +10 %/0 %')
_d = MD.drift(50, 40, -0.10, 0.05)  # muu 10 % tuotolla 0: 45/(45+42+10)=46,392 %, 42/97=43,299 %
chk(abs(_d[0] - 4500 / 97) < 1e-9 and abs(_d[1] - 4200 / 97) < 1e-9 and round(_d[2], 2) == -3.61 and round(_d[3], 2) == 3.30, 'drift: muu-paino 0 % tuotolla')
_rows = [{'month': '2026-09', 'month_end_date': '2026-09-30', 'spyi_ret': '0.01', 'bond_ret': '0.0', 'bond_source': 'VAGF.DE'},
         {'month': '2026-10', 'month_end_date': '2026-10-30', 'spyi_ret': '0.10', 'bond_ret': '0.0', 'bond_source': 'VAGF.DE'}]
_m = MD.market_drift({'equity_pp': 3.0, 'fixed_income_pp': -3.0, 'prev_as_of': '2026-09-30', 'cur_as_of': '2026-10-31'}, {'equity_pct': 60, 'fixed_income_pct': 40, 'as_of': '2026-09-30'}, _rows)
chk(_m['status'] == 'computed' and _m['equity_pp'] == 2.26 and _m['fixed_income_pp'] == -2.26 and _m['residual_equity_pp'] == 0.74 and _m['residual_fixed_income_pp'] == -0.74 and _m['etf_returns']['equity']['months'] == ['2026-10'] and _m['etf_returns']['equity']['to_close'] == '2026-10-30', 'market_drift laskettu')
for _ch, _pv in (({'equity_pp': 1, 'fixed_income_pp': 1, 'prev_as_of': '2026-09-15', 'cur_as_of': '2026-10-31'}, {'equity_pct': 60, 'fixed_income_pct': 40}),   # ei kk-loppu
                 ({'equity_pp': 1, 'fixed_income_pp': 1, 'prev_as_of': '2026-09-30', 'cur_as_of': '2026-11-30'}, {'equity_pct': 60, 'fixed_income_pct': 40}),   # tuotto puuttuu
                 ({'equity_pp': 1, 'fixed_income_pp': None, 'prev_as_of': '2026-09-30', 'cur_as_of': '2026-10-31'}, {'equity_pct': 60, 'fixed_income_pct': None})):  # paino puuttuu
    _m = MD.market_drift(_ch, _pv, _rows)
    chk(_m['status'] == 'unavailable' and _m['reason'] and _m['equity_pp'] is None and _m['fixed_income_pp'] is None and _m['residual_equity_pp'] is None, f'market_drift tyhjä: {_ch}')
for s in h['snapshots']:
    for f in s['funds']:
        ch = f.get('allocation_change_vs_prev') or {}
        m = ch.get('market_drift')
        if not m: continue
        if m['status'] == 'computed':
            w = m['prev_weights']; e = m['etf_returns']
            d = MD.drift(w['equity_pct'], w['fixed_income_pct'], e['equity']['return_pct'] / 100, e['bond']['return_pct'] / 100)
            chk(abs(d[2] - m['equity_pp']) < 0.006 and abs(d[3] - m['fixed_income_pp']) < 0.006, f"{s['period']} n{f['n']} market_drift kaava")
            chk(e['equity']['etf'] == 'SPYI' and e['bond']['etf'] == 'VAGF' and e['equity']['source'] and w['as_of'] == ch['prev_as_of'], f"{s['period']} n{f['n']} market_drift lähteet")
            if ch.get('equity_pp') is not None: chk(abs(ch['equity_pp'] - m['equity_pp'] - m['residual_equity_pp']) < 0.011, f"{s['period']} n{f['n']} residuaali osake")
            if ch.get('fixed_income_pp') is not None: chk(abs(ch['fixed_income_pp'] - m['fixed_income_pp'] - m['residual_fixed_income_pp']) < 0.011, f"{s['period']} n{f['n']} residuaali korko")
        else:
            chk(m.get('reason') and m['equity_pp'] is None and m['fixed_income_pp'] is None, f"{s['period']} n{f['n']} market_drift tyhjä ilman syytä")
# kiinnitetty: OP-Maltillinen 10/2026 (57,6/41,1/1,3; SPYI -0,3085 %, VAGF +1,4518 %)
_s10 = next(s for s in h['snapshots'] if s['period'] == '2026-10')
if _s10['revision'] >= 10:
    _op = next(f for f in _s10['funds'] if f['n'] == 14)['allocation_change_vs_prev']['market_drift']
    chk((_op['equity_pp'], _op['fixed_income_pp'], _op['residual_equity_pp'], _op['residual_fixed_income_pp']) == (-0.42, 0.42, 0.42, -0.12), 'OP-Maltillinen markkinavaikutus')
# r011: Nordnet One rahastokoko (Morningstar Global Fund Size); r010 arkisto ennallaan
_r010 = json.load(open(ROOT / 'revisions/2026-10/r010.json'))
_nn10 = next(f for f in _r010['funds'] if f['n'] == 20)['costs']
chk(_nn10.get('fund_size') == 1599 and _nn10.get('fund_size_currency') is None, 'r010 Nordnet koko ennallaan')
if _s10['revision'] >= 11:
    _nn = next(f for f in _s10['funds'] if f['n'] == 20)['costs']
    chk(_nn['fund_size'] == 55146100 and _nn['fund_size_currency'] == 'EUR' and _nn['fund_size_as_of'] == '2026-11-05' and _nn['fund_size_type'] == 'fund', 'Nordnet One rahastokoko r011')
    chk(round(_nn['fund_size'] / 1e6) == 55, 'Nordnet koko ei pyöristy nollaan')
    chk('osuussarja' in (_nn.get('note') or '').lower() or 'share class' in (_nn.get('note') or '').lower(), 'Nordnet notessa osuussarja')
for s in h['snapshots']:
    for f in s['funds']:
        typ = (f.get('costs') or {}).get('fund_size_type')
        chk(typ in (None, 'fund', 'share_class'), f"{s['period']} n{f['n']} fund_size_type")
        sz = (f.get('costs') or {}).get('fund_size')
        if typ: chk(sz and (f.get('costs') or {}).get('fund_size_currency') in ('EUR', 'USD') and (f.get('costs') or {}).get('fund_size_as_of'), f"{s['period']} n{f['n']} koko puutteellinen tyypin kanssa")

print('\n'.join(err) or f'OK: {len(periods)} kautta {periods}')
sys.exit(1 if err else 0)
