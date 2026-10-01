# -*- coding: utf-8 -*-
"""
Manuscrito en ingles para el Journal of Computer Applications in Archaeology.

JCAA no impone plantilla ni tipografia —maqueta la editorial— pero si exige una
estructura de cierre que VAR no pide: accesibilidad de los datos, intereses en
competencia, contribuciones de autoria y declaracion de uso de IA. El fichero es
ciego: solo titulo y resumen, sin nombres ni afiliaciones.

Normas aplicadas:
  - menos de 8 500 palabras, referencias incluidas
  - resumen de 300 palabras como maximo y hasta seis palabras clave
  - encabezados numerados, tres niveles como maximo, menos de 75 caracteres
  - titulo y encabezados de primer nivel en Title Case
  - ingles britanico o estadounidense, sin mezclar
"""
import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(BASE, "results", "figuras")
OUT = os.path.join(BASE, "JCAA_manuscript.docx")

BLACK = RGBColor(0, 0, 0)
FONT = "Times New Roman"

doc = Document()
for s in doc.sections:
    s.left_margin = s.right_margin = Cm(2.5)
    s.top_margin = s.bottom_margin = Cm(2.5)

st = doc.styles["Normal"]
st.font.name = FONT
st.font.size = Pt(11)
st.paragraph_format.space_after = Pt(8)
st.paragraph_format.line_spacing = 1.5


def run(p, t, size=11, bold=False, italic=False):
    r = p.add_run(t)
    r.font.name = FONT
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    r.font.color.rgb = BLACK
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    return r


def P(t="", size=11, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
      after=8, before=0, spacing=1.5):
    p = doc.add_paragraph()
    if t:
        run(p, t, size, bold, italic)
    pf = p.paragraph_format
    pf.alignment = align
    pf.space_after = Pt(after)
    pf.space_before = Pt(before)
    pf.line_spacing = spacing
    return p


def H(t, level=1):
    size = {1: 13, 2: 12, 3: 11}[level]
    return P(t, size=size, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT,
             before=14 if level == 1 else 10, after=6, spacing=1.15)


def table(label, caption, cols, rows):
    p = doc.add_paragraph()
    run(p, label + " ", 10, bold=True)
    run(p, caption, 10)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.0
    t = doc.add_table(rows=1, cols=len(cols))
    t.style = "Table Grid"
    for i, c in enumerate(cols):
        cell = t.rows[0].cells[i]
        cell.text = ""
        run(cell.paragraphs[0], c, 10, bold=True)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            run(cells[i].paragraphs[0], str(v), 10)
            cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()


