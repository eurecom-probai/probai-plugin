# Venue dimensions

These presets describe the listed templates, verified on 2026-11-09. Use the actual manuscript's dimensions for modified layouts or other template versions. All dimensions below are inches; body sizes are TeX points.

| Key | Template | Body | Text width | Column width | Column gap |
| --- | --- | ---: | ---: | ---: | ---: |
| `icml` | ICML 2026, style dated 2025-10-29 | 10 | 6.75 | 3.25 | 0.25 |
| `iclr` | ICLR 2026 | 10 | 5.5 | 5.5 | N/A, single column |
| `aistats` | AISTATS 2026 Paper Pack | 10 | 6.75 | 3.25 | 0.25 |
| `neurips` | NeurIPS 2026 | 10 | 5.5 | 5.5 | N/A, single column |
| `tmlr` | TMLR main branch, retrieved 2026-11-09 | 10 | 6.5 | 6.5 | N/A, single column |

## Official sources

- [ICML 2026 style archive](https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip): `icml2026.sty` sets text width, column separation, and normal font size. The column width is `(6.75 - 0.25) / 2`.
- [ICLR 2026 style](https://github.com/ICLR/Master-Template/blob/master/iclr2026/iclr2026_conference.sty): `textwidth` is 5.5 inches and `normalsize` uses 10 pt type with 11 pt leading.
- [AISTATS 2026 Paper Pack](https://aistats.org/aistats2026/AISTATS2026PaperPack.zip), linked from the [official call](https://virtual.aistats.org/Conferences/2026/CallForPapers): `aistats2026.sty` sets geometry and normal font size; `sample_paper.tex` also specifies 3.25-inch columns.
- [NeurIPS 2026 style archive](https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip), linked from the [official call](https://neurips.cc/Conferences/2026/CallForPapers): `neurips_2026.sty` sets 5.5-inch text width and 10 pt normal text.
- [TMLR style](https://github.com/JmlrOrg/tmlr-style-file/blob/main/tmlr.sty) sets 6.5-inch text width; the [sample manuscript](https://github.com/JmlrOrg/tmlr-style-file/blob/main/main.tex) selects a 10 pt article. The style header records January 2021; the retrieval date identifies the snapshot used here.

## Resolve dimensions

Use explicit final dimensions first, then manuscript measurements, then a venue preset. Without a venue or manuscript, use a 3.25-inch figure width and 10 pt body text. For an unsupported venue, obtain manuscript measurements or explicitly choose the generic fallback.

Read `\textwidth`, `\columnwidth`, and the local `\linewidth` in the intended containing environment. When values depend on TeX macros, obtain resolved dimensions from the manuscript's build or a small measurement document using its class and style. Convert TeX points to inches by dividing by **72.27**. Matplotlib font sizes use its own point convention; use the nominal 8/7 pt styling sizes without geometrical conversion.

Set the figure's width directly from the selected column or text width. For a minipage, multiply its parent container width by the minipage fraction once. If the measurement is already the final local `\linewidth`, use it directly.

Examples: an ICML column is 3.25 inches; an ICML full-width figure is 6.75 inches; a 48% ICLR minipage is `5.5 * 0.48 = 2.64` inches. Use these concrete values in `figsize`. Keep this reference as sizing guidance; implement only the dimensions needed by the current figure.

Subplot rows and columns control panels inside that canvas. They do not select manuscript columns. Allocate 2 inches per subplot row, including labels and short titles, then add measured height for a shared legend. Keep equal aspect when required by the data.

Include the PDF at its intended width, for example `\includegraphics[width=\linewidth]{figures/result.pdf}` inside the measured column or minipage. Preserve the exported PDF page size; automatic tight cropping changes the resulting scale. Other venues and future template versions require their own measurements.
