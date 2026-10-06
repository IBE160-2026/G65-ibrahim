# Tilbakemelding på product brief

| | |
|---|---|
| **Gruppe** | G65 – G65-ibrahim |
| **Product brief** | `_bmad-output/planning-artifacts/briefs/brief-G65-ibrahim-2026-09-11/brief.md` (commit `888c530`) |
| **Tilbakemelding fra** | Faglærer i IBE160 (utarbeidet med KI-støtte) |
| **Dato** | 2026-10-06 |

## Samlet vurdering

- **Godt utgangspunkt med justeringer.** Gruppen kan gå videre og innarbeide punktene under.

**Det som er bra:**

1. Briefen er ærlig og realistisk for en gruppe på én person som er ny i programmering. Dere har bevisst valgt «one feature done well»: oppsummering av PDF eller innlimt tekst med valg av lengde (kort/middels/lang) og språk (norsk/engelsk). Risikoene (PDF-lesing, kvalitet på sammendrag, grenser i gratisversjonen av Gemini) er tydelig beskrevet med tiltak.
2. Avgrensningene er konkrete: bare tekstbaserte PDF-er, ingen OCR, ingen tabeller og figurer, ingen innlogging og ingen betalte API-er. Det gjør det lett å lage PRD og stories med en klar ramme.

**De viktigste endringene:**

1. V1 er trolig for lite til å vise nok funksjonalitet, testing og prosess. Bare oppsummering kan bli ferdig svært raskt med Streamlit og Gemini. Ta inn minst én av de planlagte utvidelsene i v1 – for eksempel flashcards eller quiz med fasit – eller lagring av tidligere sammendrag per emne.
2. Gjør suksesskriteriene testbare. «Accurate, genuinely useful summaries» og «Clean interface» kan ikke sjekkes. Skriv for eksempel «et kort sammendrag er under 150 ord», «valgt språk engelsk gir engelsk sammendrag selv om PDF-en er på norsk» og «en skannet PDF uten tekst gir en forståelig feilmelding».
3. Avklar fristene. Briefen sier at leveranser og milepæler er «TBD» fordi emneplanen ikke er lest. Les emnebeskrivelsen, og oppdater «Course Context & Constraints» med riktig innleveringsform og frist.

## Vanskelighetsgrad og gjennomførbarhet

### Vurdert vanskelighetsgrad

- **Enkel**

**Sammenlignbart med:** 1) AI Study Buddy (enkel), slått sammen med 8) Foredragsnotater – sammendrag og quizgenerator (enkel), slik dere selv skriver. Med bare oppsummering i v1 ligger prosjektet i nedre del av «enkel».

**Begrunnelse:**

| Faktor | Nivå (lav / middels / høy) | Kommentar |
|---|---|---|
| Domenelogikk – hvor mange og hvor kompliserte regler og beregninger må stemme? | Lav | Få regler: lengde, språk og håndtering av ugyldig input. |
| Datamodell – antall entiteter og relasjoner mellom dem | Lav | Ingen lagring beskrevet. Dokument inn, sammendrag ut. |
| Brukere, roller og innlogging | Lav | Én bruker, ingen innlogging – bevisst valgt. |
| KI-funksjonalitet i appen, f.eks. kall til språkmodell, prompts i koden og håndtering av usikre svar | Middels | Ett LLM-kall, men med krav om «thoughtful prompt engineering», valg av lengde og språk, og strukturert svar. |
| Integrasjoner og eksterne tjenester, f.eks. API-er, betaling og e-post | Lav | Gemini API (gratisnivå). |
| Sanntid, samtidighet eller flere brukere som påvirker hverandre | Lav | Ingen. |
| Filhåndtering, f.eks. opplasting, PDF-lesing og eksport | Middels | Opplasting og tekstuttrekk fra PDF. Godt avgrenset til tekstbaserte PDF-er. |
| Sikkerhet og personvern | Lav | Ingen lagring og ingen personopplysninger. Kursmateriale sendes til Google – det bør nevnes. |

**Hva vanskelighetsgraden betyr for dere:**

- _Enkel:_ Et enkelt prosjekt gir stor sjanse for å bli ferdig. Vanskelighetsgraden inngår likevel i vurderingen, så for å nå helt opp må dere vise mer i gjennomføringen. Det betyr særlig et gjennomarbeidet design, grundig testing, en tydelig dokumentert prosess og en README som virker. Vurder også om én utvidelse – quiz med fasit eller flashcards – kan løfte vanskelighetsgraden.

