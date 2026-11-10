#!/usr/bin/env python3
"""Luo tai päivittää kuukausisnapshotin vaiheittain (ks. SCHEMA.md).

  python3 scripts/stage_snapshot.py returns 2026-10   # tuotot + vertailu heti kuun lopun jälkeen
  python3 scripts/stage_snapshot.py content 2026-10 updates.json   # sisältö (allokaatio) kun saatavilla
  python3 scripts/stage_snapshot.py drift 2026-10   # painomuutosten markkinavaikutus (SPYI/VAGF) uutena revisiona

Jokainen tallennus kirjoittaa koko snapshotin kopion revisions/<kausi>/rNNN.json
eikä koskaan poista vanhoja revisioita tai muita kuukausia.
"""
import json, sys, copy, datetime as dt, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark
import market_drift as MD
ROOT = pathlib.Path(__file__).resolve().parent.parent
HIST = ROOT / 'history.json'
SUSPECT_PP = 5.0

def now(): return dt.datetime.now().astimezone().isoformat(timespec='seconds')

def latest_alloc(h, n, before):
    for s in sorted(h['snapshots'], key=lambda s: s['period'], reverse=True):
        if s['period'] >= before: continue
        for f in s['funds']:
            a = f.get('allocation_primary') or {}
            if f['n'] == n and a.get('equity_pct') is not None: return s['period'], a
    return None, None

def save_revision(h, snap, summary):
    revs = snap.setdefault('revisions', [])
    k = len(revs) + 1
    snap['revision'] = k
    path = f"revisions/{snap['period']}/r{k:03d}.json"
    revs.append({'revision': k, 'saved_at': now(), 'path': path, 'summary': summary})
    p = ROOT / path; p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists(): raise SystemExit(f'{path} on jo olemassa – ei ylikirjoiteta')
    body = copy.deepcopy(snap); body.pop('revisions', None)
    json.dump(body, open(p, 'w'), ensure_ascii=False, indent=1)

def coverage(h, snap):
    me = snap.get('month_end') or snap.get('return_date')
    fund = {f['n']: f for f in h['funds']}
    elig = [f for f in snap['funds'] if (f.get('allocation_primary') or {}).get('equity_pct') is not None
            and not (fund[f['n']].get('merged_on') and fund[f['n']]['merged_on'] <= (me or ''))]
    dates = sorted(f['allocation_primary']['as_of'] for f in elig if f['allocation_primary'].get('as_of'))
    cur = [f for f in elig if me and f['allocation_primary'].get('as_of') == me]
    by = {}
    for d in dates: by[d] = by.get(d, 0) + 1
    snap['content_coverage'] = {'funds_total': len(snap['funds']), 'eligible': len(elig), 'current_month_end': len(cur),
                                'as_of_min': dates[0] if dates else None, 'as_of_max': dates[-1] if dates else None, 'by_as_of': by}
    snap['content_status'] = 'complete' if me and len(cur) == len(elig) else 'partial'

