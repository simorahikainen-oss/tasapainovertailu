#!/usr/bin/env python3
"""Muuntaa selaimen bond_tables_batchN.json -tiedoston stage_snapshot.py content -syötteeksi.
  python3 scripts/import_bond_tables.py <batch.json> <out_updates.json>
Batch-muoto (kuten bond_tables_batch4.json): funds[{n:"n2"|"VAGF", isin?, url, table_footnote "As of Mon DD, YYYY | ...",
  scope?, note?, screenshots?, direct_measures?: {effective_duration, yield_to_worst, as_of, as_of_label, scope?},
  duration_p1/p2, ytw_p1/p2: {header, rows}}]. '–' = null. Rahasto tunnistetaan n:llä ja URL:n on vastattava tietokannan ms_url:ia."""
import json, sys, re, datetime as dt, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
MON = {m: i for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
VAGF_URL = 'https://global.morningstar.com/en-nd/investments/etfs/0P0001HSBO/portfolio'

def num(v):
    return None if v in ('\u2013', '-', '', None) else float(v)

def date_from(label):
    m = re.search(r'[Aa]s of (\w{3}) (\d{1,2}), (\d{4})', label or '')
    assert m, f'päivä puuttuu: {label}'
    return dt.date(int(m.group(3)), MON[m.group(1)], int(m.group(2))).isoformat()

def table(x, pre, key, method):
    p1, p2 = x[pre + '_p1'], x[pre + '_p2']
    assert p2['header'][-1] == 'Subtotal Weight', 'Subtotal Weight -sarake puuttuu'
    cols = p1['header'][1:] + p2['header'][1:-1]
    rows = [r[0] for r in p1['rows']]
    assert rows == [r[0] for r in p2['rows']], 'sivujen rivit eivät täsmää'
    vals = [[num(v) for v in a[1:]] + [num(v) for v in b[1:-1]] for a, b in zip(p1['rows'], p2['rows'])]
    return {'heading': 'Fixed Income Exposure Analysis – ' + ('Effective Duration' if key == 'effective_duration' else 'Yield To Worst'),
            'as_of': date_from(x['table_footnote']), 'as_of_label': x['table_footnote'],
            'basis': 'long positions of holdings (holdings-based calculations)', 'scope': 'unknown',
            'scope_note': x.get('scope') or 'Otsikko ei kerro, onko pohjana korko-osuus vai koko salkku.',
            'cell_unit': '% (taulukon solut; pohja ei ilmoitettu)', 'columns': cols, 'rows': rows, 'values': vals,
            'subtotal_weight': [num(b[-1]) for b in p2['rows']], 'source_url': x['url'], 'read_method': method, 'screenshots': x.get('screenshots')}

def main(src, out):
    h = json.load(open(ROOT / 'history.json')); F = {f['n']: f for f in h['funds']}
    d = json.load(open(src)); ups = []
    for x in d['funds']:
        n = x['n'] if x['n'] in ('VAGF', 'SPYI') else int(str(x['n']).lstrip('n'))
        exp = VAGF_URL if n == 'VAGF' else F[n]['ms_url']
        assert x['url'] == exp, (n, x['url'], exp)
        if n != 'VAGF': assert x.get('isin') in (None, F[n]['isin']), (n, x.get('isin'))
        dm = dict(x.get('direct_measures') or x.get('direct_measures_Investment_column') or {})
        if dm.get('label') and not dm.get('as_of_label'): dm['as_of_label'] = dm['label']
        dm.pop('scope', None) if dm.get('scope') is None else None
        # vain Effective Duration ja Yield to Worst; YTM/modified duration/coupon eivät ole korvikkeita
        extra = {k: dm[k] for k in ('yield_to_maturity', 'modified_duration', 'weighted_coupon', 'weighted_price') if k in dm}
        def rep(k, label):
            v = dm.get(k)
            return {'value': v, 'as_of': date_from(dm.get('as_of_label')) if v is not None else None, 'label': label}
        bm = {'scope': dm.get('scope', 'unknown'), 'method': 'reported', 'source': 'Morningstar portfolio, Bond tab',
              'source_url': x['url'], 'checked_at': d['read_at'], 'as_of_label': dm.get('as_of_label') or x.get('table_footnote'),
              'effective_duration_years': rep('effective_duration', 'Effective Duration'),
              'yield_to_worst_pct': rep('yield_to_worst', 'Yield to Worst'),
              'note': ' '.join(z for z in ((x.get('note') or '').strip(), (x.get('anomaly') or '').strip()) if z) or None}
        if extra: bm['other_measures_not_used'] = extra
        if x.get('duration_p1'):
            bm['exposure_tables'] = {'effective_duration': table(x, 'duration', 'effective_duration', d.get('method')),
                                     'yield_to_worst': table(x, 'ytw', 'yield_to_worst', d.get('method'))}
        ups.append({'n': n, 'bond_metrics': bm})
    json.dump(ups, open(out, 'w'), ensure_ascii=False, indent=1)
    print(f'{len(ups)} päivitystä -> {out}')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
