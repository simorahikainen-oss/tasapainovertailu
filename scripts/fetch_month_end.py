#!/usr/bin/env python3
"""Hakee kuun lopun (month-end) tuotot ja Morningstar-feedin metatiedot.

Käyttö: python3 scripts/fetch_month_end.py 2026-10
Kirjoittaa data/raw/<kausi>/ (raakavastaukset) ja data/staging/<kausi>.json.
Tuotot lasketaan Morningstarin päiväkohtaisesta kumulatiivisesta
kokonaistuottosarjasta kuun viimeisen arvon kohdalta. Screenerin ReturnM0/ReturnM12
EIVÄT ole kuun lopun lukuja (ne päivittyvät päivittäin) eikä niitä käytetä tuottoina.
"""
import json, sys, csv, datetime as dt, urllib.request, urllib.parse, calendar, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
KEY = 'klr5zyak8x'
UA = {'User-Agent': 'Mozilla/5.0'}
ETF_IDS = {'SPYI': ('IE00B3YLTY66', '0P0000TKW7'), 'VAGF': ('IE00BG47KH54', '0P0001HSBO')}
YAHOO = {'SPYI': 'SPYI.DE', 'VAGF': 'VAGF.DE'}

def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))

def month_end(period):
    y, m = map(int, period.split('-'))
    return dt.date(y, m, calendar.monthrange(y, m)[1])

def add_years(d, n):
    try: return d.replace(year=d.year + n)
    except ValueError: return d.replace(year=d.year + n, day=28)

def screener(isins):
    dp = 'SecId|Name|Isin|PortfolioDate|ClosePriceDate|OngoingCharge|FundTNAV|FundTNAVDate|CategoryName|AssetAllocEquity|ReturnM0|ReturnM12'
    q = dict(page=1, pageSize=100, outputType='json', version=1, languageId='fi-FI', currencyId='EUR',
             universeIds='FOALL$$ALL', securityDataPoints=dp, filters='Isin:IN:' + ':'.join(isins))
    return get(f'https://lt.morningstar.com/api/rest.svc/{KEY}/security/screener?' + urllib.parse.urlencode(q))

def cumret(secid, start, end):
    u = (f'https://lt.morningstar.com/api/rest.svc/timeseries_cumulativereturn/{KEY}?id={secid}&currencyId=EUR'
         f'&idtype=Morningstar&frequency=daily&startDate={start}&endDate={end}&outputType=COMPACTJSON')
    s = get(u)
    return {(dt.date(1970, 1, 1) + dt.timedelta(days=t // 86400000)).isoformat(): v for t, v in s}

def value_at(series, d):
    """Viimeisin arvo päivänä d tai ennen (enintään 7 pv taaksepäin)."""
    for k in range(8):
        x = (d - dt.timedelta(days=k)).isoformat()
        if x in series: return series[x], x
    return None, None

def returns_from(series, me):
    out, dates = {}, {}
    end, endd = value_at(series, me)
    if end is None: return None
    dates['end'] = endd
    refs = {'ytd': dt.date(me.year - 1, 12, 31), 'y1': add_years(me, -1), 'y3': add_years(me, -3), 'y5': add_years(me, -5), 'y10': add_years(me, -10)}
    yrs = {'ytd': None, 'y1': None, 'y3': 3, 'y5': 5, 'y10': 10}
    for k, d in refs.items():
        v, vd = value_at(series, d)
        if v is None: out[k] = None; continue
        r = (1 + end / 100) / (1 + v / 100)
        out[k] = round(((r ** (1 / yrs[k])) - 1) * 100 if yrs[k] else (r - 1) * 100, 2)
        dates[k] = vd
    return out, dates

def yahoo_month_close(sym, me):
    p1 = int(dt.datetime(me.year, me.month, 1).timestamp()) - 40 * 86400
    p2 = int(dt.datetime(me.year, me.month, me.day).timestamp()) + 3 * 86400
    d = get(f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1={p1}&period2={p2}&interval=1d')['chart']['result'][0]
    q = d['indicators']; c = q['adjclose'][0]['adjclose'] if 'adjclose' in q else q['quote'][0]['close']
    pts = sorted((dt.datetime.fromtimestamp(t, dt.timezone.utc).date(), v) for t, v in zip(d['timestamp'], c) if v is not None)
    cur = [p for p in pts if p[0] <= me and p[0].month == me.month]
    prev = [p for p in pts if p[0] < dt.date(me.year, me.month, 1)]
    return prev[-1], cur[-1]

def main(period):
    me = month_end(period)
    if dt.date.today() <= me: sys.exit(f'{period} ei ole vielä päättynyt')
    h = json.load(open(ROOT / 'history.json'))
    raw = ROOT / 'data' / 'raw' / period; raw.mkdir(parents=True, exist_ok=True)
    funds = [f for f in h['funds'] if f.get('status') != 'merged' or (f.get('merged_on') or '9999') > me.isoformat()]
    sc = screener([f['isin'] for f in h['funds']]); json.dump(sc, open(raw / 'screener.json', 'w'), ensure_ascii=False, indent=1)
    rows = {r['Isin']: r for r in sc['rows']}
    start = add_years(me, -10) - dt.timedelta(days=10)
    st = {'period': period, 'month_end': me.isoformat(), 'fetched_at': dt.datetime.now().astimezone().isoformat(timespec='seconds'),
          'returns_method': 'Morningstar timeseries_cumulativereturn (päivä, EUR, kokonaistuotto), arvo kuun viimeisenä päivänä tai sitä edeltävänä noteerauspäivänä; 3v/5v/10v p.a.',
          'funds': {}, 'etfs': {}, 'missing': []}
    for f in h['funds']:
        r = rows.get(f['isin']); e = {'n': f['n'], 'isin': f['isin']}
        secid = (r or {}).get('SecId') or (f.get('ms_secid'))
        if r:
            e['feed'] = {k: r.get(k) for k in ('SecId', 'Name', 'PortfolioDate', 'ClosePriceDate', 'OngoingCharge', 'FundTNAV', 'FundTNAVDate', 'CategoryName', 'AssetAllocEquity')}
        if secid:
            s = cumret(secid, start, me + dt.timedelta(days=1))
            res = returns_from(s, me)
            if res and res[1]['end'] >= (me - dt.timedelta(days=5)).isoformat():
                e['returns'], e['return_dates'] = res
        if 'returns' not in e: st['missing'].append(f['n'])
        st['funds'][str(f['n'])] = e
    for k, (isin, sid) in ETF_IDS.items():
        s = cumret(sid, start, me + dt.timedelta(days=1)); res = returns_from(s, me)
        st['etfs'][k] = {'isin': isin, 'secid': sid, 'returns': res[0], 'return_dates': res[1]}
        (p0, p1) = yahoo_month_close(YAHOO[k], me)
        st['etfs'][k]['xetra'] = {'prev': [p0[0].isoformat(), p0[1]], 'cur': [p1[0].isoformat(), p1[1]], 'month_ret': p1[1] / p0[1] - 1}
    json.dump(st, open(raw / 'staging_input.json', 'w'), ensure_ascii=False, indent=1)
    (ROOT / 'data' / 'staging').mkdir(exist_ok=True)
    json.dump(st, open(ROOT / 'data' / 'staging' / f'{period}.json', 'w'), ensure_ascii=False, indent=1)
    print(f"{period}: tuotot {len(st['funds']) - len(st['missing'])}/{len(st['funds'])}, puuttuu {st['missing']}")

if __name__ == '__main__':
    main(sys.argv[1])
