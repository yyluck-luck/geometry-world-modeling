# Full-target visual evidence

Prepared while generation is running; no target/output pixels read and no visual exported yet.

This is a supporting experimental image grid, using figure-designer's experimental-results, labelling and honest-comparison guidance. Four columns retain targets20–23 in fixed order; four rows show real reference, A0, A1 exact-repeat attempt and B. Every generated cell receives the already-fixed full-frame MSE. The footnote reports replay and signed aggregate difference, with known-sequence/GT-camera/ft-mse/no-novelty limits. There is no invented method label, selected crop, normalization, highlight claiming a winner or variance estimate from one repeat.

Individual PNGs retain576² native uint8 pixels and undergo decoded-byte readback. A288²-per-cell overview uses LANCZOS only for readability; native images remain available. SVG contains vector labels and embeds original raster images. Real RGB observations are intrinsically raster, so preserving their exact pixels is the appropriate exception to the skill's blanket vector-only artwork recommendation. No generative image tool modifies evidence. Final root visual inspection remains pending actual scores and export.

Use existing Python/NumPy/Pillow; Matplotlib is absent from both project and bundled artifact runtimes, and no package installation is needed for a labelled photo grid. Run only after the completed generation has been independently accepted, root score sealed and independent integer verification passed. Exporting images is evidence presentation, not a new experiment.
