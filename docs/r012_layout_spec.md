# r012 – Päätaulukon asettelu (Grok Build -portille)

Tavoite: taulukko mahtuu ~1440 px työpöydälle ilman vaakavieritystä; kapeammilla näytöillä (1280 px, mobiili) taulukko vierii vaakasuunnassa omassa laatikossaan, rahastosarake ja otsikkorivi pysyvät näkyvissä. Data, sarakkeet, järjestys, lajittelu, Excel-vienti ja solujen sisältö (luvut, päivät, tagit, tooltipit) EIVÄT muutu. Viitetoteutus: repo `index.html` (patch `r012_index_html.patch`).

## 1. Vierityslaatikko
- Kääri `<table>` (molemmat thead-rivit + tbody) elementtiin `<div class="tw" id="tw">…</div>`.
- `.tw{overflow:auto;-webkit-overflow-scrolling:touch;max-width:100%;max-height:calc(100vh - 16px);background:#fff;border-radius:8px;box-shadow:0 1px 3px #0001}`
  - `max-height` on tarpeen, jotta otsikkorivi voi olla sticky laatikon sisällä (laatikko on vieritysyhteys molempiin suuntiin).
- Älä aseta `overflow:hidden` mihinkään taulukon yläelementtiin (main, card tms.).

## 2. Tiiviimpi typografia
- `.tw table{font-size:12px}`; `.tw th,.tw td{padding:4px 5px}`; `.tw small{font-size:10px}` (pvm-, kattavuus-, markkina- ja ISIN-rivit).
- Otsikot saavat rivittyä: `.tw th,.tw th.num{white-space:normal;line-height:1.2;vertical-align:bottom}`.
- Numerosolut pysyvät `white-space:nowrap` (ennallaan). Poikkeus: 50/50-rivin "korko-osuus (VAGF)" -pikkuteksti saa rivittyä (`<small class="wr">`, `.tw td.num small.wr{white-space:normal}`).
- Arviosolun alarivi kahdelle riville: `pvm<br>kattavuus&nbsp;NN&nbsp;%` (ennen `pvm · kattavuus NN %` yhdellä rivillä). Sisältö sama.

## 3. Sticky-otsikko ja -rahastosarake
- Sarakeotsikkorivi (`#hd`): `.tw #hd th{position:sticky;top:0;z-index:2}`. Ryhmärivi (Tuotot %, Ero, …) jää staattiseksi (vierii pois).
- Sarake 1 (#): `.tw td:nth-child(1),.tw #hd th:nth-child(1){position:sticky;left:0;width:22px;min-width:22px;max-width:22px;z-index:1;background-color:#fff}`
- Sarake 2 (Rahasto): `.tw td:nth-child(2),.tw #hd th:nth-child(2){position:sticky;left:32px;min-width:130px;max-width:150px;z-index:1;background-color:#fff;box-shadow:inset -2px 0 0 #c5cad3}` (left = sarakkeen 1 leveys 22 + padding 10).
- Raidoitus säilyy: `.tw tbody tr:nth-child(even) td:nth-child(2){box-shadow:inset -2px 0 0 #c5cad3,inset 0 0 0 999px rgba(0,0,0,.045)}`.
- Kulmasolut: `.tw #hd th:nth-child(-n+2){background:#eef0f4;z-index:3}`.
- 50/50- ja ETF-rivien omat taustat (`!important`) peittävät valkoisen taustan → ok, kunhan tausta on läpinäkymätön.
- Rahastosarakkeen tagit (sulautunut, ei tuottoa) ja Allok. pvm -sarakkeen tagit (vanhempi, tarkista) rivittyvät: `.tw td:nth-child(2) .tag,.tw td:last-child .tag{display:inline-block;margin:2px 2px 0 0}`; `.tw td:last-child{min-width:72px;max-width:84px}`.

## 4. Erityispiirteet ja Selitys tuottoerolle
- Molemmille sarakkeille luokka `tx` (G: `feat:'g-tx sep tx'`, `expl:'g-tx tx'`; koskee th:tä ja td:tä): `.tw .tx{width:150px;min-width:130px;max-width:170px}`.
- Teksti 3 riviin: solun sisältö `<div class="clamp" title="KOKO TEKSTI (HTML-escapattu)">teksti</div>`; `.tw .clamp{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}`. Koko teksti tooltipissä. "kuvaus YYYY-MM" -pikkurivi (jos `text_from_period` ≠ kausi) jää clampin ulkopuolelle sen alle.
- Escape title: `esc=t=>String(t??'').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;')`.
- Sama ETF-/50/50-riveillä (`x.feat`).

## Mitattu (headless Chrome, repo index.html, r012-data)
| Ikkuna | Ennen: taulukko / tila | Jälkeen: taulukko / tila |
|---|---|---|
| 1440 px | 1894 / 1425 px, sivu vuoti yli, ei vieritystä | 1362 / 1362 px – mahtuu, ei vieritystä |
| 1920 px | – | 1485 / 1485 px – mahtuu |
| 1280 px | vuoti yli | 1332 / 1202 px – vierii laatikossa, #/Rahasto ja otsikko pysyvät |
| kapea 500 px | vuoti yli | vierii laatikossa |
Ylivuotavia soluja (scrollWidth > clientWidth) 0.

## Hyväksyntä
1. 1440×900: ei vaakavierityspalkkia sivulla eikä laatikossa; kaikki 19 saraketta näkyvät.
2. 1280 px ja puhelin: laatikossa vaakavieritys; # ja Rahasto pysyvät vasemmalla, sarakeotsikot ylhäällä pystyvierityksessä.
3. Erityispiirteet/Selitys korkeintaan 3 riviä, hover näyttää koko tekstin.
4. Excel-vienti ennallaan (tests/excel_export_test.py OK).