### Gjennomførbarhet med BMAD og Claude Code

Dere skal planlegge med BMAD (product brief → PRD → arkitektur → epics og stories) og implementere med Claude Code. Vurderingen under tar hensyn til at det må være tid til hele denne flyten, og til testing, retting og README til slutt.

| Spørsmål | Vurdering (OK / risiko / stor risiko) | Kommentar |
|---|---|---|
| **Tid og omfang** – kan v1 realistisk bli ferdig og stabil i løpet av semesteret, med tid til flere iterasjoner? | OK | V1 kan bli ferdig og stabil med god margin. Risikoen er heller at det blir for lite å vise. Bruk tiden på én utvidelse og grundig testing. |
| **BMAD-flyten** – er briefen konkret nok til at PRD, arkitektur og stories kan lages uten store hull, og blir det overkommelig mange stories? | OK | Briefen er konkret, og flyten er enkel å bryte ned. Antall stories blir lite – en utvidelse gir et bedre grunnlag for epics. |
| **Egnet for Claude Code** – bruker løsningen en vanlig, godt dokumentert teknologistakk som Claude Code håndterer godt, eller krever den nisjeteknologi, spesialmaskinvare eller mye manuell konfigurasjon? | OK | Python, Streamlit og Gemini er godt dokumentert og passer godt for en nybegynner. |
| **Kontroll på KI-ens arbeid** – kan gruppen selv avgjøre om koden gjør det riktige? Krever domenet kunnskap gruppen ikke har, f.eks. avanserte beregninger eller fagregler, så er det vanskelig å kvalitetssikre. | OK | Du kjenner kursmaterialet og kan selv vurdere om et sammendrag er riktig. Lag en sjekkliste for hva et godt sammendrag skal inneholde, og test mot egne forelesningsnotater. |
| **Testbarhet** – finnes det tydelige regler og forventede resultater som tester kan skrives mot? | Risiko | PDF-lesing, valg av lengde og språk og feilhåndtering kan testes automatisk. Kvaliteten på sammendraget må testes manuelt. Beskriv begge deler i PRD-en. |
| **Kjørbar for sensor** – kan appen kjøres lokalt etter README, uten gruppens nøkler, betalte kontoer eller egen infrastruktur? | Risiko | Gemini krever en API-nøkkel, selv på gratisnivå. Beskriv i README hvordan sensor lager en gratis nøkkel, og legg gjerne inn en testmodus med et lagret eksempelsvar. |
| **Avhengigheter og kostnader** – krever løsningen betalte API-er, f.eks. språkmodeller, og finnes det en plan for kostnad, testmodus eller mock-data? | OK | Bare gratisnivå, med plan for grenser (throttling og caching). Det er godt gjennomtenkt. |

**Konklusjon om gjennomførbarhet:**

- **Gjennomførbart som beskrevet.**

**Forslag til justering av omfang eller vanskelighetsgrad:**

1. Flytt quiz-generering med fasit inn i v1, med en enkel quizvisning der studenten svarer og får se resultatet. Fasit gir noe konkret å teste mot, og det bruker samme flyt som dere allerede har planlagt (les materiale → LLM-kall → strukturert svar).
2. Alternativt: legg til lagring av sammendrag per emne (for eksempel i en lokal SQLite-database), slik at du kan bygge opp en samling over semesteret. Det gir datamodell og flere testtilfeller uten å kreve innlogging.

## Hvorfor product brief er viktig for mappen

Product brief er utgangspunktet for PRD, arkitektur, stories og til slutt koden. Del 1 av mappen vurderes blant annet på om sensor kan følge en sporbar vei fra plan til ferdig app. Den vurderes også på om appen gjør det dere har beskrevet, om den er testet, om den er godt designet, og om den kan kjøres etter README. Et uklart, for stort eller for lite brief gjør alt dette vanskeligere senere. Det er mye enklere å rette nå enn sent i semesteret.

## 1. Gjennomgang av briefens deler

