# 2026-10 r016 – kuun 20. päivän tarkistus (20.11.2026)

Ajo: 20.11.2026 n. klo 9.00–9.20 (Europe/Helsinki). Morningstar Global (en-nd) julkiset portfolio- ja quote-sivut headless Chromella
(sama menetelmä kuin r014: `method/scrape.js`, `method/quotes.js`, `method/parse.py`, `method/build_batch.py`, `method/make20.py`).
Huom: headless Chromen oletus-UA sai CloudFront 403 -eston; ajettiin tavallisella Chrome-UA:lla (ei kirjautumista). n11:n ensimmäinen luenta ei avannut Bond-välilehteä
(`portfolio_raw/n11_attempt1_bondtab_failed.json`); luettu uudelleen onnistuneesti.

## Uutta
- n19 Obsido Global Balanced A2: Morningstar Holdings/Measures/Exposure Analysis 31.10.2026. Allokaatio net 56,94 / 28,51 / kassa 4,50 / muu 10,04 / pref 0,01 / conv 0,01
  (ennen MS 30.9. 57,11 / 28,35). Effective Duration 4,40 (31.10.; ennen 4,26 30.9.); YTW-riviä ei ole. Taulukot 31.10. → arvio duraatio 4,45 (kattavuus 94,1 %), YTW 5,33 % (92,0 %).
  Obsidon virallinen fact sheet 30.9.2026 (julkaistu /2026/11/; osakkeet 52,9, korot 32,4, muut 14,7) on vanhempi kuin MS 31.10. → ei käytetty; 31.10. fact sheetia ei löytynyt.
- n2/n4 Nordea Premium I/P ja n3 Säästö 50: Fixed Income Exposure Analysis 30.9.2026 (ennen 31.8.). Arviot: Premium duraatio 4,66→4,74 (79,1→81,2 %), YTW 4,48→5,04 % (98,0→97,4 %);
  Säästö 50 duraatio 4,97→4,94 (79,0→79,2 %), YTW 4,27→4,76 % (98,4→98,2 %). Taulukoiden painot summautuvat 96,25 % / 89,02 %:iin (caveat tallennettu).
- n24 OP-Tavoite 3A: Morningstar muutti 31.10. taulukon soluarvoja (sama päivä). Uusi luenta tallennettu; edelliset arvot `exposure_tables_superseded`-kentässä ja r015-arkistossa. Arvio duraatio 4,19→4,21, YTW 4,56 ennallaan.
- Rahastokoot (Morningstar quote fundSize = surveyedFundSize ±1 %, päivä uudempi): n7, n9, n12, n14, n15, n21, n23, n24. Ei päivitetty: n5 (fundSize ja surveyed eroavat), n8 (ristiriitainen, r014), n20 (surveyed 1 597,6).

## Ennallaan (tarkistettu 20.11.)
- Nordea factsheetit (I, P, Säästö 50, Vastuullinen Tasapaino): edelleen "Perustuu rahaston sijoituksiin 30.09.2026".
  Morningstar n2/n3/n4 nyt 30.9. (n2/n4 net 62,22/39,71, long 67,41/40,74; n3 54,56/48,35) = sama päivä kuin factsheet → factsheet säilyy (ei uudempaa lähdettä).
- n17 MS 30.9. (76,14/26,32, epäuskottava kuten aiemmin). n12 Danske MS 30.9. ja factsheet "10 suurinta omistusta per 30.09.2026". n11 Evli MS 30.9. (78,79/19,99, epäuskottava). n15 POP MS 30.9. (99,8 % muut). n13 S-Pankki MS 31.10. 92,11 (virheellinen, liputettu). n22 Aktia MS 98,1 % muut (30.9.).
- Raportoidut ED-arvot ennallaan: n6 3,77 (31.10.), n9 4,47 (31.10.), n11 2,71 (30.9.), n15 4,65 (30.9.), n17 2,67 (30.9.), n24 4,38 (31.10.), VAGF 5,99 (30.9.). YTW-riviä ei millään (checked_absent).
- VAGF taulukot ja mittarit 30.9. (ei 31.10. vielä).
- Juoksevat kulut: ei muutettu (quote-sivun onGoingCharge poikkeaa monella aiemmasta screener-arvosta – raportoitu käyttäjälle, ei vaihdettu menetelmää).

## Tarkistussummat (sha256)
- danske.pdf 7f192cebd836ae52714d83410969574a0e19f0197a622d6b60d10a203c2fc31b
- nordea_FI0008806419.pdf 7f369f065dd02390f8932172c8287c3f02e03ef71a250ea1b6b3d73a35181a19
- nordea_FI0008806807.pdf 3dd94117b1b7a2da10a097ec8489124579548f5fc163e546f3f9535b7ca23ed6
- nordea_FI4000171178.pdf de9bdb4e8849a1e2ed0db9e10bc380dd4279c0ffc323612453fa3787c61a7248
- nordea_FI4000400098.pdf 0e90cd48ca8062949fcbc93fc334c29efeb85a8ae305fbb211cde67b41854e2a
- Fact-Sheet-OGB-A2-30.9.2026.pdf faf2a41ad676b312bb430ac2ff1acf26c5820d01a07b773ca2c820d9a30a8f0b
- bond_tables_batch10_all.json d2d83ef67f3bc42921422c4a60c5789e62216c0ea72d5db7827a9bbe75036a22
- updates_r016.json 78379dc81cde1d544f6ca5fa3df82d3542547989ae4ce65d1d9f3e682e299688