def figure(fname, label, caption, width=15.0):
    doc.add_picture(os.path.join(FIG, fname), width=Cm(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph()
    run(p, label + " ", 10, bold=True)
    run(p, caption, 10)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(12)
    p.paragraph_format.line_spacing = 1.0


# ----------------------------------------------------------------- title page
P("Computational Symmetry in Andean Textile Iconography: Frieze Group Analysis "
  "of Open-Access Digitised Collections",
  size=15, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=16, spacing=1.15)

H("Abstract", 1)
P("Symmetry group classification offers a formal description of ornament that does not depend on "
  "iconographic interpretation: a periodic band necessarily belongs to one of seven frieze groups, "
  "and the assignment is a geometric property of the design rather than a reading by the analyst. This "
  "paper applies an automatic frieze group detector to a corpus of 866 Andean textiles assembled from "
  "three open-access museum collections, all released under CC0. The detector is first validated on 84 "
  "synthetic patterns of known group, degraded with noise, blur and shear, reaching 92.9% accuracy. "
  "Sensitivity analysis identifies shear as the only critical degradation: a shear of 0.03, under two "
  "degrees and invisible in a catalogue photograph, drops the correlation of an exact reflection from "
  "1.00 to 0.51, which motivates a rectification step driven by the translation lattice. On the real "
  "corpus, 242 pieces (28%) show periodicity sufficient for group assignment. The distribution of "
  "groups differs markedly between cultures (permutation test, p = 0.0007; Cramér's V = 0.363) and "
  "follows a chronological order across horizons (p = 0.0003; V = 0.351). Nasca concentrates 76% of its "
  "pieces in p2mm, the group of maximal symmetry, whereas Wari shifts 54% towards p2mg, where "
  "reflection is replaced by a glide. The paper also documents a measurement artefact relevant to any "
  "computational work on textiles: the thread grid competes with the periodicity of the design and, "
  "since plain weave exhibits p2mm symmetry, biases results towards the most symmetric group. "
  "Correcting it does not weaken the observed association but strengthens it, and restores robustness "
  "to the exclusion of pieces whose museum attribution is uncertain.")
P("Keywords: Andean iconography; frieze groups; symmetry; pre-Columbian textiles; digital heritage; "
  "computer vision", italic=True, after=16)

# ------------------------------------------------------------------ 1
H("1. Introduction", 1)
P("Symmetry analysis occupies an unusual position among methods for describing ornament: it is formal, "
  "exhaustive and independent of interpretation. Any pattern repeating along one direction belongs to "
  "exactly one of seven frieze groups, and any pattern repeating along two independent directions to "
  "one of seventeen wallpaper groups. Washburn and Crowe (1988) turned this classification into a "
  "systematic instrument for the cultural comparison of designs, where the question is not what a motif "
  "represents but how it repeats.")
P("In the Andean field, Frame (1991, 2006) has shown that repetition structure is not ornament added to "
  "cloth but a consequence of how cloth is built, so that design symmetry and textile structure "
  "determine one another. That link between geometry and manufacture is what makes symmetry analysis "
  "more than a formal taxonomy for this particular material.")
P("On the computational side, Liu, Collins and Tsin (2004) established the reference procedure for "
  "automatically detecting the translation lattice and assigning a symmetry group from an image. Their "
  "work, however, addresses patterns photographed for that purpose. Applying it to museum catalogue "
  "photography — fragmentary pieces, hung, deformed and not always frontal — requires adaptations that "
  "form part of the contribution of this paper.")
P("Systematic application to Andean material has been limited by access to images. That obstacle has "
  "receded: several museums now publish their holdings under CC0 with structured metadata and "
  "programmatic access. This paper exploits that opening to build a reproducible corpus and apply a "
  "validated detector to it.")
P("The contribution is threefold. First, a corpus of 866 images of Andean textiles with normalised "
  "provenance, entirely CC0 and reconstructible from published code. Second, a frieze group detector "
  "robust to the degradations characteristic of catalogue photography, with its synthetic validation "
  "and an analysis of which degradation breaks it. Third, evidence that the distribution of symmetry "
  "groups differs significantly between Andean cultures, and is chronologically ordered.")

# ------------------------------------------------------------------ 2
H("2. Materials and Methods", 1)
H("2.1. Sources and inclusion criteria", 2)
P("Four open-access repositories were consulted. Table 1 summarises what each yielded.")
table("Table 1.", "Repositories consulted and their yield.",
      ["Source", "Access", "Pieces with image", "Licence"],
      [["The Metropolitan Museum of Art (Open Access dump)", "No key", "592", "CC0"],
       ["Cooper Hewitt (Smithsonian)", "Free key", "141", "CC0"],
       ["Cleveland Museum of Art", "No key", "133", "CC0"],
       ["Zenodo", "No key", "0 (datasets, not object images)", "CC-BY / CC0"],
       ["NMAI (Smithsonian)", "Free key", "0", "metadata CC0"]])
P("A piece enters the corpus if its declared provenance is Andean and its support is textile. Provenance "
  "is evaluated over the culture, country, region, subregion and excavation fields; country names match "
  "by prefix and culture names require a whole word with an optional adjectival suffix.")

H("2.2. Two findings about open-access infrastructure", 2)
P("The National Museum of the American Indian, the largest Andean collection consulted, releases its "
  "metadata as CC0 but does not distribute the images. Of 6,390 records retrieved, only 7 carried a "
  "media block; the indexed field marks 'Images' for all of them, but 5,921 also mark 'Catalog cards', "
  "so what has been digitised is the record, not the object. A direct query by unit returns 180 records "
  "with CC0 media across the entire museum. The distinction between open metadata and open images does "
  "not appear in the interface documentation , and it decisively constrains how a corpus can be planned.")
P("The second finding is a construction risk. A substring filter over culture names returned 10,309 "
  "pieces; the term 'ica', from the Ica culture of the Peruvian south coast, occurs inside 'Amer-ica-n' "
  "and pulled in 7,691 United States garments from the costume department. With word boundaries the "
  "corpus falls to 1,158. This is a ninefold inflation that passes unnoticed unless the departmental "
  "breakdown is inspected.")

H("2.3. Final corpus", 2)
P("After excluding supports without an iconographic surface — spindles, needles, metal ornaments — and "
  "pieces below 0.3 megapixels, the analysis corpus comprises 866 images. Five cultures exceed 70 "
  "pieces: Wari 109, Paracas 88, Chimú 76, Nasca 75 and Ica 72.")

H("2.4. Periodicity detection and rectification", 2)
P("Each image is converted to greyscale, the featureless border of the photograph is cropped away, and the result is "
  "normalised. Normalised autocorrelation by Fourier transform provides the translation vectors: local "
  "maxima reaching at least 80% of the highest peak away from the origin are accepted as candidates, "
  "and the shortest is retained. A high relative threshold is necessary because a pattern with 180-degree "
  "rotation produces an intermediate peak at half a cell, and admitting it leads to taking half the true "
  "period.")
P("The lattice vector also reveals the tilt of the piece in the photograph: in a band it should be "
  "horizontal, and any deviation reveals a rotation. The image is rectified by that angle before "
  "symmetries are measured, so that the axes of the design align with those of the image.")

H("2.5. Scoring symmetry operations", 2)
P("Each symmetry operation is scored as the maximum normalised correlation between the image and its "
  "transform, maximised over translations by circular correlation and over a small grid of affine "
  "corrections. Maximising over translations is essential: a symmetry axis may lie anywhere in the "
  "pattern, and comparing without allowing displacement detects the symmetry only when the framing "
  "happens to centre it.")
P("That same maximisation creates a problem: it absorbs the half-cell translation that distinguishes a "
  "glide from a reflection, so both score equally. Discrimination is recovered by retaining the argument "
  "of the maximum and measuring its phase relative to the period. An optimal displacement that is a "
  "multiple of the period indicates a pure reflection; one at half a cell, a glide. Without this "
  "correction, p11g and p2mg become indistinguishable from p11m and p2mm, which would invalidate the "
  "principal result of this work.")
P("The decision threshold is not a global constant but a fraction of the correlation the image itself "
  "attains under translation by its lattice vector. That value is the ceiling of the method: if the "
  "piece is worn or deformed, not even its own translation reaches high correlation, and demanding more "
  "of a reflection would make no sense. The fraction was set at 0.70 by a sweep over the synthetic "
  "patterns, with a flat optimum between 0.65 and 0.70. A lower bound on spurious correlation is also imposed, "
  "estimated by rotations to non-crystallographic angles, which prevents the regularity of the weave "
  "from being mistaken for symmetry of the design.")

H("2.6. Synthetic validation", 2)
P("No symmetry label exists against which to check real photographs, so the only evidence that the "
  "detector measures what it claims comes from cases whose answer is known. Eighty-four periodic bands were "
  "built, twelve per frieze group, applying each group's generators to a fundamental domain of verified "
  "asymmetry, and degraded with noise, blur and shear.")
table("Table 2.", "Recovery accuracy by frieze group (n = 12 per group).",
      ["Group", "Accuracy", "Group", "Accuracy"],
      [["p1", "100%", "p2", "92%"],
       ["p11m", "100%", "p11g", "83%"],
       ["p2mg", "100%", "p1m1", "75%"],
       ["p2mm", "100%", "Overall", "92.9%"]])
P("Sensitivity analysis against the degradations, shown in Figure 1, identifies shear as the only "
  "critical degradation. Noise and blur leave the correlation of an exact reflection at 0.99 and 1.00 "
  "respectively. A shear of 0.03 — under two degrees, indistinguishable by eye in a catalogue "
  "photograph — drops it to 0.51 if no correction is applied. The grid of affine corrections returns it "
  "to 0.82 and rectification by the lattice vector holds it at 0.80, both above the decision threshold. "
  "Across the validation as a whole, introducing rectification raised overall accuracy from 28.6% to "
  "85.7%, and subsequent threshold tuning brought it to 92.9%.")
figure("figura3_degradaciones.png", "Figure 1.",
       "Effect of each degradation on the correlation of an exact reflection, in a synthetic p11m "
       "pattern; mean of six replicates. Noise and blur are harmless; shear is "
       "what breaks detection, and the two corrections introduced keep it above the threshold up to "
       "values of 0.03.")

H("2.7. Statistical analysis", 2)
P("A permutation test on the chi-squared statistic with 10,000 resamples is used rather than the "
  "asymptotic test, because with six observed groups and cultures comprising some twenty pieces, many cells fall "
  "below five cases. Cramér's V accompanies it in order to separate the existence of the effect from its "
  "magnitude. All tests are repeated excluding pieces whose cultural attribution the source museum marks "
  "as uncertain, as a sensitivity analysis.")

# ------------------------------------------------------------------ 3
H("3. Results", 1)
H("3.1. Coverage", 2)
P("Of the 866 pieces, 242 (28%) show periodicity sufficient to receive a group assignment; 330 show no "
  "detectable periodicity and 294 show it too weakly. Most pieces with an assigned group have a "
  "one-dimensional lattice (227 of 242), that is, they correspond to bands rather than two-dimensional "
  "fields. Figure 2 shows two examples per group, those with the cleanest periodicity, so that the "
  "reader may judge the plausibility of the assignments.")
figure("figura1_ejemplos.png", "Figure 2.",
       "Corpus pieces by assigned frieze group. Two examples per group, ordered by correlation under "
       "translation (r). Note that the two p2mg examples are Wari chequerboard pieces, whose displaced "
       "repetition is visible to the naked eye.")

H("3.2. The weave artefact", 2)
P("A textile has two superimposed periodicities: the thread grid and that of the design. The former "
  "is far more regular and dominates the autocorrelation. In a first run without scale restriction, 29% "
  "of the pieces with an assigned group showed periods of 4 to 15 pixels, characteristic of the weave "
  "and not of the motif. The bias is not neutral: plain weave is a lattice with reflection in both axes, "
  "that is p2mm, precisely the group on which the interpretation rests.")
P("Restricting the minimum autocorrelation radius to 3% of the longer side, pieces with a period below "
  "15 pixels fall from 71 to 15 and the median period rises from 39 to 45 pixels. The effect on "
  "inference is the opposite of what might be feared: the artefact was masking the signal rather than "
  "producing it.")
table("Table 3.", "Effect of excluding the weave scale on the tests.",
      ["Test", "With weave", "Without weave"],
      [["Culture × frieze", "p = 0.046, V = 0.29", "p = 0.0004, V = 0.36"],
       ["Horizon × frieze", "p = 0.019, V = 0.29", "p = 0.0015, V = 0.33"],
       ["Culture × frieze, uncertain excluded", "p = 0.099 (n.s.)", "p = 0.0007, V = 0.36"]])
P("The last row is decisive for the credibility of the result: before the correction, the cultural "
  "association disappeared when pieces whose attribution the museum itself marks with a question mark "
  "were excluded. After the correction it survives and is even strengthened. Both versions of the "
  "results are preserved in the deposited material.")

H("3.3. Association between culture and symmetry group", 2)
P("Table 4 gives the distribution of frieze groups for the four cultures that exceed the threshold of "
  "20 pieces, and Figure 3 presents the same distribution as small multiples, in which the comparison "
  "between cultures is read along a single row across the four panels.")
table("Table 4.", "Distribution of frieze groups by culture, excluding pieces of uncertain attribution "
      "(n = 96; p = 0.0007; V = 0.363).",
      ["Culture", "p1", "p11m", "p1m1", "p2", "p2mg", "p2mm", "n"],
      [["Nasca", "5%", "—", "5%", "—", "14%", "76%", "21"],
       ["Wari", "—", "7%", "7%", "7%", "54%", "25%", "28"],
       ["Chimú", "21%", "12%", "12%", "4%", "4%", "46%", "24"],
       ["Ica", "9%", "4%", "22%", "—", "35%", "30%", "23"]])
figure("figura2_reparto.png", "Figure 3.",
       "Distribution of frieze groups by culture, as a percentage of pieces and excluding those of "
       "uncertain attribution (permutation test: p = 0.0007; Cramér's V = 0.363). Comparison between "
       "cultures is read along the same row across the four panels: the inversion between Nasca and Wari "
       "in the two lower rows is the principal result.")

# ------------------------------------------------------------------ 4
H("4. Discussion", 1)
H("4.1. Interpretation of the observed distribution", 2)
P("Nasca and Wari stand in sharp opposition. Nasca concentrates three of every four pieces in p2mm, the "
  "group of maximal symmetry among the friezes: reflection in the axis parallel to the translation, "
  "reflection in the perpendicular one, and half-turn rotation. Wari inverts the distribution and places "
  "more than half in p2mg, where the parallel reflection is replaced by a glide, that is, a reflection "
  "followed by half a cell of translation.")
P("The literature on Wari tapestry tunics describes design built by recombining a short repertoire of "
  "abstract motifs and by deliberate expansion and compression of those modules (Bergh 2012; "
  "Stone-Miller & McEwan 1990). It is worth being precise about the relation between that body of work "
  "and what is observed here: the preference for p2mg is not a confirmation of the documented "
  "distortion, which is a different phenomenon, but a new and compatible observation. Both point to a "
  "compositional logic based on displacing the module rather than mirroring it, but the formal "
  "equivalence between the two remains to be established and would be the natural object of a dedicated "
  "study.")
P("Chimú shows the most diverse distribution and is the only culture with an appreciable presence of p1, "
  "the group with no symmetry beyond translation. By chronological horizon (n = 127; p = 0.0003; "
  "V = 0.351) the progression is ordered: the Early Intermediate Period concentrates 75% in p2mm, the "
  "Middle Horizon shifts 47% to p2mg, and the Late Intermediate Period shows the most balanced "
  "distribution, with p2mm at 45%.")

H("4.2. Limitations", 2)
P("Coverage of 28% is the principal limitation. Part of it is genuine: much Andean iconography is "
  "figurative or of unique composition, and forcing a frieze label onto a non-periodic design would "
  "produce exactly the kind of result that does not withstand scrutiny. Part is a limitation of the "
  "method on fragmentary or poorly framed pieces: as Figure 2 shows, the analysis operates on the whole "
  "photograph, so background and museum mounting compete with the object.")
P("Periodicity in the valid pieces is imperfect: the median correlation under translation is 0.59, "
  "consistent with wear, deformation of the cloth and foreshortening in the photograph.")
P("A residual bias towards p2mm persists. Validation shows p1m1 confused with p2mm in 3 of 12 cases, so "
  "the observed predominance of p2mm should be read as an upper bound. The opposition between Nasca and "
  "Wari does not depend on it: it rests on p2mg, whose recovery in validation was complete.")
P("Samples per class are small, between 21 and 28 pieces. Only four cultures exceed the threshold of 20 "
  "pieces set for the test; Paracas, Inca, Moche and Chancay fall outside it despite being well "
  "represented in the corpus, because most of their pieces do not reach sufficient periodicity.")
P("Finally, the corpus comes from three United States collections. What reached those collections is not "
  "a random sample of Andean textile production but the outcome of a century of antiquities trade with "
  "preferences of its own, probably biased towards visually striking and well-preserved pieces. Any cultural reading "
  "of these distributions inherits that bias.")

# ------------------------------------------------------------------ 5
H("5. Conclusions", 1)
P("The distribution of symmetry groups differs between Andean cultures "
  "and with a moderate effect size, and is ordered chronologically by horizon. The opposition between "
  "the mirror symmetry of Nasca and the displacement of Wari is the sharpest finding and the most "
  "interpretable in terms of compositional practice.")
P("The immediate next step is to test whether symmetry descriptors predict cultural attribution better "
  "than a convolutional network over pixels, which would separate the contribution of geometric "
  "structure from that of colour and texture. Extending the corpus with the Art Institute of Chicago and "
  "the Penn Museum would raise the samples per class enough to include Paracas and Inca in the test. "
  "Finally, the most promising extension is to segment the decorated region before analysing it: since "
  "the method currently operates on the whole photograph, much of the 72% without a group may be due to "
  "the background rather than to an absence of periodicity in the piece.")

# ---------------------------------------------------- required closing matter
H("Data Accessibility Statement", 1)
P("All material supporting this work is deposited with persistent identifiers. The code and derived data "
  "— unified corpus with normalised provenance, group assignments with their descriptors, synthetic "
  "validation and statistical tests — are available at https://doi.org/10.5281/zenodo.22167721 under the "
  "MIT licence. The 1,193 corpus images, with their provenance manifest, are deposited as a separate "
  "data record at https://doi.org/10.5281/zenodo.22167857 under CC0. Development continues at "
  "https://github.com/vl4dimr/simetria-textil-andina.")
P("The images are archived in addition to publishing the code that harvests them, rather than instead of "
  "it, because the corpus is built by querying museum interfaces and those interfaces change: during "
  "this work the Metropolitan's interface blocked the requesting IP address after a burst of concurrent "
  "requests. A corpus that depends on several interfaces continuing to respond identically years from "
  "now would not be reproducible.")

H("Acknowledgements", 1)
P("[Left blank for peer review.]", italic=True)

H("Funding Information", 1)
P("This research received no specific grant from any funding agency.")

H("Competing Interests", 1)
P("The authors have no competing interests to declare.")

H("Authors' Contributions", 1)
P("[Author 1] contributed validation and investigation; [Author 2] contributed validation, investigation "
  "and supervision; [Author 3] contributed conceptualisation, methodology, software, formal analysis, "
  "resources, data curation, visualisation, project administration and the original draft. All authors "
  "contributed to reviewing and editing the manuscript and approved the submitted version. "
  "[Names withheld for blind review; supplied in the submission metadata.]")

H("Declaration of AI Use", 1)
P("Artificial intelligence tools (Claude, Anthropic) were used to assist in writing the harvesting code "
  "for the museum collections, implementing the symmetry detector, running the statistical analyses, "
  "generating the figures, and drafting an initial version of the text. All numerical results derive "
  "from executing that code over the data described and are reproducible from the deposited repository. "
  "The authors have verified the method, checked the results and reviewed the entire text, and take full "
  "responsibility for the content, including the accuracy of the references and the validity of the "
  "archaeological interpretations.")

H("References", 1)
for ref in [
    "Bergh, S E (ed.) 2012 Wari: Lords of the Ancient Andes. Cleveland: Cleveland Museum of Art / Thames "
    "& Hudson.",
    "Frame, M 1991 Structure, Image and Abstraction: Paracas Necrópolis Headbands as System Templates. "
    "In: Paracas Art and Architecture: Object and Context in South Coastal Peru. Iowa City: University "
    "of Iowa Press. pp. 110–171.",
    "Frame, M 2006 Elemental Pathways in Fiber Structures: Approaching Andean Symmetry Patterns through "
    "an Ancient Technology.",
    "Frame, M The Question of Symmetry in Andean Textiles. Textile Society of America Symposium "
    "Proceedings.",
    "Liu, Y, Collins, R T and Tsin, Y 2004 A Computational Model for Periodic Pattern Perception Based "
    "on Frieze and Wallpaper Groups. IEEE Transactions on Pattern Analysis and Machine Intelligence, "
    "26(3): 354–371.",
    "Stone-Miller, R and McEwan, G F 1990 The Representation of the Wari State in Stone and Thread: A "
    "Comparison of Architecture and Tapestry Tunics.",
    "Washburn, D K and Crowe, D W 1988 Symmetries of Culture: Theory and Practice of Plane Pattern "
    "Analysis. Seattle: University of Washington Press.",
]:
    p = P(ref, size=10, after=6, spacing=1.15)
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.first_line_indent = Cm(-1.0)

doc.save(OUT)

words = sum(len(p.text.split()) for p in doc.paragraphs)
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            words += len(c.text.split())
print("Manuscrito JCAA ->", OUT)
print("palabras: %d (límite 8 500)" % words)
