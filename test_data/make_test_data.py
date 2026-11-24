"""Generate the committed sample inputs in test_data/.

Run from the repo root:

    .venv/Scripts/python test_data/make_test_data.py    (Windows)
    .venv/bin/python test_data/make_test_data.py        (macOS/Linux)

The outputs are always written next to this script, wherever it is run from.
It writes four files:

- norwegian_lecture.pdf   -- about 10 text slides in Norwegian (with æ, ø, å)
- english_lecture.pdf     -- about 10 text slides in English
- mixed_language_notes.txt -- Norwegian and English paragraphs, UTF-8, no BOM
- scanned_lecture.pdf     -- one page holding only an image, no text layer

Why synthetic: real lecture slides are usually copyrighted, so the committed
test data is written here from text kept in this script. Real course PDFs for
manual runs go in test_data/private/, which is gitignored and never committed.

Only the Python standard library is used. The output is deterministic: no
creation date, no document ID, objects in a fixed order, so every run with the
same Python/zlib build writes the same bytes. Another build (for example one
using zlib-ng) may compress the scanned image differently, which is harmless.
"""

import textwrap
import zlib
from pathlib import Path

OUT_DIR = Path(__file__).parent

PAGE_WIDTH = 792  # landscape slide, in points
PAGE_HEIGHT = 612
MARGIN = 72
HEADING_SIZE = 24
BODY_SIZE = 14
BODY_LEADING = 20
WRAP_WIDTH = 80

