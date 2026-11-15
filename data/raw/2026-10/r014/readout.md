# r014 – täysi kuukausiajo 15.11.2026 (kausi 2026-10)

## Menetelmä
- Morningstar Global (en-nd) julkiset portfolio- ja quote-sivut luettiin headless Chromella (ei kirjautumista) – `method/scrape.js`, `method/quotes.js`.
  Portfolio: Bond-välilehti, Asset Allocation (Net/Short/Long), Fixed Income Measures (Investment-sarake + "As of" -rivi), Fixed Income Exposure Analysis
  (Effective Duration ja Yield To Worst × Credit Rating) taulukkonäkymänä, molemmat sivut (Next), arvot DOM-tekstistä (ei visuaalista transkriptiota).
  Raakasisältö: `portfolio_raw/<n>.json` (koko sivuteksti Equity- ja Bond-välilehdiltä, taulukkosolut, footnotet).
- Tarkistus: 21 rahaston + VAGF:n taulukot täsmäsivät solu soluun aiemmin tallennettuihin (sama as_of) → lukutapa validoitu; muutokset vain n5, n6 (31.10.).
- Quote: Fund Size / Share Class Size, Ongoing Costs, Category (sivuteksti) ja sivun itse lataama quote-JSON (`quote_raw/`).
- lt.morningstar.com screener API palautti 15.11.2026 HTTP 401 → juoksevia kuluja (screener OngoingCharge) ei voitu päivittää samasta lähteestä.
  Morningstar Global "Ongoing Costs" on eri datapiste; sitä ei käytetty olemassa olevien kulujen korvaamiseen (paitsi Finlandia n18, jolta kulu puuttui).
- Tuotot 31.10.2026 tarkistettu uudelleen (`returns_recheck_20261115.json`, timeseries_cumulativereturn): kaikki julkaistut arvot ennallaan.
- Linkit: `links_20261115.txt` (check_links.py). Rikki: n16 Nordea Vakaa Tuotto (sulautunut 6.11.2026) yhtiösivu 404 – ei korvattu seuraajalla.

## Yhtiöraportit
- UB Smart kuukausiraportti lokakuu 2026 (s. 3 kaavio, `company/ub_smart_202610_s3_omaisuusluokat.png`): Osakkeet 33,2 / Korko 33,5 / Reaaliomaisuus 32,0 / Käteinen 1,3.
- Aktia Varainhoitosalkku 50 kuukausiraportti 31.10.2026: osakkeet 51,6 / korot 46,2 / käteinen 2,2.
- Nordea factsheetit (haettu 15.11.2026): sijoitukset 30.09.2026. Vastuullinen Tasapaino 53,42/46,58/0 (käytetty n17).
  Premium I/P 54,18/40,24/5,58 ja Säästö 50 53,15/41,66/5,19 (fyysinen jakauma) – EI käytetty: n2/n4 futuurikorjattu Morningstar-linja (puolivuosikatsauksen long-futuurit) ja n3 Morningstar-linja säilytetty; lähteen vaihto olisi menetelmähyppy.
- S-Pankki VH50 kuukausikatsaus 30.10.2026: vain rahastotyyppijako (ETF 37 % luokittelematon) – ei käytetty.
- Danske Kompassi 50 factsheet: omistusanalyysi 30.9.2026 vain kaaviona; käytetty Morningstarin 30.9. taulukkoa.

## Arviot
`stage_snapshot.py` laskee `illustrative_estimates` (suljettujen välien keskipisteet, avoimet/Unk/N/A pois, kattavuus / Subtotal-summa) tallennetuista raakataulukoista.

