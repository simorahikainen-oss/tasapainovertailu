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
print('\n'.join(err) or f'OK: {len(periods)} kautta {periods}')
sys.exit(1 if err else 0)