def returns_stage(period):
    h = json.load(open(HIST)); st = json.load(open(ROOT / 'data' / 'staging' / f'{period}.json'))
    me = st['month_end']
    if any(s['period'] == period for s in h['snapshots']):
        snap = next(s for s in h['snapshots'] if s['period'] == period)
    else:
        snap = {'period': period, 'funds': []}; h['snapshots'].append(snap)
    e = st['etfs']
    sp, va = e['SPYI']['xetra']['month_ret'], e['VAGF']['xetra']['month_ret']
    benchmark.append_month(period, e['SPYI']['xetra']['cur'][0], sp, va)
    hz = benchmark.horizons(period)
    prevs = [s for s in h['snapshots'] if s['period'] < period and s.get('benchmark', {}).get('SPYI_meta')]
    pb = prevs[-1]['benchmark'] if prevs else {}
    S, V = e['SPYI']['returns'], e['VAGF']['returns']
    b = {'SPYI': {'isin': e['SPYI']['isin'], 'ytd': S['ytd'], 'y1': S['y1'], 'as_of': me, 'source': 'Morningstar NAV ' + e['SPYI']['secid']},
         'VAGF': {'isin': e['VAGF']['isin'], 'ytd': V['ytd'], 'y1': V['y1'], 'as_of': me, 'source': 'Morningstar NAV ' + e['VAGF']['secid']},
         'etf_50_50': {'ytd': round(.5 * S['ytd'] + .5 * V['ytd'], 2), 'y1': round(.5 * S['y1'] + .5 * V['y1'], 2), 'method': '0.5*SPYI+0.5*VAGF'},
         'etf_50_50_rebalanced': dict(hz['etf_50_50_rebalanced'], method='50/50 kk-rebalansointi, Xetra-päätöskurssit (Yahoo)',
                                      proxy_notes=(pb.get('etf_50_50_rebalanced') or {}).get('proxy_notes')),
         'SPYI_px': hz['SPYI_px'], 'VAGF_px': hz['VAGF_px'],
         'xetra_month_close': {k: e[k]['xetra'] for k in ('SPYI', 'VAGF')}}
    for k in ('SPYI', 'VAGF'):
        m = copy.deepcopy(pb.get(f'{k}_meta') or {})
        b[f'{k}_meta'] = m
    snap['benchmark'] = b
    snap['return_date'] = me; snap['month_end'] = me
    snap['returns_status'] = 'published'; snap['returns_published_at'] = now()
    snap['returns_method'] = st['returns_method']
    prev_snap = max((s for s in h['snapshots'] if s['period'] < period), key=lambda s: s['period'], default=None)
    pf = {f['n']: f for f in (prev_snap or {}).get('funds', [])}
    meta = {f['n']: f for f in h['funds']}
    cur = {f['n']: f for f in snap['funds']}
    flags = []
    for n_s, x in st['funds'].items():
        n = int(n_s); f = cur.get(n)
        if f is None:
            f = {'n': n, 'isin': x['isin']}; snap['funds'].append(f)
            p = pf.get(n, {})
            pp, a = latest_alloc(h, n, period)
            if a:
                ca = copy.deepcopy(a); ca['carried_from_period'] = pp; f['allocation_primary'] = ca
                f['allocation'] = {'equity_pct': a.get('equity_pct'), 'fixed_income_pct': a.get('fixed_income_pct'), 'as_of': a.get('as_of'), 'source_url': a.get('source_url')}
            for k in ('features', 'explanation', 'allocation_morningstar'):
                if p.get(k) is not None: f[k] = copy.deepcopy(p[k])
            f['text_from_period'] = prev_snap['period'] if prev_snap else None
            f['allocation_change_vs_prev'] = None
            if p.get('costs'): f['costs'] = copy.deepcopy(p['costs'])
        fd = x.get('feed') or {}
        if fd:
            c = f.setdefault('costs', {})
            for src, dst in (('OngoingCharge', 'ongoing_cost_pct'), ('FundTNAV', 'fund_size'), ('FundTNAVDate', 'fund_size_as_of'), ('CategoryName', 'category_fi')):
                if fd.get(src) is not None: c[dst] = fd[src]
            c['source'] = 'Morningstar (lt.morningstar.com screener API: OngoingCharge, FundTNAV, FundTNAVDate)'
            c['fetched_at'] = st['fetched_at'][:10]
            if fd.get('AssetAllocEquity') is not None:
                f['allocation_morningstar_feed'] = {'equity_net_pct': fd['AssetAllocEquity'], 'portfolio_date': fd.get('PortfolioDate'),
                    'source': 'Morningstar screener AssetAllocEquity (vain osake netto, ei korko/kassa-erittelyä)', 'fetched_at': st['fetched_at'][:10]}
        r = x.get('returns')
        mf = meta[n]
        if r:
            f['returns'] = dict(r, as_of=me, source=mf.get('ms_url', '').replace('/portfolio', '/quote'), method='month_end_cumulative')
            f['vs_50_50'] = {k: round(r[k] - b['etf_50_50'][k], 2) for k in ('ytd', 'y1')}
            f['vs_50_50_rebalanced'] = {k: (round(r[k] - b['etf_50_50_rebalanced'][k], 2) if r.get(k) is not None and b['etf_50_50_rebalanced'].get(k) is not None else None) for k in ('ytd', 'y1', 'y3', 'y5', 'y10')}
            f.pop('returns_missing', None)
        else:
            f['returns'] = None; f['vs_50_50'] = None; f['vs_50_50_rebalanced'] = None
            f['returns_missing'] = mf.get('merger_note') or 'Kuun lopun tuottoa ei saatu Morningstar-feedistä.'
            flags.append({'n': n, 'flag': 'returns_missing'})
        fa, a = f.get('allocation_morningstar_feed'), f.get('allocation_primary') or {}
        f['flags'] = [z for z in f.get('flags', []) if z.get('type') not in ('allocation_stale', 'feed_divergence')]
        if a.get('as_of') != me:
            f['flags'].append({'type': 'allocation_stale', 'note': f"Sisältö {a.get('as_of')} (ei {me})"})
        if fa and a.get('equity_pct') is not None and fa.get('portfolio_date') and fa['portfolio_date'] > (a.get('as_of') or '') \
                and abs(fa['equity_net_pct'] - a['equity_pct']) > SUSPECT_PP:
            f['flags'].append({'type': 'feed_divergence', 'note': f"Morningstar-feed {fa['portfolio_date']}: osake {fa['equity_net_pct']} vs käytetty {a['equity_pct']} – tarkistettava ennen käyttöä"})
    snap['funds'].sort(key=lambda f: f['n'])
    coverage(h, snap)
    h['snapshots'].sort(key=lambda s: s['period'])
    h['schema_version'] = 2
    save_revision(h, snap, f"Tuotot {me} julkaistu; sisältö {snap['content_coverage']['current_month_end']}/{snap['content_coverage']['eligible']} kuun lopulta")
    json.dump(h, open(HIST, 'w'), ensure_ascii=False, indent=1)
    print(snap['revisions'][-1]['summary'], 'liput:', flags)

