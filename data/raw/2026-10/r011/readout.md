# r011 – Nordnet One Tasapaino, rahastokoko

Ainoa r010-rivi, joka sivustolla näkyi nollana: Nordnet One Tasapaino EUR (n=20).
Screenerin FundTNAV oli 1 599 (pvm 30.10.2026, valuutta puuttui); `Math.round(1599/1e6) === 0` → "0 €".
Muilla 23 rahastolla ja SPYI/VAGF:llä koko oli täytetty. 50/50-rivillä kokoa ei ole (synteettinen salkku).

Morningstar Global quote (en-nd), SAL-kentät 10.11.2026:

- Fund Size (`fundSize`) 55 146 100 EUR, pvm 5.11.2026
- Share class size (`shareSize`) 55 146 100 EUR, pvm 5.11.2026 (ainoan osuussarjan koko = rahastokoko)
- `surveyedFundSize` 1 599,039 = virheellinen FundTNAV, ei käytetä

Lähde: https://global.morningstar.com/en-nd/investments/funds/0P0001P84Z/quote
Raaka: nordnet_one_tasapaino_quote.json
