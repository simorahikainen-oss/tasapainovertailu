"""50/50 kk-rebalansoitu vertailusalkku data/benchmark_monthly.csv:stä."""
import csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV = ROOT / 'data' / 'benchmark_monthly.csv'

def load():
    return list(csv.DictReader(open(CSV)))

def append_month(period, me, spyi_ret, bond_ret, src='VAGF.DE'):
    rows = load()
    if any(r['month'] == period for r in rows): return False
    if rows and rows[-1]['month'] >= period: raise SystemExit('benchmark-rivi ei ole seuraava kuukausi')
    with open(CSV, 'a', newline='') as f:
        csv.writer(f).writerow([period, me, round(spyi_ret, 6), round(bond_ret, 6), src, round(0.5 * spyi_ret + 0.5 * bond_ret, 6)])
    return True

def horizons(period):
    rows = [r for r in load() if r['month'] <= period]
    if not rows or rows[-1]['month'] != period: raise SystemExit(f'benchmark-data puuttuu kaudelta {period}')
    y = period[:4]
    def comp(sub, key, years=None):
        p = 1.0
        for r in sub: p *= 1 + float(r[key])
        return round(((p ** (1 / years)) - 1) * 100 if years else (p - 1) * 100, 2)
    out = {}
    for key, name in (('spyi_ret', 'SPYI_px'), ('bond_ret', 'VAGF_px'), ('etf_50_50_ret', 'etf_50_50_rebalanced')):
        d = {'ytd': comp([r for r in rows if r['month'].startswith(y)], key), 'y1': comp(rows[-12:], key)}
        for n in (3, 5, 10):
            d[f'y{n}'] = comp(rows[-12 * n:], key, n) if len(rows) >= 12 * n else None
        out[name] = d
    return out