NORWEGIAN_SLIDES = [
    ("Vannets kretsløp: en oversikt", [
        "Vannets kretsløp beskriver hvordan vann beveger seg mellom hav, luft og land.",
        "Den samme vannmengden brukes om og om igjen, og nesten ingenting går tapt.",
        "Solen gir energien som driver hele kretsløpet.",
        "Tyngdekraften får nedbør og elver til å føre vannet tilbake til havet.",
        "Kretsløpet påvirker vær, klima og livet på jorden.",
        "Vann som fordamper fra havet i dag, kan falle som snø på fjellet om noen uker.",
    ]),
    ("Fordampning", [
        "Fordampning skjer når flytende vann blir til vanndamp.",
        "Det meste av fordampningen kommer fra havets overflate.",
        "Høy temperatur og sterk vind gjør at vannet fordamper raskere.",
        "Når vannet fordamper, blir salter og andre stoffer liggende igjen.",
        "Fordampningen kjøler ned overflaten, omtrent som svette kjøler huden.",
        "Over hele jorden fordamper det omtrent like mye vann som det faller som nedbør.",
    ]),
    ("Transpirasjon fra planter", [
        "Planter tar opp vann gjennom røttene og slipper det ut gjennom bladene.",
        "Denne prosessen kalles transpirasjon.",
        "Et stort løvtre kan avgi flere hundre liter vann på en varm sommerdag.",
        "Fordampning og transpirasjon kalles ofte samlet for evapotranspirasjon.",
        "Skoger kan derfor øke luftfuktigheten i et område merkbart.",
        "Mengden vann som avgis, avhenger av plantetype, temperatur og tilgang på vann i jorden.",
    ]),
    ("Kondensasjon og skyer", [
        "Varm og fuktig luft stiger og avkjøles høyere oppe i atmosfæren.",
        "Når luften blir kald nok, kondenserer vanndampen til små dråper.",
        "Dråpene samler seg rundt bittesmå partikler av støv, salt eller sot.",
        "Milliarder av slike dråper danner skyer og tåke.",
        "Dugg på gresset om morgenen er også et resultat av kondensasjon.",
        "Lave skyer består oftest av vanndråper, mens høye skyer ofte består av iskrystaller.",
    ]),
    ("Nedbør", [
        "Nedbør oppstår når dråpene i skyene blir for tunge til å holde seg svevende.",
        "Nedbøren kan komme som regn, snø, sludd eller hagl.",
        "Formen avhenger av temperaturen i luftlagene som nedbøren faller gjennom.",
        "Vestlandet får mye nedbør fordi fuktig luft fra havet presses opp over fjellene.",
        "Nedbør måles i millimeter, altså hvor høyt vannet ville stått på flat mark.",
        "Store nedbørsmengder over kort tid kan gi skred i bratte lier.",
    ]),
    ("Avrenning og elver", [
        "En del av nedbøren renner bortover bakken som overflateavrenning.",
        "Bekker samles til elver som til slutt munner ut i havet.",
        "Bratt terreng og tette flater som asfalt gir rask avrenning.",
        "Rask avrenning kan føre til flom etter kraftig regn eller snøsmelting.",
        "Elvene frakter også sand, leire og næringsstoffer nedover mot kysten.",
        "Elvenes vannføring varierer gjennom året og er ofte størst i mai og juni.",
    ]),
    ("Infiltrasjon og grunnvann", [
        "Noe av vannet siger ned i jorden. Dette kalles infiltrasjon.",
        "Vannet fyller porer og sprekker i jord og berggrunn og blir grunnvann.",
        "Grunnvann kan bli liggende i bakken i alt fra dager til tusenvis av år.",
        "Mange norske kommuner henter drikkevann fra grunnvannsbrønner.",
        "Kilder oppstår der grunnvannet kommer opp til overflaten av seg selv.",
        "Leire slipper vann gjennom svært sakte, mens sand og grus slipper det lett gjennom.",
    ]),
    ("Snø, is og breer", [
        "I kalde områder kan vann bli lagret som snø og is i lang tid.",
        "Breer dannes når snø hoper seg opp år etter år og presses sammen til is.",
        "Jostedalsbreen er den største breen på det europeiske fastlandet.",
        "Om våren smelter snøen og gir ekstra mye vann i elvene.",
        "Snøsmeltingen er viktig for vannkraftverkene i Norge.",
        "Når klimaet blir varmere, smelter mange breer raskere enn før.",
    ]),
    ("Mennesker og vannets kretsløp", [
        "Mennesker endrer kretsløpet når vi demmer opp elver og bygger magasiner.",
        "Jordbruk bruker store mengder vann til vanning av åkre.",
        "Byer med mye asfalt slipper mindre vann ned i bakken.",
        "Forurensning kan følge vannet fra land til elver og videre ut i havet.",
        "God vannforvaltning handler om å bruke vannet uten å skade kretsløpet.",
        "Klimaendringer kan gi både mer intens nedbør og lengre tørkeperioder.",
    ]),
    ("Oppsummering", [
        "Vannets kretsløp er drevet av solenergi og tyngdekraft.",
        "Hovedprosessene er fordampning, kondensasjon, nedbør og avrenning.",
        "Vann kan lagres i hav, innsjøer, grunnvann, snø og is.",
        "Kretsløpet fordeler varme og ferskvann rundt hele jorden.",
        "Å forstå kretsløpet hjelper oss å planlegge for flom, tørke og drikkevann.",
        "Den samme vannmengden har sirkulert på jorden i flere milliarder år.",
    ]),
]

