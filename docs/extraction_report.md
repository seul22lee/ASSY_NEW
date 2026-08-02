# Extraction report

Reproducibility and quality record for the two source PDFs. Every figure here
comes from `build/*.meta.json` and `outputs/validation_report.json`, produced by
`scripts/extract_pdf_structure.py` and `scripts/validate_ontology.py`.

---

## 1. Source identification

| | Mott 6e | Shigley 10e |
|---|---|---|
| File | `Machine Elements in Mechanical Design.pdf` | `ad7608c18e740b0e402c025fa3187de8.pdf` |
| SHA-256 | `567ca2af8190cc8c441d608de1c05b2548c8857706d7d1cf1fc3e1ceb66123b5` | `d6bf6ca2206d12a2986e7378a89e0fd2f3a9d41c8cec211158a1ac5698b89d91` |
| Size | 36,189,012 bytes | 25,036,364 bytes |
| PDF pages | 873 | 1105 |
| Embedded title | "Machine Elements in Mechanical Design, 6e" | "Shigley's Mechanical Engineering Design 10th Edition" |
| Embedded author | Robert L. Mott | Richard G. Budynas, J. Keith Nisbett |
| Producer | Foxit PDF SDK DLL 3.1 (from Adobe InDesign CS6) | Foxit PDF SDK DLL 3.1 (from Adobe Acrobat 8.1) |
| Encrypted | no | no |
| Outline entries | 449 | 350 |
| Numbered chapters | 23 | 20 |
| Total extracted characters | 2,485,632 | 2,383,236 |

The SHA-256 is recorded in RDF on `ev:SourceDocument` and checked on every run,
so provenance cannot silently drift onto a different scan of the same edition.

The second file's embedded metadata contains promotional text from a file-sharing
site in its `subject` and `keywords` fields. This is noise from the file's
history, not bibliographic data; the pipeline takes its bibliographic facts from
`config/config.yaml`, not from the PDF metadata.

---

## 2. Text extractability — is OCR needed?

**No, and OCR was not run.** Both PDFs carry a usable embedded text layer.
Determined empirically, not assumed:

| | Mott 6e | Shigley 10e |
|---|---|---|
| Pages with < 40 extracted characters | 4 (0.5 %) | 11 (1.0 %) |
| Which pages | 0, 14, 16, 256 | 0, 2, 22, 106, 294, 371, 488, 582, 686, 946, 990 |
| Median characters per page (sampled) | 2,934 | 1,889 |
| Extraction errors | 0 | 0 |

The near-empty pages are covers, part-title pages and full-page figure plates —
pages that genuinely carry little or no text. None of them is a body-text page
whose text failed to extract.

OCR is therefore **disabled by default** in `config/config.yaml`
(`ocr.enabled: false`). Blanket OCR of ~2,000 pages would add cost and a second,
independent error source to a text layer that is already good. The extractor
flags `ocr_candidate` pages so that a future run can target only those regions if
a claim ever needs one.

---

## 3. Page-number handling

**The central discipline of this project: the PDF page index and the printed
page number are different things and are never conflated.**

| | Mott 6e | Shigley 10e |
|---|---|---|
| Page-label tree present | yes | yes |
| Roman-labelled front matter pages | 16 | 22 |
| Arabic-labelled pages | 856 | 1082 |
| First arabic page (PDF index) | 17 | 23 |
| Observed offset (index − printed) | **+16** | **+22** |

The offset is constant *within* each file and **different between them**. It
would differ again in a third source, and a book with unnumbered plates or a
restart in numbering would have no constant offset at all.

So the offset is never used. `ev:printedPage` is read from the PDF's own page
label tree via PyMuPDF's `Page.get_label()`. `ev:pdfPageIndex` is the 0-based
index. They are separate RDF properties with separate SHACL shapes.
`tests/test_mdkg.py::TestPageNumberPreservation` asserts both offsets *and*
asserts that they differ, precisely to document why neither may be hard-coded.

