"""Painomuutoksen markkinavaikutus (passiivinen ajelehtiminen) ETF-tuotoilla.

Lähtöpainot w_e (osake), w_b (korko), w_o = 100 - w_e - w_b (muu, tuotto 0 %).
Lähtöpainoina käytetään edellisen kuun lopun painoja, tai jos niitä ei ole, viimeisimpiä
tunnettuja aiempia painoja (base_date merkitään, ei arvioida).
Osake = SPYI, korko = VAGF; tuotot EUR, Xetra kuukauden päätöskurssit (data/benchmark_monthly.csv,
sama sarja kuin sivuston SPYI_px/VAGF_px; kertyviä ETF:iä → kurssituotto = kokonaistuotto).
ETF-tuottoikkuna on aina sama kaikille rahastoille: edellinen kalenterikuukausi
(edellisen kuun loppu → snapshotin kuun loppu), ei rahaston oma havaintoväli.
  ajelehtinut osake = w_e(1+r_e) / (w_e(1+r_e) + w_b(1+r_b) + w_o), vastaavasti korko.
  markkinavaikutus = ajelehtinut - lähtöpaino (%-yks.).
  aktiivinen/muu (residuaali) = toteutunut muutos - markkinavaikutus, vain kun toteutunut
  muutos on yhden kalenterikuukauden mittainen; muuten null (change_period_months merkitään).
Tuottoja ei arvioida: jos kuukausivälille ei ole tarkkoja kuukauden loppukursseja, arvo jää tyhjäksi (status unavailable + reason).
"""
import calendar, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark

SRC = ('data/benchmark_monthly.csv: Xetra-päätöskurssien kuukausituotot (Yahoo Finance SPYI.DE / VAGF.DE, EUR); '
       'tarkistettu 10.11.2026 Yahoo päivädataa vasten, ei osinkoja (kertyvät osuuslajit)')
METHOD = ('Passiivinen ajelehtiminen yhdeltä kalenterikuukaudelta (edellinen kuun loppu → snapshotin kuun loppu), '
          'samoilla SPYI- (osake) ja VAGF- (korko) EUR-tuotoilla kaikille rahastoille. Lähtöpainoina edellisen kuun '
          'lopun osake-, korko- ja muu-painot, tai jos niitä ei ole, viimeisimmät tunnetut aiemmat painot (base_date; '
          'muu tuotto 0 %). Markkinavaikutus = ajelehtinut paino - lähtöpaino. Aktiivinen/muu = toteutunut muutos - '
          'markkinavaikutus vain, kun toteutunut muutos on yhden kuukauden mittainen; muuten tyhjä (change_period_months), '
          'koska jaksot eivät ole vertailukelpoisia (sis. kaupat, lähde-/pyöristyserot, rahaston omien sijoitusten ero ETF:istä).')
ETF = {'equity': ('SPYI', 'IE00B3YLTY66', 'SPYI.DE', 'spyi_ret'), 'bond': ('VAGF', 'IE00BG47KH54', 'VAGF.DE', 'bond_ret')}

def drift(w_e, w_b, r_e, r_b):
    """Palauttaa (ajelehtinut osake %, ajelehtinut korko %, markkinavaikutus osake %-yks., korko %-yks.). r = desimaali."""
    w_o = 100.0 - w_e - w_b
    tot = w_e * (1 + r_e) + w_b * (1 + r_b) + w_o
    de, db = 100.0 * w_e * (1 + r_e) / tot, 100.0 * w_b * (1 + r_b) / tot
    return de, db, de - w_e, db - w_b

def _month_end(d):
    y, m = int(d[:4]), int(d[5:7]); return f'{d[:7]}-{calendar.monthrange(y, m)[1]:02d}'

def prev_month_end(d):
    """Edellisen kalenterikuukauden viimeinen päivä (2026-10-31 → 2026-09-30)."""
    y, m = int(d[:4]), int(d[5:7])
    if m == 1: y, m = y - 1, 12
    else: m -= 1
    return f'{y}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}'

def month_steps(start_d, end_d):
    """Kuukausien määrä start_d:n kuukauden jälkeen end_d:n kuukauteen (09-30→10-31 = 1, 06-30→10-31 = 4)."""
    y, m = int(start_d[:4]), int(start_d[5:7])
    n = 0
    while True:
        m += 1
        if m == 13: y, m = y + 1, 1
        k = f'{y}-{m:02d}'
        if k > end_d[:7]: break
        n += 1
    return n