ENGLISH_SLIDES = [
    ("Introduction to Plate Tectonics", [
        "Plate tectonics explains how the outer shell of the Earth moves over time.",
        "The shell, called the lithosphere, is broken into large and small plates.",
        "The plates move only a few centimetres each year.",
        "Over millions of years this slow motion reshapes continents and oceans.",
        "The theory ties together earthquakes, volcanoes and mountain building.",
        "The idea grew from older observations of how the continents seem to fit together.",
    ]),
    ("Layers of the Earth", [
        "The Earth has a crust, a mantle, an outer core and an inner core.",
        "The crust is thin compared with the rest of the planet.",
        "The upper mantle is solid but can flow very slowly, like warm wax.",
        "The rigid lithosphere rides on a softer layer called the asthenosphere.",
        "Heat from the deep interior keeps the mantle in slow motion.",
        "Oceanic crust is thinner and denser than continental crust.",
    ]),
    ("Continental Drift", [
        "In 1912 Alfred Wegener proposed that the continents had once been joined.",
        "He called the former supercontinent Pangaea.",
        "Matching coastlines, fossils and rock types supported his idea.",
        "Most geologists rejected it because he could not explain the driving force.",
        "Later discoveries on the ocean floor showed that he was largely right.",
        "Glacial deposits and coal beds were found in places with very different climates today.",
    ]),
    ("Sea-Floor Spreading", [
        "Mid-ocean ridges are long underwater mountain chains.",
        "At the ridges, magma rises and forms new oceanic crust.",
        "The new crust moves away from the ridge on both sides.",
        "Rocks on the sea floor record reversals of the magnetic field in stripes.",
        "The stripes are symmetric around the ridge, which confirms the spreading.",
        "The youngest oceanic crust lies at the ridge and gets older with distance from it.",
    ]),
    ("Divergent Boundaries", [
        "At divergent boundaries, two plates move away from each other.",
        "Most divergent boundaries lie along mid-ocean ridges.",
        "On land they can form rift valleys, such as the East African Rift.",
        "Iceland sits on the Mid-Atlantic Ridge and has frequent eruptions.",
        "Earthquakes here are usually shallow and relatively weak.",
        "Over time a rift valley can widen and flood to become a new ocean.",
    ]),
    ("Convergent Boundaries", [
        "At convergent boundaries, two plates move towards each other.",
        "When an oceanic plate meets a continental plate, the denser oceanic plate sinks.",
        "This sinking is called subduction and creates deep ocean trenches.",
        "Subduction feeds chains of volcanoes, such as those around the Pacific.",
        "When two continents collide, high mountains like the Himalayas form.",
        "The deepest point on Earth, the Mariana Trench, formed at a subduction zone.",
    ]),
    ("Transform Boundaries", [
        "At transform boundaries, plates slide past each other sideways.",
        "Crust is neither created nor destroyed at these boundaries.",
        "Friction makes the plates lock and then slip suddenly.",
        "Each sudden slip releases energy as an earthquake.",
        "The San Andreas Fault in California is a well-known example.",
        "Rocks along the fault are often ground into fine crushed material.",
    ]),
    ("What Drives the Plates", [
        "Heat inside the Earth sets up slow convection currents in the mantle.",
        "Ridge push occurs as new crust slides down from the raised ridge.",
        "Slab pull occurs as a sinking plate drags the rest of the plate behind it.",
        "Slab pull is thought to be the strongest of these forces.",
        "Scientists still debate how the forces combine in different places.",
        "Laboratory models and computer simulations are used to test these ideas.",
    ]),
    ("Earthquakes and Volcanoes", [
        "Most earthquakes and volcanoes occur near plate boundaries.",
        "The Pacific Ring of Fire follows a long chain of subduction zones.",
        "Hot spots such as Hawaii form volcanoes far from any boundary.",
        "Seismometers record earthquake waves and help locate their source.",
        "Mapping these events reveals the outlines of the plates.",
        "Early warning systems use this knowledge to reduce the damage from hazards.",
    ]),
    ("Summary", [
        "The lithosphere is divided into plates that move slowly over the mantle.",
        "Plates meet at divergent, convergent and transform boundaries.",
        "Each boundary type produces typical landforms and hazards.",
        "Mantle convection, ridge push and slab pull drive the motion.",
        "Plate tectonics links many features of the Earth into one theory.",
        "It is one of the central ideas of modern geology.",
    ]),
]

MIXED_NOTES = """\
Notater fra forelesning om fotosyntese

Fotosyntese er prosessen der planter, alger og noen bakterier bruker energi fra sollys til å lage sukker. Prosessen skjer i kloroplastene, som inneholder det grønne fargestoffet klorofyll. Planten tar opp karbondioksid fra luften og vann fra jorden, og den slipper ut oksygen som et biprodukt.

The light-dependent reactions take place in the thylakoid membranes. Light energy splits water molecules, releases oxygen and produces the energy carriers ATP and NADPH. These carriers are then used in the next stage of the process.

I Calvin-syklusen, som foregår i stroma, bindes karbondioksid til et organisk molekyl. Ved hjelp av ATP og NADPH bygges det opp sukker som planten kan bruke til vekst eller lagre som stivelse. Syklusen trenger ikke lys direkte, men er avhengig av produktene fra lysreaksjonene.

Several factors limit the rate of photosynthesis: light intensity, carbon dioxide concentration and temperature. If one factor is in short supply, increasing the others has little effect. Greenhouses often add extra carbon dioxide to make crops grow faster.

Fotosyntesen er grunnlaget for nesten alle næringskjeder på jorden. Den binder også karbon fra atmosfæren og påvirker dermed klimaet. Skoger og havets planteplankton står for en stor del av den globale fotosyntesen.
"""


