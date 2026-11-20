# 2026-10 r017 – juoksevat kulut Morningstarin quote-sivulta

Käyttäjä päätti 20.11.2026, että tasapainovertailun juoksevat kulut (TER) otetaan Morningstarin rahastosivun **Ongoing Cost / Ongoing Costs** -kentästä.

Lähdeaineisto: samana päivänä (20.11.2026, n. 9.09–9.15 Europe/Helsinki) luetut Morningstar Global quote-sivut (`quotes.js`; sivun teksti + sal-service `onGoingCharge` / `onGoingChargeDate`). Sivun "Ongoing Costs" -luku ja API-kenttä täsmäsivät kaikilla luetuilla rahastoilla. Osuussarjat varmistettiin ISIN-tunnuksella ja sivun otsikolla.

Päivitetty 23 aktiivista rahastoa. Sulautunutta n16 (Nordea Stable Return) ei päivitetty. SPYI 0,17 % ja VAGF 0,08 % tarkistettiin samoista sivuista; arvot ennallaan, ETF-metaa ei muutettu (`stage_snapshot.py` hyväksyy ETF:lle vain `bond_metrics`).

Huomioita:
- UB Smart I (n5): sivun Ongoing Costs 4,32 % (as of 2026-03-09). Related Investments -taulukossa erillinen Performance Fee % on I-sarjalla "–" ja A-sarjalla 0,00; molempien Ongoing Cost on 4,32. Aiempi screener-arvo oli 1,64.
- Säästöpankki Tasapainoinen B (n21, FI4000278676) 1,55 % ja D (n23, FI4000517719) 0,95 %, molemmat as of 2026-10-30. Sarjat luettiin omilta sivuiltaan; arvot eivät ole samat. Aiempi screener antoi molemmille 1,11.
- Alexandria (n8): Morningstar 1,90 % (as of 2026-09-14); yhtiön sivu on aiemmin ilmoittanut 1,87 %.
- SPYI: luettu osoitteesta `.../etfs/0P0000TKW7/quote` (sama ISIN IE00B3YLTY66 kuin `etfs[].ms_url`). Snapshotin `SPYI_meta.source_url` osoittaa `.../0P0000TKVG/quote`; kulu 0,17 % ennallaan, URL-eroa ei muutettu tässä revisiossa.
