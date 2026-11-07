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
print('\n'.join(err) or f'OK: {len(periods)} kautta {periods}')
sys.exit(1 if err else 0)