def src_type(a):
    return 'morningstar' if (a or {}).get('source') == 'morningstar' else 'company'

def from_morningstar(u):
    """Morningstarin portfolio-sivun Asset Allocation (net %): u = {n, as_of, source_url, morningstar_raw:{stocks,bonds,cash,other}, long?:{...}}.
    Sama normalisointi kuin 9/2026 auditissa: jos nettosumma > 101 tai kassa/muu < 0 -> osake ja korko suhteutetaan positiivisten summaan."""
    m = u['morningstar_raw']; e, fi = m['stocks'], m['bonds']; cash = m.get('cash') or 0
    # preferred/convertible kuuluvat 'muu'-luokkaan (ei osake eikä korko), kuten 9/2026 säännössä
    oth = (m.get('other') or 0) + (m.get('preferred') or 0) + (m.get('convertible') or 0)
    assert e is not None and fi is not None, f"n{u['n']}: Morningstar ei läpivalaise osake/korko-jakoa – käytä yhtiöraporttia"
    a = {'equity_pct': e, 'fixed_income_pct': fi, 'other_pct': round(100 - e - fi, 2), 'as_of': u['as_of'], 'source': 'morningstar',
         'source_url': u['source_url'], 'raw_net': {('equity' if k == 'stocks' else 'fixed_income' if k == 'bonds' else k): v for k, v in m.items()}}
    if u.get('long'): a['raw_long'] = u['long']
    tot = e + fi + cash + oth
    if tot > 101 or cash < 0 or oth < 0:
        pos = sum(v for v in (e, fi, cash, oth) if v > 0)
        a['equity_pct'], a['fixed_income_pct'] = round(e / pos * 100, 1), round(fi / pos * 100, 1)
        a['other_pct'] = round(100 - a['equity_pct'] - a['fixed_income_pct'], 1)
        a['note'] = f"normalisoitu Morningstarin nettoluvuista (nettosumma {tot:.2f} %; johdannaiset/lyhyet positiot)"
    if u.get('note'): a['note'] = (a.get('note', '') + ' ' + u['note']).strip()
    return a

def weighted_table(b, month_end, n):
    """Morningstarin kaavion taulukkonäkymä (chart -> table) per mittari:
    b['table'][metric] = {"as_of","source_url","table_name","unit","rows":[{"label","weight_pct","value"|null,"lower"|null,"upper"|null}], "weight_basis"}
    Laskenta vain riveistä, joilla on tarkka numeerinen value. Pelkkä väli (lower/upper) tai avoin pää EI saa
    keskipistettä: rivi jää kattamattomaksi. Painot normalisoidaan katetuille riveille; coverage = katettu / taulukon kokonaispaino."""
    tabs = b.get('table') or {}
    for k, label in BM_KEYS.items():
        t = tabs.get(k)
        if not t: continue
        assert t.get('as_of') and t['as_of'] <= month_end and t.get('source_url') and t.get('rows'), f'n{n}: {k} taulukon provenance'
        tot = sum(r['weight_pct'] for r in t['rows'] if r.get('weight_pct') is not None)
        cov = [r for r in t['rows'] if isinstance(r.get('value'), (int, float)) and r.get('weight_pct') is not None]
        w = sum(r['weight_pct'] for r in cov)
        t['coverage_pct'] = round(w / tot * 100, 1) if tot else 0.0
        t['rows_without_exact_value'] = len(t['rows']) - len(cov)
        val = round(sum(r['weight_pct'] * r['value'] for r in cov) / w, 2) if w and t['rows_without_exact_value'] == 0 else None
        t['calc_note'] = ('Painotettu keskiarvo taulukon tarkoista arvoista.' if val is not None else
                          'Ei laskettu: osalla riveistä vain väli/avoin pää (keskipistettä ei käytetä) tai painot puuttuvat.')
        b[k] = {'value': val, 'as_of': t['as_of'] if val is not None else None, 'label': label}
    b['table'] = tabs

