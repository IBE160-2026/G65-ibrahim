# Tilbakemelding på PRD

| | |
|---|---|
| **Gruppe** | G65 – G65-ibrahim |
| **PRD vurdert** | `_bmad-output/planning-artifacts/prds/prd-G65-ibrahim-2026-10-18/prd.md` (status `final`, sist endret 2026-10-18, commit 3708ad0) |
| **Dato** | 2026-11-12 |
| **Type** | Formativ tilbakemelding, ikke karakter |

## 1. Samlet inntrykk

Dette er en ryddig og ærlig PRD med en klar tese: ett LLM-kall som gir både sammendrag og quiz fra samme materiale. Omfanget passer for én person som er ny i programmering. Risikoen ligger ikke i strukturen, men i det som skjer når KI-en svarer feil, ufullstendig eller ikke i det hele tatt, og i at flere avgjørelser fortsatt står åpne selv om status er `final`.

## 2. Dette fungerer godt

1. **Testbare konsekvenser per FR.** FR-3 og FR-4 sier hva som skal skje («en spesifikk, lesbar feilmelding, ikke et blankt sammendrag eller et ubehandlet unntak», «avvist før noe Gemini-kall gjøres»). FR-5 har konkrete ordgrenser. Disse kan nesten kopieres rett inn som testtilfeller.
2. **Ærlig avgrensning.** §5 Non-Goals og §6.2 er konkrete, og de to `[ASSUMPTION]`-taggene er indeksert i §14. §10 skiller tydelig mellom det som kan testes automatisk og det som bare kan vurderes manuelt (sammendragets kvalitet, med egen sjekkliste).
3. **Briefens hovedpunkter er tatt inn.** Quiz med fasit er flyttet inn i v1, testdata-mappen er spesifisert (§6.1), og hemmeligheter og README er egne punkter (§11). Telleren SM-C1 («ikke fyll ut med tekst for å nå ordgrensen») viser at dere har tenkt på hva som ikke skal optimaliseres.

## 3. Oversikt per dimensjon

| Dimensjon | Vurdering | Kort begrunnelse |
|---|---|---|
| Beslutningsklarhet | god | Åpne spørsmål er ærlige, men frist, quizformat og ett/to kall står uavklart i et dokument merket `final`. |
| Substans | god | Innholdet er produktspesifikt. Noen seksjoner (§9–§11) begrunnes med vurderingsvekter, ikke med produktbehov. |
| Strategisk sammenheng | god | Tydelig tese om felles pipeline. «Hvorfor ikke bare en chatbot» er kun antydet. |
| Testbarhet | god | Sterke konsekvenser for input og UI, men KI-feil, lengdemåling og quizformat er uklare. |
| Scope og avgrensning | sterk | Eksplisitte Non-Goals, MVP inn/ut og indekserte antakelser. |
| Brukbarhet for neste fase | god | Glossar og ID-er er konsistente, men flere krysshenvisninger peker feil (se kap. 5). |
| Formtilpasning | sterk | Én bruker og én reise passer et soloprosjekt. |

## 4. Viktigste forbedringer

### 4.1 Hva skjer når Gemini ikke leverer?
- **Alvorlighet:** høy
- **Hvor:** §4.2 FR-7 («using a deliberately engineered prompt»), §9 («request structured output»), §7 Cost («throttling and/or caching»)
- **Problem og hvorfor det betyr noe:** Ingen FR beskriver feiltilfeller fra selve KI-kallet: ugyldig eller avkuttet strukturert svar, rate limit (429), tidsavbrudd, manglende nøkkel, eller svar på feil språk. Dette er de vanligste feilene i en slik app, og arkitektur og stories vil ikke ha noe å bygge tester på.
- **Forslag:** Legg til f.eks. «FR-12: Feilhåndtering for Gemini-kall». Konsekvenser: (a) ved ugyldig/ikke-parserbart svar vises en forståelig melding og brukeren kan prøve igjen, uten ubehandlet unntak; (b) ved 429 eller timeout (>60 s) vises melding med råd om å vente; (c) manglende API-nøkkel gir melding som peker til README; (d) hvis sammendraget er utenfor valgt ordgrense, vises det likevel, men med en merknad.

### 4.2 Quizformat og riktighet på fasiten
- **Alvorlighet:** høy
- **Hvor:** §4.3 FR-8 (`[ASSUMPTION: multiple-choice or short-answer with an exact-match…]`), FR-9, §13 spørsmål 3
- **Problem og hvorfor det betyr noe:** FR-9 («matched the Answer Key») kan ikke testes før formatet er valgt. Exact-match på fritekst er upålitelig. Dessuten er fasiten selv KI-generert, så «correct» betyr bare «samsvarer med det modellen sa». Dette er kjernen i «kontroll på KI-ens arbeid».
- **Forslag:** Bestem nå: flervalg med 4 alternativer og nøyaktig ett riktig. Legg til konsekvenser: «hvert spørsmål har nøyaktig 4 alternativer og 1 riktig svar-indeks»; «et quizsvar som mangler fasit eller har ≠1 riktig alternativ forkastes og genereres på nytt (maks 1 gang)»; og i §10 en manuell stikkprøve: «bygger tre av fem spørsmål/fasit på sammendragets innhold?»