Non-arabic labels (`Cover`, `i`, `xvii`) are preserved in `ev:pageLabel` with
`ev:pageLabelStyle`, and `ev:printedPage` is left absent rather than being
forced into a number.

---

## 4. Text-layer integrity — the significant finding

### 4.1 Shigley 10e mis-maps mathematics glyphs

The Shigley PDF sets mathematics in `MathematicalPi`, `CMMI` and `Grk` fonts
whose glyphs are mapped to **unrelated ASCII code points**. Extracted text is
therefore not merely lossy — it is *wrong in a way that reads as plausible*.

Observed substitutions, confirmed by comparing extracted text against rendered
page images:

| Printed | Extracted as |
|---|---|
| `=` | `5` |
| `−` (minus) | `2` |
| `+` | `1` |
| `∂` | `0` |
| `∫` | `#` |
| `δ` | `d` |
| `σ` | `s` |
| `/` (in fractions) | `y` |

A real example, printed page 566 (PDF index 588), the bearing load-life
exponents:

| | |
|---|---|
| **Text layer says** | `• a 5 3 for ball bearings  • a 5 10y3 for roller bearings (cylindrical and tapered roller)` |
| **The page actually reads** | `a = 3 for ball bearings`, `a = 10/3 for roller bearings (cylindrical and tapered roller)` |

A pipeline that trusted the text layer here would record the exponent as "5" or
"10y3". Neither is a number a reviewer would immediately flag as absurd, which
is what makes this failure mode dangerous.

### 4.2 Mott 6e drops some glyphs

Mott's body text is clean and `=` renders correctly. Some mathematics glyphs —
prime marks in particular — are dropped: printed page 184 renders
`Estimating Actual Endurance Limit, s_n′` as `Estimating Actual Endurance Limit, sn = .`
Lossy, but not misleading in the same way.

### 4.3 How this is handled

Reliability is **measured per span**, not assumed per document. The extractor
computes the fraction of characters in a recognised mathematics font, and every
`ev:EvidenceSpan` carries a verdict:

| `ev:textIntegrity` | Spans in v0.1 | Rule |
|---|---|---|
| `reliable` | 87 | May be quoted |
| `partial-glyph-loss` | 3 | May be quoted with care; symbols may be missing |
| `glyph-mismapped` | 1 | **Must not be quoted or parsed.** Stored only for traceability |
| `unverified` | 0 | — |

Page-level flags: Mott 42 pages (4.8 %) above the math-font threshold, Shigley 74
pages (6.7 %).

**Every equation asserted in this ontology was transcribed from a rendered page
image, not from the text layer**, and records
`ev:transcriptionSource = "rendered-page-image"`. The equations so verified:

| Equation | Source | Verified reading |
|---|---|---|
| Mott (14–1) | printed p. 571 | `L₂/L₁ = (P₁/P₂)^k`, k = 3.00 ball, 3.33 roller |
| Mott (11–2) | printed p. 476 | `L_min = 2T/(τ_d·D·W)`, with `τ_d = 0.5·s_y/N` |
| Mott (11–9) | printed p. 480 | `T = 1000·N·R·h`, per inch of spline length |
| Shigley (11–1) | printed p. 566 | `a = 3` ball, `a = 10/3` roller |
| Shigley (7–48), (7–49) | printed p. 392 | `F_f = π·f·p·l·d`; `T = (π/2)·f·p·l·d²` |

`tests/test_mdkg.py::TestTextIntegrity` enforces that any equation claim whose
evidence is `glyph-mismapped` carries a transcription source.

Shigley's keyseat stress-concentration factors (printed p. 384) sit in
mis-mapped runs **and** are quoted by the book from an external reference. The
claim records the structure of the statement; **the numbers are deliberately not
reproduced**.

---

## 5. Structure preservation

The pipeline does not treat the books as undifferentiated text. Preserved:

| Structure | How | Counts |
|---|---|---|
| Document hierarchy | `build/<doc>.toc.json`, resolved to page ranges | 449 + 350 outline nodes |
| Chapter / section hierarchy | classified as part / chapter / section / front / back matter | 23 + 20 chapters |
| Page boundaries | one record per page with both page numbers | 873 + 1105 |
| Text blocks with coordinates | `build/<doc>.blocks.jsonl` | 28,917 + 31,624 |
| Numbered equations, tables, figures, examples | regex detection, marked caption-like when block-initial | 3,505 + 4,664 candidates |
| Fonts per block | for the integrity metric | all blocks |

The artifact detector is **recall-oriented and not authoritative**. It surfaces
candidate anchors for human curation; it never produces a claim. Of the 8,169
detected candidates, 35 numbered items are cited by v0.1 claims (21 equations,
8 tables, 5 figures, 1 example) — every one of them hand-confirmed.

---

## 6. Verification results

`scripts/validate_ontology.py` reopens both PDFs on every run:

| Check | Result |
|---|---|
| Evidence spans re-verified against the PDFs | **91 / 91 pass** |
| Recorded page label matches the PDF's own label | 91 / 91 |
| Stored excerpt still found on the recorded page | 91 / 91 |
| SHACL conformance | conforms |
| Custom checks | 13 / 13 pass |
| Unit tests | 57 / 57 pass |

The anchor-verification mechanism caught four bad anchors during authoring —
three where de-hyphenation wrongly merged a genuine hyphenated compound broken
at a line end (`standards-setting` → `standardssetting`), one case mismatch. The
matcher now tries a de-hyphenated match first and falls back to a
hyphenation-blind comparison, recording which matcher succeeded in
`match_mode`.

---

## 7. Known extraction limitations

1. **Table structure is not parsed.** Tables are detected by caption and cited
   by number; their cell contents are not extracted. Mott's Table 11–1 (key
   dimensions vs shaft diameter) and Table 14–4 (recommended design life) are
   cited, not reproduced. Docling was not used; for v0.1 the risk of a silently
   mis-parsed table exceeded the value of having its cells.
2. **Equations are not machine-parsed.** No SymPy round-tripping. Given the
   glyph mis-mapping in one source, parsing the text layer would produce
   confident nonsense. Symbolic expressions are analyst transcriptions from
   rendered images, and say so.
3. **Two-column reading order is not reconstructed.** Blocks are stored with
   coordinates, so column membership is recoverable, but the extractor does not
   linearise the page. Anchors are matched within a single block, which is why a
   seed anchor spanning two columns is rejected.
4. **Figures are not extracted as images.** Only captions and numbers.
5. **Hyphenation at line ends is ambiguous.** The PDF gives no way to
   distinguish a soft break inside `organiza-tions` from a real hyphen in
   `standards-setting` that lands at a line end. Handled by trying both, not by
   guessing.
6. **Cross-references are not resolved.** "See Reference 8" and "see Figure
   11–6" are text, not links.
7. **Coverage is a pilot.** 91 spans and 82 claims over ~1,978 pages. This is
   deliberate: v0.1 optimises for citation integrity over volume.

---

## 8. Reproducing this report

```bash
python3 -m pip install --user pymupdf rdflib pyshacl pydantic pint pyyaml pandas networkx

python3 scripts/extract_pdf_structure.py     # → build/
python3 scripts/build_evidence_spans.py      # → data/evidence_spans.jsonl  (fails on a bad anchor)
python3 scripts/build_claims.py              # → data/claims.jsonl
python3 scripts/build_coverage_map.py        # → data/coverage_matrix.csv, docs/source_coverage_map.md
python3 scripts/build_ontology.py            # → ontology/*.ttl, build/mdkg-full.ttl
python3 scripts/validate_ontology.py         # → shapes/ontology-shapes.ttl, outputs/validation_report.json
python3 scripts/generate_maps.py             # → outputs/*.mmd
python3 -m unittest discover -s tests -v
```

Every stage is idempotent: unchanged inputs reproduce byte-identical outputs.
Extraction of both books takes about 45 seconds.
