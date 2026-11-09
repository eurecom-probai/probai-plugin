---
name: research-plots
description: Create or revise scientific plots and publication figures with Matplotlib and Seaborn, including manuscript sizing, multi-panel layouts, typography, legends, and PDF export. Use for Python research figures and paper plots.
---

# Research Plots

Produce one Python script per exported figure, including multi-panel figures, using a small shared project-local `_config.py` when common defaults are useful. Use Matplotlib and Seaborn and deliver PDF by default. Preserve the task's data selection, aggregation, smoothing, and uncertainty definitions. Ask when a missing scientific choice materially changes the result.

## Prepare the figure

1. Inspect the data, existing plotting code, manuscript, and project conventions. Identify final placement, panel arrangement, and supplied statistical summaries.
2. Read the [style reference](references/style.md). For document geometry, read the [venue reference](references/venues.md). Explicit task settings take priority, followed by manuscript measurements, venue presets, and generic defaults.
3. Use the [shared configuration](assets/_config.py) and [figure template](assets/figure_template.py) as optional starting points. Preserve existing project conventions and keep the project independent of this plugin. Put common visual defaults in `_config.py`; keep data loading, dimensions, panels, labels, and local adjustments in each figure script.
4. Use explicit figure and axes objects, with Seaborn axes-level functions where appropriate. Apply the Seaborn theme, then the style defaults, then task-specific overrides. Make estimation explicit: for supplied line observations, use `estimator=None`, `errorbar=None`, and `sort=False` when applicable.

## Keep the code simple

Write code for the specific figure. Keep the number of custom functions to the minimum: straight-line code or a single `main()` is usually enough. Add a helper only when it materially clarifies the current script. Use direct Matplotlib and Seaborn calls, concrete dimensions, and a few local variables. Keep common styling in a small configuration file when several figures share it.

Avoid building reusable plotting utilities, generic loaders, classes, configuration schemas, dispatchers, or wrappers for individual library calls. Support the actual data and layout needed by the task. Treat the bundled files as editable examples; helper names, function signatures, and internal structure are optional.

## Layout and rendering

- Generate at the final insertion width. Distinguish manuscript columns from subplot columns and apply minipage fractions once. Use 2 inches per subplot row, including labels and short titles, plus measured space for shared legends.
- Use Computer Modern Sans text, serif mathematics, compact document-relative fonts, the explicit palette, no grid, and framed legends. Preserve category mappings across related figures.
- Select LaTeX once per execution using only `shutil.which("latex")`. Enable LaTeX when the executable is on `PATH`; otherwise use the documented font fallback with a notice. Rendering and macro errors surface during figure generation.
- Apply shared styling explicitly before creating artists, then set any local rcParams. Use `plt.rc_context()` to contain style changes. Keep backend selection in the figure script and common visual values in the project configuration. Follow project path conventions. Use the project's Python environment; the bundled examples run with `uv` and declare their dependencies inline.
- Save one descriptive PDF with vector text and geometry, 500 dpi for rasterized artists, a white background, and the configured physical dimensions. Close the figure after export.

## Inspect and deliver

When generating an actual figure, render it and inspect it at the intended printed size. Temporary preview images may support inspection. Check physical dimensions, readable text, clipping, overlaps, legends, colorbars, category assignments, comparable scales, and fidelity to supplied data and summaries. Resolve layout warnings and inspect the result again after corrections.

For crowding, adjust spacing, tick density, redundant labels, legend arrangement, or figure dimensions while preserving readable fonts. Preserve equal-aspect requirements for spatial plots and images. Use short panel titles when useful, letters when manuscript references require them, and no overall title by default.

Deliver the figure script, any project-local configuration it imports, and the PDF. State any LaTeX or font substitutions and relevant unresolved layout limitations. Provide an inclusion example when it helps the manuscript use the intended width. Explicit task instructions override these defaults.
