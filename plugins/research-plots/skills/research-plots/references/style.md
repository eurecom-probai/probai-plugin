# Figure style

Apply Seaborn's white paper theme first, explicit defaults second, and figure-specific overrides last. The [shared configuration](../assets/_config.py) implements these settings. Use it as a starting point when the project needs common defaults. Keep project-wide category mappings and style settings in this module.

## Simple figure scripts

Write each script for its specific figure, with minimal custom functions. Straight-line plotting code or one `main()` is usually enough. Keep data loading, concrete figure dimensions, panel arrangement, labels, and legend adjustments visible in that script. Use existing project conventions and avoid general-purpose plotting utilities.

The optional `_config.py` holds visual defaults and one explicit setup function. Apply the defaults inside `plt.rc_context()`, then fine-tune the figure directly:

```python
import matplotlib.pyplot as plt
import _config as plot_config

with plt.rc_context():
    plot_config.configure_style()
    plt.rcParams["lines.linewidth"] = 1.4
    fig, axes = plt.subplots(1, 2, figsize=(6.75, 2.0))
    # Draw this figure's data and arrange its legend here.
    plt.close(fig)
```

These names and this structure are examples. Preserve existing project utilities where they already serve the figure. Keep a copy of the local configuration alongside scripts that import it when sharing them.

## Typography and axes

Use Computer Modern Sans text and serif mathematics. For document body size `b`, labels and short panel titles use `max(7, 8*b/10)` pt; ticks, annotations, and offset text use `max(7, 7*b/10)` pt. Legend text and titles use the smaller `max(6, 6*b/10)` pt size. Font sizes stay constant across panel layouts. Use regular weight, short panel titles when useful, panel letters when manuscript references require them, and no overall figure title by default.

| Setting | Default |
| --- | --- |
| Figure and axes background | White |
| Text, ticks, spines | `#262626` |
| Grid | Off |
| Top and right spines | Hidden |
| Spine width | 0.6 pt |
| Major tick padding | 1 pt on both axes |
| Major tick width and length | 0.5 pt and 2.5 pt |
| Tick direction | Outward |
| Minor ticks | Off; enable when useful for the scale |
| Autoscale margins | x: 0.02, y: 0.05 |
| Lines and markers | 1.2 pt lines; approximately 3 pt line markers |
| Figure DPI | 500 |
| Export DPI | `"figure"` |

Margins apply to autoscaled axes. Preserve explicit limits, meaningful zero baselines, image extents, and equal-aspect requirements. Reduce redundant ticks and labels before changing readable font sizes. Explicitly label quantities and units.

## Palette and normalization

Use this categorical order: blue `#0072B2`, vermilion `#D55E00`, green `#009E73`, purple `#CC79A7`, orange `#E69F00`, sky blue `#56B4E9`, dark gray `#4D4D4D`. Assign colors by category name and preserve the mapping across figures. Use neutral gray for reference elements when appropriate. Combine colors with markers and dash patterns for additional series or improved distinguishability.

Use `viridis` for sequential values and Seaborn's `vlag` for diverging values around a meaningful center. Obtain the latter with `sns.color_palette("vlag", as_cmap=True)`. Select normalization from the task and data; signed quantities need an explicit meaningful center. Use shared normalization for directly comparable panels.

## Framed legends

Use a white face, opacity 1, `#B0B0B0` edges, rounded corners (`legend.fancybox=True`, `LEGEND_ROUNDING_SIZE=0.4`), and a 0.5 pt frame. Apply the corner radius directly to the legend artist with `legend.get_frame().set_boxstyle("round", pad=0, rounding_size=0.4)`. The radius uses legend font-size units; zero extra box padding preserves compact spacing. Set the frame linewidth on the legend artist; Matplotlib has no dedicated legend frame linewidth rcParam.