def etf_returns(prev_as_of, cur_as_of, rows=None):
    """{'equity': {...}, 'bond': {...}} tai (None, syy)."""
    rows = rows if rows is not None else benchmark.load()
    by = {r['month']: r for r in rows}
    for d in (prev_as_of, cur_as_of):
        r = by.get(d[:7])
        if d != _month_end(d) and not (r and r['month_end_date'] == d):
            return None, f'Havaintopäivä {d} ei ole kuukauden loppu; ETF-tuottoja on tallessa vain kuukauden loppukursseista – markkinavaikutusta ei laskettu.'
    if prev_as_of[:7] not in by:
        return None, f'ETF-kurssi puuttuu lähtöpäivältä {prev_as_of} – markkinavaikutusta ei laskettu.'
    months, y, m = [], int(prev_as_of[:4]), int(prev_as_of[5:7])
    while True:
        m += 1
        if m == 13: y, m = y + 1, 1
        k = f'{y}-{m:02d}'
        if k > cur_as_of[:7]: break
        months.append(k)
    if not months: return None, 'Ei kuukausiväliä – markkinavaikutusta ei laskettu.'
    miss = [k for k in months if k not in by]
    if miss: return None, f'ETF-kuukausituotto puuttuu: {", ".join(miss)} – markkinavaikutusta ei laskettu.'
    nonv = [k for k in months if by[k]['bond_source'] != 'VAGF.DE']
    if nonv: return None, f'Korko-ETF:n tuotto kuukausille {", ".join(nonv)} on proxy, ei VAGF – markkinavaikutusta ei laskettu.'
    out = {}
    for side, (name, isin, tk, col) in ETF.items():
        p = 1.0
        for k in months: p *= 1 + float(by[k][col])
        out[side] = {'etf': name, 'isin': isin, 'ticker': tk, 'currency': 'EUR', 'return_pct': round((p - 1) * 100, 4),
                     'from_close': by[prev_as_of[:7]]['month_end_date'], 'to_close': by[cur_as_of[:7]]['month_end_date'],
                     'months': months, 'monthly_returns': {k: float(by[k][col]) for k in months}, 'source': SRC}
    return out, None

def market_drift(ch, prev, rows=None, *, month_end):
    """ch = allocation_change_vs_prev, prev = viimeisimmät tunnetut painot ennen snapshotia, month_end = snapshotin kuun loppu.

    ETF-tuottoikkuna on aina prev_month_end(month_end) → month_end (edellinen kalenterikuukausi).
    """
    base_date = prev.get('as_of') or ch.get('prev_as_of')
    period_m = month_steps(ch['prev_as_of'], ch['cur_as_of']) if ch.get('prev_as_of') and ch.get('cur_as_of') else None
    win_from, win_to = (prev_month_end(month_end), month_end) if month_end else (None, None)
    md = {'method': METHOD, 'formula': 'w_e(1+r_e) / (w_e(1+r_e) + w_b(1+r_b) + w_o); w_o = 100 - w_e - w_b, r_o = 0',
          'base_date': base_date, 'drift_window': {'from': win_from, 'to': win_to},
          'change_period_months': period_m,
          'prev_weights': {'equity_pct': prev.get('equity_pct'), 'fixed_income_pct': prev.get('fixed_income_pct'),
                           'other_pct_assumed': None, 'as_of': prev.get('as_of'), 'source': prev.get('source'), 'source_url': prev.get('source_url')},
          'status': 'unavailable', 'equity_pp': None, 'fixed_income_pp': None, 'residual_equity_pp': None, 'residual_fixed_income_pp': None}
    w_e, w_b = prev.get('equity_pct'), prev.get('fixed_income_pct')
    if w_e is None or w_b is None:
        md['reason'] = 'Edellisen havainnon osake- tai korkopaino puuttuu – markkinavaikutusta ei laskettu.'; return md
    if w_e + w_b > 100.0001:
        md['reason'] = f'Edellisen havainnon osake + korko = {w_e + w_b:.2f} % > 100 % – markkinavaikutusta ei laskettu.'; return md
    md['prev_weights']['other_pct_assumed'] = round(100.0 - w_e - w_b, 4)
    if not month_end:
        md['reason'] = 'Snapshotin kuun loppua ei annettu – markkinavaikutusta ei laskettu.'; return md
    rets, why = etf_returns(win_from, win_to, rows)
    md['etf_returns'] = rets
    if rets is None:
        md['reason'] = why; return md
    de, db, me, mb = drift(w_e, w_b, rets['equity']['return_pct'] / 100, rets['bond']['return_pct'] / 100)
    md.update({'status': 'computed', 'drifted_equity_pct': round(de, 2), 'drifted_fixed_income_pct': round(db, 2),
               'equity_pp': round(me, 2), 'fixed_income_pp': round(mb, 2)})
    comparable = period_m == 1
    if not comparable:
        md['residual_blank_reason'] = (f'Toteutunut muutos on {period_m} kk ({ch.get("prev_as_of")}–{ch.get("cur_as_of")}), '
                                       f'markkinavaikutus lasketaan aina yhdeltä kuukaudelta ({win_from}–{win_to}); '
                                       f'aktiivinen/muu ei ole vertailukelpoinen.')
    elif ch.get('equity_pp') is not None:
        md['residual_equity_pp'] = round(ch['equity_pp'] - me, 2)
    if comparable and ch.get('fixed_income_pp') is not None:
        md['residual_fixed_income_pp'] = round(ch['fixed_income_pp'] - mb, 2)
    return md