import re as _re
EST_KEY = {'effective_duration': ('effective_duration_years', 'v'), 'yield_to_worst': ('yield_to_worst_pct', '%')}

def bucket_mid(col):
    """Suljettu väli 'a-b' (yksikkö saa olla perässä) -> keskipiste; avoimet (<x, >x), Unk ja Not Applicable -> None."""
    m = _re.fullmatch(r'\s*(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)\s*(Yrs|%)?\s*', col)
    return (float(m.group(1)) + float(m.group(2))) / 2 if m else None

def illustrative_estimate(t):
    """Havainnollistava arvio: suljettujen välien keskipisteillä painotettu keskiarvo, vain katetuista painoista
    (käyttäjän hyväksymä 7.11.2026). Ei koskaan raportoitu mittari."""
    tot = cov = acc = opn = unk = 0.0; used = []
    for j, col in enumerate(t['columns']):
        w = sum(r[j] for r in t['values'] if r[j] is not None)
        tot += w; mid = bucket_mid(col)
        if mid is not None:
            cov += w; acc += w * mid
            if w: used.append({'column': col, 'midpoint': mid, 'weight_pct': round(w, 2)})
        elif col.strip().startswith(('<', '>')): opn += w
        else: unk += w
    sub = t.get('subtotal_weight')
    pub = round(sum(x for x in sub if x is not None), 2) if sub else None
    den = pub if pub else tot
    anomalies = []
    if sub:
        for i, r in enumerate(t['values']):
            rs = sum(v for v in r if v is not None)
            if sub[i] is not None and abs(rs - sub[i]) > 0.05:
                anomalies.append({'row': t['rows'][i], 'cells_sum': round(rs, 2), 'subtotal': sub[i]})
    out = {'value': round(acc / cov, 2) if cov else None, 'covered_weight_pct': round(cov, 2), 'open_weight_pct': round(opn, 2),
           'unknown_weight_pct': round(unk, 2), 'total_weight_pct': round(tot, 2), 'published_total_weight_pct': pub,
           'coverage_pct': round(cov / den * 100, 1) if den else 0.0, 'coverage_basis': 'suljetut / julkaistu Subtotal-summa' if pub else 'suljetut / solujen summa',
           'buckets_used': used, 'row_sum_anomalies': anomalies}
    if pub is not None and abs(pub - 100) > 0.5:
        out['unclassified_vs_100_pct'] = round(100 - pub, 2)
        out['caveat'] = f'Taulukon painot summautuvat {pub} %:iin, eivät 100 %:iin; {round(100 - pub, 2)} %-yks. luokittelematta (pohja ei tiedossa).'
    return out

BM_KEYS = {'effective_duration_years': 'Effective Duration', 'yield_to_worst_pct': 'Yield to Worst'}