| rcParam | Value |
| --- | ---: |
| `legend.labelspacing` | 0.2 |
| `legend.handletextpad` | 0.4 |
| `legend.borderaxespad` | 0.2 |
| `legend.markerscale` | 0.75 |
| `legend.handlelength` | 1.5 |
| `legend.handleheight` | 0.5 |
| `legend.borderpad` | 0.3 |
| `legend.columnspacing` | 1.2 |

Place single-panel legends in available whitespace and inspect for data occlusion. Shared entries across panels usually belong in a single legend above the grid. Use panel-specific legends for different entries. Measure shared legend height and add a separate band above the 2-inch rows; reduce legend columns or wrap labels if the legend exceeds the canvas width. The learning-curve example measures this band directly and leaves 0.04 inches above and 0.06 inches below it. Adapt the layout directly for the figure at hand.

Legend markers use 75% of the source marker size, and shorter handles and compact padding keep the box proportional to the 6 pt text. Spacing and handle dimensions use Matplotlib's font-relative units. Override marker scaling for quantitative size legends when needed.

Adapt handles to the chart: line samples for lines, patches for filled regions, readable point sizes for scatter. Increase scatter legend opacity independently of data opacity when useful. Keep quantitative size encodings accurate when the legend represents point sizes.

## Plot-specific choices

- **Lines:** preserve observation order unless sorting is part of the task. Use sparse markers and dash patterns when they improve identification. Preserve supplied uncertainty bands and use matching colors with restrained transparency.
- **Scatter:** adapt point area and opacity to density. Matplotlib's scatter `s` uses square points; a 3 pt marker corresponds approximately to `s=9`. Use shapes where useful, and selectively rasterize dense collections.
- **Bars and distributions:** preserve category order, supplied summaries, and error bars. Explicitly configure statistical estimation. For raw distributions, any density estimation or binning choice belongs to the task.
- **Heatmaps and images:** label colorbars, share comparable scales, preserve meaningful aspect ratios, and adapt ticks and spines to the structure.

For Seaborn line plots of supplied observations, use `estimator=None`, `errorbar=None`, and `sort=False` where applicable. Other Seaborn plot types have their own statistical defaults; inspect them before choosing the function. Preserve supplied values and uncertainty definitions.

## LaTeX and export

Determine availability solely with `shutil.which("latex")`: enable LaTeX when the executable is on `PATH`. Set `text.usetex` directly if the task requests a different choice. Rendering and macro errors surface during figure generation.

When the executable is absent, report the reason and selected font: installed Computer Modern Sans, then Latin Modern Sans, then bundled DejaVu Sans. Native math uses `mathtext.fontset="cm"`. Native mathtext supports a subset of LaTeX; resolve unsupported labels explicitly. Do not silently switch backends after a real figure's label or macro error.

The examples use an Agg canvas for layout metrics and `draw_without_rendering()` to avoid rasterizing text while measuring. PDF output uses the PDF backend. This keeps PDF LaTeX rendering independent of the additional `dvipng` dependency used for Agg image rendering. A later PNG preview may require its own toolchain or a PDF rasterizer.

Save PDF with a white background and the configured canvas dimensions. Set `savefig.bbox=None` to override any ambient tight-cropping setting. Preserve vector text and geometry; use 500 dpi for selectively rasterized artists. Native PDF fonts use TrueType embedding (`pdf.fonttype=42`); LaTeX uses its own font embedding. Close the figure after export.

Inspect final PDFs at their printed size for clipping, label overlaps, legend occlusion, font substitutions, consistent categories and scales, and fidelity to supplied data. Temporary previews support review; PDF remains the delivered format unless another format is requested.

## Library references

- [Matplotlib LaTeX rendering](https://matplotlib.org/stable/users/explain/text/usetex.html)
- [Matplotlib layout padding](https://matplotlib.org/stable/api/_as_gen/matplotlib.figure.Figure.tight_layout.html)
- [Seaborn color palettes](https://seaborn.pydata.org/tutorial/color_palettes.html)