## SHA-256
1710a6b56d161e1870a3c3eba3b86bae7827c5b059546591ec521ed7f370d84a  ub.pdf
c88f2275d34ef5dcb30b1506cc6506d26a801076db494ddcc2803d98b594ad71  aktia_vh50.pdf
5827d25bc62a3498ed74aaafa20c8c918023209cc25fa48c113e593a5dd8ebfc  nordea_FI4000400098.pdf
4cbe7a2bb77da38422cce11ba4e26e8c0c4e94e2dc0fad7fa425f6cf1ddf7115  nordea_FI4000171178.pdf
72dde406989b426e2a6d0980bd136eb58e4b74d4479ea8f40d679f561d8f5b10  nordea_FI0008806807.pdf
fc9099a4de67a9e4c269884b9cffa82a89d9f18566ed2badff48d98831438820  nordea_FI0008806419.pdf
c51cbd90362866e89e38e9c48f980858fb97538fdadb18d24243f76d7f62f280  spankki_kk.pdf
ca3d4c8694d3cacab1005d07f99971295fc5c859fd31730f64a1a0961e823b2c  danske.pdf
9dbbaa88a1866fcc5440b145c2addaf60f762c041c11931c994d850fd6f2b7fb  bond_tables_batch9_all.json
d8bdcfc5bb79b5bea2a3da3f50865ebaed54ae1e03d0a2f1316e817b6ef10601  updates_r014.json
938ff2cd2e8caaef3db8944c2b8d39e26c4b30d8a7d61c3a64ec3cff11dba035  portfolio_raw/SPYI.json
e9f0febb95c79927190c465854b788fa75a6f38af9f9ee1f6a1a5d7685d2ce1c  portfolio_raw/VAGF.json
5d93bef9f66525f7b69cdaaf529e27302b1f7123cbe7a8969153121c1bea1a65  portfolio_raw/n1.json
6f01ecaf8d10ca421a6cae3969e3d69497427e8b52bd5124f7223bbde426d0b2  portfolio_raw/n10.json
0b312517413a6f126def5aed5c77794f5a97dceb5e422e30dd37722ac131a4e6  portfolio_raw/n11.json
50aa918d4bf23bd13b819e1f5468d3ab2555555cca3f4fc4200549ef6ec15aaf  portfolio_raw/n12.json
fbaccdb431516e7a62299936c8af4d3bcfc994b13e33dcc1d102699fe6d65e83  portfolio_raw/n13.json
bfff562432eca6062633403764e717a3a56a279240be256c930a090eb3c9d645  portfolio_raw/n14.json
3067ea696e02a42a9a36860bc83800be0c258e63dc7e6cc0569b0bd1fe5e4a65  portfolio_raw/n15.json
ad969a1a3332cce87a19a1dbf9afdb870c5ec0227e0a0b5a3eb34dedb776c938  portfolio_raw/n17.json
69ec473bf24844f9c6e3d03c2a25d554ed08943be68928cc4f5559dda558f9d9  portfolio_raw/n18.json
4d8dc9b4d0fb8520beb8fdd19c90989f78a5cb277ae2525864cca2695ada7131  portfolio_raw/n19.json
9f058c785f3ed691ef2b324edb3fa6471d6534a91c1641e0e6b85ba1a3a1d2b5  portfolio_raw/n2.json
d85d81ea2a1d5613a7758f8ddd64fcb30684fdb930b222977155eb1b64f8f378  portfolio_raw/n20.json
dc4f796a9d03db5dea6cd75cba1b58ae078732b1fe64de26a1931ae640d1fe5d  portfolio_raw/n21.json
21d57489d8ca47c2fba9fb2297c61242875af201e8b4f2fb1922b2491621887d  portfolio_raw/n22.json
0277fca0fda0f54b301c5a6fd21be52991fc9b458ae187731f769bb23dc3199d  portfolio_raw/n23.json
3145613b6e91fe87ad8441fb299cd8c16eb344a121ac350b8b144a27465bc1f1  portfolio_raw/n24.json
6ee7b2a295656bef2a20bd4c636b93e607f7a7cfab5630cfe45ff5932efb62d4  portfolio_raw/n3.json
7805173834ef21152b0df89fb07c570e5cf5794ac8077e0d653676d013d7cc2d  portfolio_raw/n4.json
4f3dd04b9b1bba3251d5cf746c679a1923a27f51c4d49544135b04b081297226  portfolio_raw/n5.json
d06c40e24c8c4e164a189ecf2c4c43d5c040d72701bc81bc4bb87027a7670863  portfolio_raw/n6.json
b441234a4ed4f372cd7303d897bb51a62af9cdfe1483c4d0ca4b6d6a568a0080  portfolio_raw/n7.json
a1de6f05e1584757bbd4a16074783e296811be3f35b9016d8f2e0d546c1b3f55  portfolio_raw/n8.json
5ab05807397568793b2a2812447f39a34d71e6744e7039c6e80b32680aca4857  portfolio_raw/n9.json
0d1666a589d2148bcc90cb70dd5e1fa84be88edfc121326d6410f5da7f68dadb  quote_raw/SPYI.json
74b264c99fef9ee1edea4fc5a46d9893cef34a9d72413adb58b4909cb93f25f8  quote_raw/VAGF.json
972d7b96def5cb7ad8ecc809d45a048f545057fc54da1eb723c9e8fe019dff30  quote_raw/n1.json
83a81c5f3c9ab1cdfdf9b58d7faef8f8893e5b977c26bc93e7c719332cc4599d  quote_raw/n10.json
18a52e38cc6a574710cdb5fae0fce2f8c7bc7494f20d74c08c7ad286ed31e6ab  quote_raw/n11.json
e9897aa5332d147f9ed0f028b79bf11f6c9af07fc118841420cfb1ecb4df355a  quote_raw/n12.json
0447b0a37f8173330505df0412705f47106f2cdc1e757f725c9b26f392e11c7f  quote_raw/n13.json
0f1b72896e03004c9fdcf96cf23380ccc932357406d42f0f6c55a682a82e59dd  quote_raw/n14.json
d481b5daa15e4931246095206df40bca879c3d1dea1df6a6bdbccbd6cfb459ce  quote_raw/n15.json
068cb151664884434f9808bb64aa64f905acd24d71a9dcee66b1377eea5afa71  quote_raw/n17.json
ac4276308270b8f8082c00aac13212dba26bcda195de7530a1d2e138a0602d96  quote_raw/n18.json
2e873a851830a9ed338096b5e195990ac5459e891cde4ef9b1dbac996f417a32  quote_raw/n19.json
81e2cbaf94acb8b3cfb60f9c4a5bab45866f1bed4f49c0efbe34f9a5b2a447e5  quote_raw/n2.json
6358d0d3da0726be875483a4866060619312a3aa2894a6301580b40ee1971708  quote_raw/n20.json
bf0e9f41f81148d74a9bcc8d67d4872a6b70b86ca5c19f1db28e23a699b27a01  quote_raw/n21.json
5bdc50bf87f0ca9b2b88cff72cd628b113ecd51c52e0efcda143c801a353612d  quote_raw/n22.json
f6e35531be18ea1b231e3011b652860e9138f36ea57ace22be232da035cd7eed  quote_raw/n23.json
c55db9eec2d3586e605622294536908a96b5a5ef3f7cd60284a264714df335f4  quote_raw/n24.json
052e64bb0301fe637b08418ef9b594cf87c7bfd079c39578ad800d5fbf81ba8b  quote_raw/n3.json
3b85bdc3500da9b85580954e7ec9d557fbbf51fde8997ccce1b67fd603181e55  quote_raw/n4.json
2891276ac4c33f0cc9994f421dff392bb651abf7e09f2c515b048d4b1537cf30  quote_raw/n5.json
82e60a5c77012d4813867766218a31fdceac0e32381464fb911481df2d1ccd7a  quote_raw/n6.json
d861fddde3f811715bb782fd37c955fdff9cd6c61fbdc138fd0ad42491be24b9  quote_raw/n7.json
af35e4570bdbbb84a820396ccf1ef2b14eec626a4769e79b743ce0b0a056c37c  quote_raw/n8.json
9984fe61dbf3e501c19d698db72089c382419a604af2e7f8e0e0bc481493346a  quote_raw/n9.json