| Del av brief | Status | Kommentar |
|---|---|---|
| Executive Summary – er det klart hva appen er, og hvilket problem den løser? | OK | Tydelig: last opp PDF eller lim inn tekst, velg lengde og språk, få et strukturert sammendrag. |
| The Problem – er problemet konkret, med reelle situasjoner og brukere? | OK | Konkret om tidkrevende bearbeiding av forelesningsmateriale og blanding av norsk og engelsk. |
| The Solution – beskriver løsningen brukeropplevelsen, ikke bare teknologi? | OK | Beskriver flyten i tre steg. Teknologivalget (Streamlit, Gemini) kan flyttes til arkitekturen. |
| What Makes This Different – er vurderingen ærlig og realistisk? | Juster | Mangler som egen del, men problemdelen sammenligner med generiske chatboter. Skriv det ut som egen del, og vær ærlig om at mange verktøy allerede kan oppsummere PDF-er. |
| Who This Serves – er primærbrukerne tydelige, og vet vi hva de trenger? | OK | Primærbrukeren er konkret beskrevet med behov og type materiale. Det er greit at det er deg selv i v1. |
| Success Criteria – kan kriteriene faktisk sjekkes eller testes? | Endre | Kriteriene er vage («accurate», «clean», «easy-to-use»). Skriv funksjonelle kriterier som kan bli testtilfeller. |
| Scope – er det klart hva som er med i første versjon, og hva som ikke er det? | Juster | Svært tydelig inndeling, men v1 er smal. Vurder å flytte én utvidelse inn. |
| Vision – henger visjonen sammen med resten uten å blåse opp omfanget? | OK | Flashcards, quiz og flere brukere er tydelig plassert etter kurset. |

## 2. Utgangspunkt for del 1 av mappen

Punktene følger kriteriene i sensorveiledningen for del 1. Vektene i parentes viser hvor mye hvert kriterium teller i del 1.

| Kriterium i del 1 | Hva briefen bør legge til rette for | Status | Kommentar |
|---|---|---|---|
| **1. Prosess og KI-styring** (30 %) | Brief som er presis nok til at PRD og stories kan bygges direkte på den, slik at krav kan spores fra brief til kode. | OK | Briefen er presis. Lagre prompt-iterasjonene for sammendraget – de er godt materiale for sporbar KI-styring. |
| **2. Funksjonalitet og omfang** (20 %) | Realistisk omfang for gruppen og semesteret: en tydelig kjerneflyt som kan bli ferdig og stabil, og nok innhold til å vise reell funksjonalitet. | Juster | Kjerneflyten er tydelig, men omfanget er lite. Én utvidelse gir mer reell funksjonalitet å vise. |
| **3. Kvalitetssikring og testing** (15 %) | Suksesskriterier og funksjoner som er konkrete nok til å bli testtilfeller. | Endre | Kriteriene må gjøres konkrete. Lag et sett med testdokumenter (norsk, engelsk, skannet PDF, tom fil) med forventet oppførsel. |
| **4. Design og brukeropplevelse** (10 %) | Tydelige brukere og brukssituasjoner som designet kan bygges rundt, gjerne med de viktigste skjermbildene eller flytene skissert. | OK | Én tydelig bruker og én tydelig flyt. Tenk på tomtilstander, ventetid mens Gemini svarer, og feilmeldinger. |
| **5. Kodekvalitet og arkitektur** (10 %) | Teknologivalg som er begrunnet og ikke mer komplekse enn appen trenger. | OK | Streamlit og Gemini er enkle og begrunnede valg for en nybegynner. |
| **6. README og kjørbarhet** (10 %) | Løsning som andre kan kjøre lokalt uten betalte kontoer, og uten tilgang til gruppens egne tjenester og nøkler. | Juster | Lokal kjøring er planlagt. Beskriv hvordan sensor skaffer en gratis Gemini-nøkkel, eller legg inn testmodus. |
| **7. Ryddighet i repoet** (5 %) | En plan for hvor hemmeligheter, testdata og dokumentasjon skal ligge. | Juster | Ikke beskrevet. Bruk `.env.example` eller Streamlit sin `secrets.toml` (som ikke committes) for nøkkelen, og legg testdokumenter i en egen mappe. |

## 3. Neste steg for gruppen

1. Bestem om quiz med fasit, flashcards eller lagring per emne skal inn i v1, og oppdater Scope.
2. Skriv om «Success Criteria» med 5–8 konkrete, testbare kriterier, og lag et lite sett med testdokumenter.
3. Les emnebeskrivelsen, og oppdater frister og leveranser i «Course Context & Constraints» før du lager PRD-en.

Oppdater product brief i repoet når dere har gjort endringene, slik at historikken viser hvordan planen utviklet seg. Det er en del av prosessen sensor ser etter.
