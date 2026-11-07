"""Kertaluonteinen: schema 2 -kentät, sulautumismetatieto ja olemassa olevien snapshotien r001-arkisto."""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import stage_snapshot as S
h = json.load(open(S.HIST))
f16 = next(f for f in h['funds'] if f['isin'] == 'FI0008810254')
f16.update(status='merged', merged_on='2026-11-06', last_trading_day='2026-11-03',
  successor={'name': 'Nordea 1 – Stable Return Fund', 'isin': 'LU0227384020', 'share_class': 'BP-EUR',
             'isin_source': 'Morningstar lt.morningstar.com screener: LU0227384020 = "Nordea 1 - Stable Return BP EUR"; ISIN ei mainittu Nordean ilmoituksessa'},
  merger_source_url='https://www.nordeafunds.com/fi/news/ilmoitus-nordea-vakaa-tuotto-ja-nordea-1-stable-return-fund-rahastojen-osuudenomistajille-1.10.2026',
  merger_note='Nordea Vakaa Tuotto sulautui Nordea 1 – Stable Return Fundiin 6.11.2026. Historia säilytetään; vastaanottavan rahaston tuottoja ei yhdistetä tähän sarjaan.',
  stitch_successor_returns=False)
for s in h['snapshots']:
    if s.get('revisions'): continue
    s['month_end'] = {'2026-08': '2026-08-31', '2026-09': '2026-09-30'}[s['period']]
    s['returns_status'] = 'published' if s.get('return_date') else 'none'
    S.coverage(h, s)
    S.save_revision(h, s, 'Arkistoitu schema 2 -siirrossa (aiemmat versiot git-historiassa, viimeisin commit 8e9b68b)')
h['schema_version'] = 2
h['description'] = 'Tasapainorahastojen kuukausivertailu vs. 50/50 ETF (SPYI+VAGF). Snapshots lisätään perään, ei ylikirjoiteta. Kenttäkuvaus: SCHEMA.md.'
json.dump(h, open(S.HIST, 'w'), ensure_ascii=False, indent=1)
print([(s['period'], s['content_coverage']) for s in h['snapshots']])