def validate_bond_metrics(b, month_end, n):
    """Vain suoraan raportoidut luvut (Morningstarin taulukko tai yhtiön raportti). Ei painotettuja laskelmia, ei arvioita, ei korvikkeita.
    {"scope":"fixed_income_sleeve"|"whole_fund", "source":..., "source_url":...,
     "effective_duration_years":{"value":x|null,"as_of":"YYYY-MM-DD"|null,"label":"Effective Duration"},
     "yield_to_worst_pct":{"value":x|null,"as_of":...,"label":"Yield to Worst"}}"""
    b = copy.deepcopy(b)
    b['method'] = b.get('method', 'reported')
    assert b['method'] in ('reported', 'weighted_table_calculation'), f'n{n}: method'
    assert 'components' not in b, f'n{n}: käytä table_rows-kenttää'
    if b['method'] == 'weighted_table_calculation':
        weighted_table(b, month_end, n)
    assert b.get('scope') in ('fixed_income_sleeve', 'whole_fund', 'unknown'), f'n{n}: scope pakollinen eikä sitä oleteta'
    assert b.get('checked_at'), f'n{n}: checked_at (milloin lähde tarkistettiin) pakollinen'
    for k in ('effective_duration_years', 'yield_to_worst_pct'):
        assert not (isinstance(b.get(k), dict) and b[k].get('estimate')), f'n{n}: arvioita ei tarkkoihin kenttiin'
    for tk, t in (b.get('exposure_tables') or {}).items():
        assert tk in ('effective_duration', 'yield_to_worst'), tk
        for req in ('as_of', 'as_of_label', 'source_url', 'heading', 'basis', 'scope', 'columns', 'rows', 'values', 'cell_unit'):
            assert t.get(req) is not None, f'n{n}: exposure_tables.{tk}.{req}'
        assert t['scope'] in ('fixed_income_sleeve', 'whole_fund', 'unknown') and t['as_of'] <= month_end
        assert len(t['values']) == len(t['rows']) and all(len(r) == len(t['columns']) for r in t['values'])
        k, unit = EST_KEY[tk]
        e = illustrative_estimate(t)
        e.update(unit=unit, as_of=t['as_of'], scope=t['scope'], label='arvio', source_url=t['source_url'],
                 method='Suljettujen välien keskipisteillä painotettu keskiarvo katetuista painoista; avoimet välit (<, >) ja Unk/Not Applicable pois; ei Morningstarin raportoima luku')
        b.setdefault('illustrative_estimates', {})[k] = e
    assert b.get('source_url') and b.get('source'), f'n{n}: lähde'
    for bad in ('ytm_pct', 'current_yield_pct', 'modified_duration_years', 'yield_to_maturity_pct'):
        assert bad not in b, f'n{n}: {bad} ei ole hyväksytty korvike'
    for k, label in BM_KEYS.items():
        m = b.get(k)
        if not isinstance(m, dict): m = {'value': None, 'as_of': None, 'label': label}
        m.setdefault('value', None); m.setdefault('as_of', None); m.setdefault('label', label)
        assert m['label'] == label, f"n{n}: {k} label '{m['label']}' != '{label}' – ei korviketta"
        if m['value'] is not None:
            assert isinstance(m['value'], (int, float)) and m['as_of'] and m['as_of'] <= month_end, f'n{n}: {k} arvo vaatii as_of <= kuun loppu'
        if 'check_status' in m:
            assert m['check_status'] in ('reported', 'checked_absent', 'not_checked'), f'n{n}: {k} check_status'
            assert (m['check_status'] == 'reported') == (m['value'] is not None), f'n{n}: {k} check_status vs value'
        b[k] = m
    return b

