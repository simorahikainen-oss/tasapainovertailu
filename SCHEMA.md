# history.json – schema 2

Tietokanta, jota sivusto lukee osoitteesta `https://raw.githubusercontent.com/simorahikainen-oss/tasapainovertailu/main/history.json`.
Kaikki muutokset ovat lisääviä: schema 1 -kentät säilyvät, joten vanha käyttöliittymä ja Excel-vienti toimivat.

## Ylätaso
- `schema_version`: 2
- `funds[]`: rahastojen perustiedot (`n`, `name`, `isin`, `ms_url`, `company_url`, `link_status`, …).
  Sulautuneilla lisäksi `status: "merged"`, `merged_on`, `last_trading_day`, `successor{name,isin,share_class,isin_source}`,
  `merger_source_url`, `merger_note`, `stitch_successor_returns: false`.
- `etfs[]`: SPYI ja VAGF.
- `snapshots[]`: yksi per kuukausi (`period` = `YYYY-MM`), nousevassa järjestyksessä. Vanhoja kuukausia ei poisteta.

## Snapshot
- `period`, `month_end` (kuun viimeinen päivä), `return_date` (= month_end, kun tuotot julkaistu; null jos ei tuottoja)
- `returns_status`: `published` | `none`; `returns_published_at`; `returns_method`
- `content_status`: `complete` (kaikkien tukikelpoisten rahastojen sisältö kuun lopulta) | `partial`
- `content_coverage`: `{funds_total, eligible, current_month_end, as_of_min, as_of_max, by_as_of{päivä: lkm}}`
- `benchmark`: `SPYI`, `VAGF` (Morningstar NAV ytd/y1), `etf_50_50`, `etf_50_50_rebalanced` (ytd…y10, kk-rebalansointi Xetra),
  `SPYI_px`, `VAGF_px`, `SPYI_meta`, `VAGF_meta`, `xetra_month_close`
- `revision` (nykyinen numero) ja `revisions[]`: `{revision, saved_at, path, summary}`; `path` = `revisions/<period>/rNNN.json`
  on koko snapshotin kopio sellaisena kuin se oli tallennettaessa (ilman `revisions`-listaa). Uusin revisio = snapshot itse.
- `backfill: true` = jälkikäteen koottu edellinen allokaatiotieto (2026-08).

## Rahasto snapshotissa (`funds[]`)
- `returns {ytd,y1,y3,y5,y10,as_of,source,method}` – aina kuun lopulta (`as_of == month_end`). null + `returns_missing` (syy), jos ei saatavilla.
- `vs_50_50 {ytd,y1}`, `vs_50_50_rebalanced {ytd…y10}` – rahaston tuotto miinus vertailusalkku, %-yks.
- `allocation_primary {equity_pct, fixed_income_pct, other_pct, as_of, source, source_url, note, carried_from_period?}` – käytettävä sisältö.
  `as_of` on sisällön todellinen päivä; `carried_from_period` = tieto on siirretty aiemmasta snapshotista ilman muutosta.
- `allocation` – schema 1 -yhteensopiva kopio.
- `allocation_morningstar_feed {equity_net_pct, portfolio_date, source, fetched_at}` – Morningstar-screenerin osakepaino (vain netto-osake,
  ei korko-/kassaerittelyä). Ei korvaa `allocation_primary`-arvoa automaattisesti.
- `allocation_change_vs_prev` – vain kun sisällön `as_of` muuttui; muuten null.
- `flags[]`: `{type, note}`; tyypit `allocation_stale` (sisältö ei kuun lopulta), `feed_divergence` (feedin uudempi osakepaino poikkeaa > 5 %-yks.).
- `costs`, `features`, `explanation`, `text_from_period` (miltä kuulta kuvausteksti on).

## Keskimääräinen osakepaino (kaavio)
Kullekin snapshotille: tasapainoinen (equal weight) keskiarvo `allocation_primary.equity_pct`-arvoista niiltä rahastoilta, joilla arvo on ja jotka
eivät ole sulautuneet viimeistään `month_end`-päivänä. ETF:t eivät ole mukana. Kaksi sarjaa: kaikki (viimeisin saatavilla oleva sisältö) ja
vain kuun lopun sisältö (`as_of == month_end`). Kuukautta ei piirretä, jos yhdenkään rahaston sisältö ei ole kyseiseltä kuulta (paitsi `backfill`).
Ei interpolointia.

## Päivitysprosessi
1. Kuun päätyttyä: `python3 scripts/fetch_month_end.py YYYY-MM` → `data/raw/YYYY-MM/`, `data/staging/YYYY-MM.json`
2. `python3 scripts/stage_snapshot.py returns YYYY-MM` → tuotot, vertailu, kulut; sisältö siirretään aiemmasta päivämäärineen; uusi revisio.
3. Kun sisältöä ilmestyy (Morningstarin täysi allokaatio tai yhtiön raportti): kirjoita `updates.json`
   (`[{"n":7,"allocation_primary":{...,"as_of":"YYYY-MM-DD","source_url":"..."},"features":"..."}]`) ja aja
   `python3 scripts/stage_snapshot.py content YYYY-MM updates.json` → uusi revisio.
4. `python3 tests/test_history.py` ennen pushia.

Tuottoina EI käytetä screenerin `ReturnM0`/`ReturnM12`-kenttiä: ne päivittyvät päivittäin eivätkä ole kuun lopun lukuja.