### 4.3 Testmodus: avgjør det, og rett opp motsigelsen i SM-2
- **Alvorlighet:** medium
- **Hvor:** §6.2/§11 (`[NOTE FOR PM]`), §13 spørsmål 4, SM-2 («without the builder's own key»)
- **Problem og hvorfor det betyr noe:** SM-2 og §11 sier at andre skal kunne kjøre appen «uten byggerens egen nøkkel», men appen krever en Gemini-nøkkel. En mock-modus er også det som gjør at de automatiserte testene i §10 kan kjøres uten nettverk og uten å bruke opp gratiskvoten.
- **Forslag:** Gjør den til et FR: «FR-13: Når `MOCK_MODE=true` returnerer appen et lagret eksempelsvar (Summary + Quiz) uten Gemini-kall.» Skriv SM-2 om til: «Sensor kan kjøre appen i mock-modus uten nøkkel, og med egen gratis nøkkel i live-modus, kun etter README.»

### 4.4 Frist og `final` med åpne spørsmål
- **Alvorlighet:** medium
- **Hvor:** frontmatter `status: final`, §13 spørsmål 1 («reported as due now/overdue»), 2 og 3
- **Problem og hvorfor det betyr noe:** Fristen er fortsatt ikke avklart, selv om briefen-tilbakemeldingen ba om det. Uten frist kan ikke epics prioriteres. `final` med fire åpne spørsmål, hvorav to blokkerer arkitektur og stories, signaliserer ferdig der det ikke er det.
- **Forslag:** Les emnebeskrivelsen og skriv frist og leveranseform inn i §0/§6. Sett status til `draft` til spørsmål 2–3 er besluttet, eller flytt dem til «Beslutninger» med begrunnelse.

### 4.5 Gjør lengde, språk og input måle- og avgrensbare
- **Alvorlighet:** medium
- **Hvor:** FR-5 («under 150 words»), FR-6 vs. glossar («Output Language … (and Quiz)»), FR-4 («non-PDF/non-text file»), FR-7 («structured, readable»)
- **Problem og hvorfor det betyr noe:** Språkmodeller treffer sjelden ordgrenser nøyaktig, og det står ikke hvordan ord telles. FR-6 nevner bare Summary, men glossaret og UJ-1 forutsetter at Quiz også følger språkvalget. Det finnes ingen grense for innlimt tekst eller PDF-størrelse. «Structured, readable» kan ikke testes.
- **Forslag:** «Ord telles ved å splitte på mellomrom; et sammendrag regnes som korrekt hvis det ligger innenfor grensen ±10 %.» Utvid FR-6 til «Summary og Quiz». Legg til «tekst over N tegn avvises med melding». Erstatt «structured» med «Summary har en overskrift og minst 3 punkter/avsnitt».

## 5. Mekaniske funn

- Krysshenvisninger som ikke stemmer: §0 sier antakelser er indeksert i «§13» (det er §14); §6.2 og §11 henviser til «Open Question in §12» (det er §13); Vision henviser til «§4 Non-Goals» (det er §5).
- FR-1 til FR-11 og SM-1/2/3/C1 er sammenhengende og unike. Begge `[ASSUMPTION]` er indeksert og finnes i teksten.
- SM-1 («alle FR-er består») er nær en omskriving av FR-ene, og SM-3 («bruker appen etter semesteret») kan ikke måles innen innleveringen. Vurder en målbar sekundærmetrikk, f.eks. «6 av 6 testdokumenter gir forventet resultat».
- Bare ett UJ. Det er greit for én bruker, men feilveiene (4.1) bør ha egne korte scenarier.

## 6. Før dere går videre

**Må avklares før UX, arkitektur og epics:** frist og leveranseform (4.4), quizformat (4.2), ett eller to Gemini-kall (§13 sp. 2, påvirker prompt og feilhåndtering), og om det skal være testmodus (4.3).

**Kan vente:** plassering og format på prompt-loggen (`PROMPTS.md` e.l.), eksakt ventegrense, lagring og flashcards (§8).

**Oppfølging av tilbakemeldingen på product brief: delvis.** Fulgt opp: quiz med fasit i v1, testbare kriterier i FR-ene, testdata-mappe, nøkkelhåndtering, README og personvernmerknad om at materialet sendes til Google. Ikke fulgt opp: frist og leveranseform er fortsatt uavklart, og testmodus er bare «vurdert». Sjekk også Googles vilkår for gratisnivå: innsendt innhold kan brukes til produktforbedring, og det bør stå i README-en.

## 7. Refleksjonsspørsmål

1. Fasiten i quizen er laget av samme modell som sammendraget. Hvordan vil dere oppdage at en fasit er feil, og hvem avgjør det: dere eller modellen?
2. §9 og §10 er skrevet med tanke på hva sensor vekter. Hvilke av de kravene hadde dere satt opp selv for å stole på appen i egne eksamensforberedelser, og hvilke ville dere strøket?

_Vurdert mot kvalitetsrubrikken i bmad-prd. Dette er veiledning, ikke sensur._
