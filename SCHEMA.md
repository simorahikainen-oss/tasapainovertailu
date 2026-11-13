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
- `costs`, `features`, `explanation`, `text_from_period` (miltä kuulta kuvausteksti on), `text_note` (r012: miten teksti tarkistettiin; tekstit eivät toista painoja, kuluja tai kokoa, jotka ovat omissa sarakkeissaan). Pelkät tekstimuutokset: `stage_snapshot.py texts`.
- `costs`: `ongoing_cost_pct`, `fund_size` (valuutan yksiköissä, ei miljoonissa), `fund_size_currency`, `fund_size_as_of`, `source`, `source_url`, `fetched_at`, `note?`.
  `fund_size_type`: `"fund"` (Morningstar Fund Size, koko rahasto) tai `"share_class"` (vain osuussarjan koko / Share class size). Puuttuva tyyppi = aiempi FundTNAV, joka on rahastotasoinen. Ensisijainen on rahastokoko; osuussarjan koko vain jos rahastokokoa ei ole, ja se merkitään tyypillä sekä UI:ssa ("osuussarja") että Excelin Koko-tyyppi-sarakkeessa. Puuttuva koko = null (ei 0). Taulukko näyttää `round(fund_size/1e6)`; alle 0,5 M jätetään tyhjäksi, jotta virheellinen pieni FundTNAV ei näy nollana.


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

## bond_metrics (rahasto snapshotissa, valinnainen)
`{scope: "fixed_income_sleeve"|"whole_fund", method: "reported", source, source_url, note?,
  effective_duration_years: {value|null, as_of|null, label: "Effective Duration"},
  yield_to_worst_pct: {value|null, as_of|null, label: "Yield to Worst"}}`
- Vain suoraan raportoidut luvut (Morningstarin taulukko / yhtiön raportti). Ei painotettuja laskelmia eikä arvioita.
- Puuttuva = null (ei 0). YTM, current yield ja modified duration eivät kelpaa (label tarkistetaan). scope ilmoitetaan, ei oleteta.
- Mittarikohtainen as_of. Syöte `stage_snapshot.py content` -tiedostossa `{"n":..,"bond_metrics":{...}}`, voi olla ilman allokaatiota.

### method "weighted_table_calculation" (sallittu 7.11.2026 käyttäjän luvalla)
`table: {effective_duration_years|yield_to_worst_pct: {as_of, source_url, table_name, unit, weight_basis, rows:[{label, weight_pct, value|null, lower|null, upper|null}], coverage_pct, rows_without_exact_value, calc_note}}`
- Lasketaan vain, jos kaikilla riveillä on tarkka `value`; välejä/avoimia päitä ei muuteta keskipisteiksi → muuten arvo null ja rivit tallessa.
- Suoraan raportoitu Effective Duration on ensisijainen.

### Tarkistustila ja raakataulukot
- `bond_metrics` on vain rahastoilla, joiden lähde on tarkistettu (`checked_at`, `as_of_label`). Puuttuva `bond_metrics` = ei tarkistettu (UI: tyhjä, title "ei tarkistettu"); `value: null` + `checked_at` = tarkistettu, lähde ei ilmoita.
- `exposure_tables.{effective_duration|yield_to_worst}`: Morningstarin "Fixed Income Exposure Analysis" -taulukko sellaisenaan: `heading, as_of, as_of_label, basis` (esim. long positions), `scope` (näkyvästä otsikosta, muuten "unknown"), `cell_unit, columns, rows, values (null = '–'), subtotal_weight, source_url`.
- Taulukoista laskettua arviota EI tallenneta tarkkoihin kenttiin. Mahdollinen havainnollistava arvio vain erilliseen `illustrative_estimates`-kenttään käyttäjän hyväksynnällä.

