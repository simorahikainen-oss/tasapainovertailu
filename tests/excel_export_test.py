"""Regressiotesti Excel-viennille (vaatii google-chrome): python3 tests/excel_export_test.py
Lukee viennin otsikkorivin perusteella ja tarkistaa, että arvo-, kattavuus- ja päiväsarakkeet eivät sekoitu."""
import subprocess, json, re, pathlib, time, sys, os
ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = ('load().then(async()=>{await new Promise(r=>setTimeout(r,500));HTMLAnchorElement.prototype.click=function(){};'
        'const W=ExcelJS.Workbook.prototype.addWorksheet;let n=[];ExcelJS.Workbook.prototype.addWorksheet=function(a,b){const w=W.call(this,a,b);n.push(w);return w};'
        'await document.getElementById("csv").onclick();const ws=n[0];const H=ws.getRow(1).values;const out={};'
        'ws.eachRow((r,i)=>{if(i>1){const o={};r.values.forEach((v,j)=>{if(H[j])o[H[j]]=v});out[String(o["Rahasto"])]=o}});'
        'const p=document.createElement("pre");p.id="res";p.textContent=JSON.stringify(out);document.body.appendChild(p)}).catch(')
src = (ROOT / 'index.html').read_text().replace('load().catch(', HOOK)
t = ROOT / '_xl_test.html'; t.write_text(src)
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8766'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    time.sleep(1)
    dom = subprocess.run(['google-chrome', '--headless=new', '--no-sandbox', '--virtual-time-budget=15000', '--dump-dom',
                          'http://localhost:8766/_xl_test.html?local'], capture_output=True, text=True, timeout=90).stdout
finally:
    srv.kill(); t.unlink()
m = re.search(r'<pre id="res">(.*?)</pre>', dom, re.S)
assert m, 'vientiä ei saatu'
import html
X = json.loads(html.unescape(m.group(1)))
row = lambda key: next(v for k, v in X.items() if key in k)
h = json.load(open(ROOT / 'history.json')); s = h['snapshots'][-1]
err = []
for f in s['funds']:
    b = f.get('bond_metrics') or {}; name = next(z['name'] for z in h['funds'] if z['n'] == f['n'])
    r = row(f['isin'])
    exp = {'Eff. duraatio (v)': (b.get('effective_duration_years') or {}).get('value'), 'Eff. duraatio pvm': (b.get('effective_duration_years') or {}).get('as_of'),
           'YTW %': (b.get('yield_to_worst_pct') or {}).get('value'), 'YTW pvm': (b.get('yield_to_worst_pct') or {}).get('as_of')}
    for k, lab in (('effective_duration_years', 'Duraatio'), ('yield_to_worst_pct', 'YTW')):
        e = (b.get('illustrative_estimates') or {}).get(k) or {}
        pre = 'Duraatio' if lab == 'Duraatio' else 'YTW'
        exp[f'{pre} ARVIO (v)' if pre == 'Duraatio' else 'YTW ARVIO %'] = e.get('value')
        exp[f'{"Duraatioarvion" if pre == "Duraatio" else "YTW-arvion"} kattavuus %'] = e.get('coverage_pct')
        exp[f'{"Duraatioarvio" if pre == "Duraatio" else "YTW-arvio"} pvm'] = e.get('as_of')
    for col, v in exp.items():
        if r.get(col) != v: err.append(f"n{f['n']} {col}: vienti {r.get(col)!r} != data {v!r}")
# kiinnitetyt arvot
ry = row('FI0008807078'); np = row('FI4000171178')
for col, v in (('Eff. duraatio (v)', 4.47), ('Eff. duraatio pvm', '2026-10-31'), ('Duraatio ARVIO (v)', 5.36), ('Duraatioarvion kattavuus %', 89.9),
               ('Duraatioarvio pvm', '2026-10-31'), ('YTW ARVIO %', 5.89), ('YTW-arvion kattavuus %', 91.5), ('YTW-arvio pvm', '2026-10-31')):
    if ry.get(col) != v: err.append(f'Ryhti {col}: {ry.get(col)!r} != {v!r}')
for col, v in (('Duraatioarvion kattavuus %', 79.1), ('YTW-arvion kattavuus %', 98.0), ('Duraatioarvio pvm', '2026-08-31')):
    if np.get(col) != v: err.append(f'Nordea Premium I {col}: {np.get(col)!r} != {v!r}')
# 50/50-rivi = VAGF:n korko-osuuden mittarit sellaisenaan (ei *0,5)
vb = s['benchmark'].get('VAGF_bond_metrics') or {}; ve = vb.get('illustrative_estimates') or {}
mix = next(v for k, v in X.items() if 'ETF-salkku (50/50)' in k); vg = row('IE00BG47KH54')
mexp = {'Eff. duraatio (v)': vb['effective_duration_years']['value'], 'Eff. duraatio pvm': vb['effective_duration_years']['as_of'],
        'YTW %': None, 'YTW pvm': None, 'Duraatio ARVIO (v)': ve['effective_duration_years']['value'], 'Duraatioarvion kattavuus %': ve['effective_duration_years']['coverage_pct'],
        'Duraatioarvio pvm': ve['effective_duration_years']['as_of'], 'YTW ARVIO %': ve['yield_to_worst_pct']['value'], 'YTW-arvion kattavuus %': ve['yield_to_worst_pct']['coverage_pct'], 'YTW-arvio pvm': ve['yield_to_worst_pct']['as_of']}