def pdf_string(text):
    """Encode text as a PDF literal string in WinAnsi (cp1252)."""
    raw = text.encode("cp1252")
    raw = raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    return b"(" + raw + b")"


def build_pdf(objects):
    """Assemble numbered objects (1..n, object 1 is the catalog) into PDF bytes."""
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref_start = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\n" % (len(objects) + 1)
    out += b"startxref\n%d\n%%%%EOF\n" % xref_start
    return bytes(out)


def stream_object(dictionary, data):
    return dictionary + b" /Length %d >>\nstream\n" % len(data) + data + b"\nendstream"


def slide_content(heading, bullets):
    lines = [b"BT", b"/F1 %d Tf" % HEADING_SIZE]
    y = PAGE_HEIGHT - MARGIN - HEADING_SIZE
    lines.append(b"1 0 0 1 %d %d Tm" % (MARGIN, y))
    lines.append(pdf_string(heading) + b" Tj")
    lines.append(b"/F1 %d Tf" % BODY_SIZE)
    y -= 2 * BODY_LEADING
    for bullet in bullets:
        wrapped = textwrap.wrap(bullet, WRAP_WIDTH)
        for index, part in enumerate(wrapped):
            prefix = "• " if index == 0 else "  "
            lines.append(b"1 0 0 1 %d %d Tm" % (MARGIN, y))
            lines.append(pdf_string(prefix + part) + b" Tj")
            y -= BODY_LEADING
        y -= BODY_LEADING // 2
    lines.append(b"ET")
    return b"\n".join(lines)


def slides_pdf(slides):
    page_count = len(slides)
    # 1 catalog, 2 pages, 3 font, then (page, content) pairs.
    page_numbers = [4 + 2 * i for i in range(page_count)]
    kids = b" ".join(b"%d 0 R" % n for n in page_numbers)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, page_count),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    for page_number, (heading, bullets) in zip(page_numbers, slides):
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] "
            b"/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>"
            % (PAGE_WIDTH, PAGE_HEIGHT, page_number + 1)
        )
        objects.append(stream_object(b"<<", slide_content(heading, bullets)))
    return build_pdf(objects)


def scanned_pdf():
    """One page whose only content is a grey image with dark text-like bars."""
    width, height = 660, 510
    rows = []
    for y in range(height):
        row = bytearray(b"\xf2" * width)  # light paper grey
        if 40 <= y < 62:  # heading bar
            row[60:420] = b"\x28" * 360
        else:
            for line in range(12):
                top = 100 + line * 32
                if top <= y < top + 12:
                    length = 520 - (line * 37) % 160
                    row[60:60 + length] = b"\x3c" * length
        rows.append(bytes(row))
    image = zlib.compress(b"".join(rows), 9)
    content = b"q %d 0 0 %d 0 0 cm /Im1 Do Q" % (PAGE_WIDTH, PAGE_HEIGHT)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] "
        b"/Resources << /XObject << /Im1 5 0 R >> >> /Contents 4 0 R >>"
        % (PAGE_WIDTH, PAGE_HEIGHT),
        stream_object(b"<<", content),
        stream_object(
            b"<< /Type /XObject /Subtype /Image /Width %d /Height %d "
            b"/ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode"
            % (width, height),
            image,
        ),
    ]
    return build_pdf(objects)


def write_bytes(name, data):
    with open(OUT_DIR / name, "wb") as handle:
        handle.write(data)


def main():
    write_bytes("norwegian_lecture.pdf", slides_pdf(NORWEGIAN_SLIDES))
    write_bytes("english_lecture.pdf", slides_pdf(ENGLISH_SLIDES))
    write_bytes("scanned_lecture.pdf", scanned_pdf())
    with open(OUT_DIR / "mixed_language_notes.txt", "w", encoding="utf-8", newline="\n") as handle:
        handle.write(MIXED_NOTES)
    print(f"Wrote test data to {OUT_DIR}")


if __name__ == "__main__":
    main()