def content_stage(period, upd_path):
    """updates.json: [{"n":7,"allocation_primary":{equity_pct, fixed_income_pct, other_pct, as_of, source, source_url, note}, "features":..}]"""
    h = json.load(open(HIST)); snap = next(s for s in h['snapshots'] if s['period'] == period)
    ups = json.load(open(upd_path)); byn = {f['n']: f for f in snap['funds']}
    changed = []
    for u in ups:
        if u['n'] in ('VAGF', 'SPYI'):  # vertailu-ETF: korkomittarit benchmark-osioon
            assert set(u) <= {'n', 'bond_metrics'}, 'ETF:lle vain bond_metrics'
            snap['benchmark'][f"{u['n']}_bond_metrics"] = validate_bond_metrics(u['bond_metrics'], snap['month_end'], u['n'])
            changed.append(u['n']); continue
        f = byn[u['n']]
        for fl in u.get('flags', []):
            assert fl.get('type') and fl.get('note'), u['n']
            f.setdefault('flags', []); f['flags'] = [z for z in f['flags'] if z.get('type') != fl['type']] + [fl]
        if 'bond_metrics' in u:
            f['bond_metrics'] = validate_bond_metrics(u['bond_metrics'], snap['month_end'], u['n'])
            if 'allocation_primary' not in u and 'morningstar_raw' not in u:
                changed.append(u['n']); continue
        if 'allocation_primary' not in u and 'morningstar_raw' not in u:
            changed.append(u['n']); continue
        a = u.get('allocation_primary') or from_morningstar(u)
        assert a.get('as_of') and a.get('source_url') and a.get('equity_pct') is not None, u
        assert a['as_of'] <= snap['month_end'], 'sisältö ei voi olla kuun lopun jälkeiseltä päivältä'
        pp, prev = latest_alloc(h, u['n'], period)
        f['allocation_primary'] = a
        f['allocation'] = {'equity_pct': a['equity_pct'], 'fixed_income_pct': a.get('fixed_income_pct'), 'as_of': a['as_of'], 'source_url': a['source_url']}
        for k in ('features', 'explanation'):
            if k in u: f[k] = u[k]; f['text_from_period'] = period
        if prev and prev.get('as_of') != a['as_of']:
            f['allocation_change_vs_prev'] = {'equity_pp': round(a['equity_pct'] - prev['equity_pct'], 2),
                'fixed_income_pp': round(a['fixed_income_pct'] - prev['fixed_income_pct'], 2) if a.get('fixed_income_pct') is not None and prev.get('fixed_income_pct') is not None else None,
                'prev_as_of': prev['as_of'], 'cur_as_of': a['as_of'], 'prev_period': pp,
                'prev_source': prev.get('source'), 'cur_source': a.get('source')}
            ch = f['allocation_change_vs_prev']
            ch['interval_note'] = f"Muutos aikavälillä {prev['as_of']} – {a['as_of']}" + ('' if prev['as_of'][:7] != a['as_of'][:7] and int(a['as_of'][5:7]) - int(prev['as_of'][5:7]) in (1, -11) else ' (ei yhden kuukauden muutos)')
            if prev.get('source') != a.get('source') and src_type(prev) == src_type(a):
                ch['source_changed'] = True
                ch['note'] = f"Eri lähdedokumentti ({prev.get('source')} → {a.get('source')}); muutos osin lähde-/pyöristyseroa"
            if src_type(prev) != src_type(a):
                f['allocation_change_vs_prev']['source_changed'] = True
                f['allocation_change_vs_prev']['note'] = f"Lähde vaihtui ({prev.get('source')} {prev['as_of']} → {a.get('source')} {a['as_of']}); muutos osin menetelmäeroa, ei puhdas kuukausimuutos"
            ch['market_drift'] = MD.market_drift(ch, prev)
        else:
            f['allocation_change_vs_prev'] = None
        f['flags'] = [z for z in f.get('flags', []) if z.get('type') not in ('allocation_stale', 'feed_divergence')]
        if a['as_of'] != snap['month_end']: f['flags'].append({'type': 'allocation_stale', 'note': f"Sisältö {a['as_of']} (ei {snap['month_end']})"})
        changed.append(u['n'])
    coverage(h, snap)
    save_revision(h, snap, f"Sisältö päivitetty rahastoille {changed}; kuun lopulta {snap['content_coverage']['current_month_end']}/{snap['content_coverage']['eligible']}")
    json.dump(h, open(HIST, 'w'), ensure_ascii=False, indent=1)
    print(snap['revisions'][-1]['summary'])

def drift_stage(period):
    """Laskee markkinavaikutuksen (market_drift) kauden kaikille allocation_change_vs_prev-muutoksille; muut arvot ennallaan."""
    h = json.load(open(HIST)); snap = next(s for s in h['snapshots'] if s['period'] == period)
    done, blank = [], []
    for f in snap['funds']:
        ch = f.get('allocation_change_vs_prev')
        if not ch: continue
        pp, prev = latest_alloc(h, f['n'], period)
        assert prev and prev.get('as_of') == ch['prev_as_of'], (f['n'], prev and prev.get('as_of'), ch['prev_as_of'])
        assert abs(round(f['allocation_primary']['equity_pct'] - prev['equity_pct'], 2) - ch['equity_pp']) < 0.006, f['n']
        ch['market_drift'] = MD.market_drift(ch, prev)
        (done if ch['market_drift']['status'] == 'computed' else blank).append(f['n'])
    save_revision(h, snap, f"Markkinavaikutus (SPYI/VAGF-ajelehtiminen) lisätty painomuutoksiin: laskettu {done}" + (f", tyhjä {blank}" if blank else '') + "; muut arvot ennallaan")
    json.dump(h, open(HIST, 'w'), ensure_ascii=False, indent=1)
    print(snap['revisions'][-1]['summary'])

if __name__ == '__main__':
    {'returns': lambda: returns_stage(sys.argv[2]), 'content': lambda: content_stage(sys.argv[2], sys.argv[3]), 'drift': lambda: drift_stage(sys.argv[2])}[sys.argv[1]]()