### Vertailu-ETF:n korkomittarit
`benchmark.VAGF_bond_metrics` (ja mahdollinen `SPYI_bond_metrics`): sama rakenne kuin rahaston `bond_metrics`. Syöte `{"n":"VAGF","bond_metrics":{...}}`.
### Selaimen taulukkobatchin tuonti
`python3 scripts/import_bond_tables.py <bond_tables_batchN.json> <updates.json>` → `stage_snapshot.py content`. Raportoidut luvut `direct_measures`-kentästä (`effective_duration`, `yield_to_worst`, `as_of_label` "Investment as of Mon DD, YYYY", `scope`); muuten null. Taulukon päivä footnotesta.

### 50/50 ETF-salkun korkomittarit
Ei omaa kenttää: käyttöliittymä näyttää 50/50-rivillä `benchmark.VAGF_bond_metrics`-arvot sellaisenaan korko-osuuden (VAGF) mittareina, ei kerrottuna 0,5:llä eikä koko salkun riskimittareina. Revisioissa ilman VAGF_bond_metrics-kenttää solut jäävät tyhjiksi.

## allocation_change_vs_prev.market_drift (r010:stä, 10.11.2026; ikkuna r013:sta 13.11.2026)
Painomuutoksen markkinavaikutus (passiivinen ajelehtiminen), `scripts/market_drift.py`; `stage_snapshot.py content` laskee sen automaattisesti uusille muutoksille, `stage_snapshot.py drift YYYY-MM` jälkikäteen uutena revisiona.
- ETF-tuottoikkuna on aina sama kaikille rahastoille: edellinen kalenterikuukausi, `drift_window {from, to}` = edellisen kuun loppu → snapshotin `month_end` (esim. 2026-09-30–2026-10-31). Ei rahaston omaa havaintoväliä.
- Lähtöpainot `prev_weights {equity_pct, fixed_income_pct, other_pct_assumed = 100 - e - b, as_of, source, source_url}` ja `base_date` (= `prev_weights.as_of`): edellisen kuun lopun painot jos saatavilla, muuten viimeisimmät tunnetut aiemmat painot (päivä merkitään, ei arvioida). Muu-osuuden tuotto 0 %.
- `etf_returns.{equity,bond}`: SPYI / VAGF, EUR, Xetra kuukauden päätöskurssit (`data/benchmark_monthly.csv`, sama sarja kuin `SPYI_px`/`VAGF_px`): `return_pct`, `from_close`, `to_close`, `months[]`, `monthly_returns{}`, `source`.
- Ajelehtinut osake = w_e(1+r_e) / (w_e(1+r_e) + w_b(1+r_b) + w_o), korko vastaavasti → `drifted_equity_pct`, `drifted_fixed_income_pct`.
- `equity_pp`, `fixed_income_pp` = ajelehtinut − lähtöpaino (%-yks.).
- `change_period_months` = toteutuneen painomuutoksen pituus kalenterikuukausina (`prev_as_of`→`cur_as_of`; 09-30→10-31 = 1, 06-30→10-31 = 4). `residual_equity_pp`, `residual_fixed_income_pp` = toteutunut muutos − markkinavaikutus (aktiivinen/muu) vain kun `change_period_months == 1`; muuten null + `residual_blank_reason`.
- `status`: `computed` | `unavailable` (+ `reason`; arvot null). Tyhjä, jos ETF-kuukausituotto puuttuu ikkunalle, korko-ETF:n tuotto on proxy tai lähtöpaino puuttuu. Ei arvioituja tuottoja. Lähtöpäivän ei tarvitse olla kuun loppu.
- UI: muutossolun alle pienellä ja haalealla "markkina ±x,xx"; menetelmä, ETF-tuotot, ikkuna, lähtöpäivä ja aktiivinen/muu tooltipissä (tyhjä residuaali: ei vertailukelpoinen). Excel: "Osake Δ markkina (%-yks.)", "Osake Δ aktiivinen/muu (%-yks.)", "Korko Δ markkina (%-yks.)", "Korko Δ aktiivinen/muu (%-yks.)", "Markkinavaikutuksen perusteet".