pinned = {'Eff. duraatio (v)': 5.99, 'Eff. duraatio pvm': '2026-09-30', 'YTW %': None, 'Duraatio ARVIO (v)': 6.23, 'Duraatioarvion kattavuus %': 97.3,
          'Duraatioarvio pvm': '2026-09-30', 'YTW ARVIO %': 4.92, 'YTW-arvion kattavuus %': 97.7, 'YTW-arvio pvm': '2026-09-30'}
for nm, r in (('50/50', mix), ('VAGF', vg)):
    for col, v in mexp.items():
        if r.get(col) != v: err.append(f'{nm} {col}: {r.get(col)!r} != data {v!r}')
    if h['snapshots'][-1].get('revision', 0) >= 7:
        for col, v in pinned.items():
            if r.get(col) != v: err.append(f'{nm} {col}: {r.get(col)!r} != kiinnitetty {v!r}')
if 'korko-osuus' not in str(mix.get('Korkotaulukon pohja (scope)')): err.append('50/50 scope-selite puuttuu')
# markkinavaikutus-sarakkeet otsikon mukaan
for f in s['funds']:
    m = (f.get('allocation_change_vs_prev') or {}).get('market_drift') or {}
    ok = m.get('status') == 'computed'
    r = row(f['isin'])
    for col, v in (('Osake Δ markkina (%-yks.)', m.get('equity_pp') if ok else None), ('Korko Δ markkina (%-yks.)', m.get('fixed_income_pp') if ok else None),
                   ('Osake Δ aktiivinen/muu (%-yks.)', m.get('residual_equity_pp') if ok else None), ('Korko Δ aktiivinen/muu (%-yks.)', m.get('residual_fixed_income_pp') if ok else None)):
        if r.get(col) != v: err.append(f"n{f['n']} {col}: vienti {r.get(col)!r} != data {v!r}")
    if ok and 'SPYI' not in str(r.get('Markkinavaikutuksen perusteet')): err.append(f"n{f['n']} perusteet puuttuu")
if s.get('revision', 0) >= 10:
    op = next(v for k, v in X.items() if 'FI0008803812' in k or 'OP-Maltillinen' in k)
    for col, v in (('Osake Δ markkina (%-yks.)', -0.42), ('Korko Δ markkina (%-yks.)', 0.42), ('Osake Δ aktiivinen/muu (%-yks.)', 0.42), ('Korko Δ aktiivinen/muu (%-yks.)', -0.12)):
        if op.get(col) != v: err.append(f'OP-Maltillinen {col}: {op.get(col)!r} != {v!r}')
    print('OP-Maltillinen:', {k: op.get(k) for k in ('Osake Δ', 'Osake Δ markkina (%-yks.)', 'Osake Δ aktiivinen/muu (%-yks.)', 'Korko Δ', 'Korko Δ markkina (%-yks.)', 'Korko Δ aktiivinen/muu (%-yks.)')})
if s.get('revision', 0) >= 13:
    lt = next(v for k, v in X.items() if 'LocalTapiola World 50' in k or 'LähiTapiola' in k)
    for col, v in (('Osake Δ markkina (%-yks.)', -0.41), ('Korko Δ markkina (%-yks.)', 0.41), ('Osake Δ aktiivinen/muu (%-yks.)', None), ('Korko Δ aktiivinen/muu (%-yks.)', None)):
        if lt.get(col) != v: err.append(f'LähiTapiola {col}: {lt.get(col)!r} != {v!r}')
    basis = str(lt.get('Markkinavaikutuksen perusteet') or '')
    if '30.9.2026' not in basis or '30.10.2026' not in basis: err.append(f'LähiTapiola perusteet jakso väärä: {basis!r}')
    if '30.6.2026' not in basis: err.append(f'LähiTapiola perusteet lähtöpäivä puuttuu: {basis!r}')
    print('LähiTapiola:', {k: lt.get(k) for k in ('Osake Δ', 'Osake Δ markkina (%-yks.)', 'Osake Δ aktiivinen/muu (%-yks.)', 'Korko Δ', 'Korko Δ markkina (%-yks.)', 'Korko Δ aktiivinen/muu (%-yks.)')})
# r011: Nordnet koko ja tyyppi
if s.get('revision', 0) >= 11:
    nn = next(v for k, v in X.items() if 'SE0017832439' in k or 'Nordnet One' in k)
    if nn.get('Koko (M)') != 55.1461: err.append(f"Nordnet Koko (M): {nn.get('Koko (M)')!r} != 55.1461")
    if nn.get('Koko-tyyppi') != 'rahasto': err.append(f"Nordnet Koko-tyyppi: {nn.get('Koko-tyyppi')!r} != 'rahasto'")
    print('Nordnet:', {k: nn.get(k) for k in ('Koko (M)', 'Koko-tyyppi')})

print('50/50:', {k: mix.get(k) for k in pinned})
print('\n'.join(err) or f'OK: Excel-vienti {len(X)} riviä, sarakkeet täsmäävät dataan')
print('Ryhti:', {k: ry.get(k) for k in ('Eff. duraatio (v)', 'Eff. duraatio pvm', 'Duraatio ARVIO (v)', 'Duraatioarvion kattavuus %', 'Duraatioarvio pvm', 'YTW ARVIO %', 'YTW-arvion kattavuus %', 'YTW-arvio pvm')})
print('Nordea Premium I:', {k: np.get(k) for k in ('Duraatio ARVIO (v)', 'Duraatioarvion kattavuus %', 'YTW ARVIO %', 'YTW-arvion kattavuus %', 'Duraatioarvio pvm', 'YTW-arvio pvm')})
sys.exit(1 if err else 0)
