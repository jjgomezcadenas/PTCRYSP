# ARGOS artwork used for pbt_argos.tex

Source: user-provided `docs/ARGOS_Proton.pdf`. Page numbers include the title page.
Embedded images were extracted with `pdfimages`; selected regions were cropped with
`sips`. No scientific curves or anatomical overlays were modified.

| Asset | PDF page | Extraction / use |
| --- | --- | --- |
| argos_workflow.png | 8 | Full workflow image; reference for the simplified TikZ workflow. |
| argos_range_uncertainty.png | 9 | Full range-uncertainty illustration, retained as source. |
| argos_range_errors.png | 9 | Upper two panels, crop x=40, y=164, width=1456, height=384 pixels. Used on content slide 4. |
| argos_clinical_examples.png | 10 | Full clinical-examples illustration, retained as source. |
| argos_brain_skullbase.png | 10 | Brain/skull-base illustration, crop x=49, y=244, width=216, height=260 pixels. Used on content slide 2. It is not labelled as an ependymoma case. |
| argos_pet_compton_comparison.png | 12 | Full comparison image; reference for the new comparison table. |
| argos_compton_illustration.png | 12 | Detector illustration unchanged, crop x=36, y=333, width=416, height=360 pixels. Used on content slide 6. |
| argos_pet_illustration.png | 12 | Detector illustration unchanged, crop x=784, y=333, width=410, height=360 pixels. Used on content slide 6. |

The source PDF does not supply separate provenance for each anatomical image.
The original overlays are retained as illustrative material.

Existing external assets reused:

- `proton_therapy_bragg.png`: Wikimedia Commons, BraggPeak-en.svg,
  D. Ilyin / A. A. Miller, CC0. Schematic depth-dose illustration.
  https://commons.wikimedia.org/wiki/File:BraggPeak-en.svg
- `prompt_gamma_compton_koide2018.jpg`: Koide et al., Scientific Reports 8,
  8116 (2018), Figure 2, CC BY 4.0. Measured prompt-gamma image/profile and
  simulated proton energy deposition, 70 MeV protons in spaced PMMA slabs.
  https://doi.org/10.1038/s41598-018-26591-2
- `dose_activity.png` and `ependymoma_mri.png`: inherited from the original
  PTCRYSP presentation.

Content slides are numbered 1–27; the title page is unnumbered.

Slide 6 retains the four bibliographic entries supplied on ARGOS page 12,
reformatted as LaTeX text. Their exact bibliographic details have not been
verified. In particular, the matching Safavi nozzle-mounted Compton-camera
paper is available at https://arxiv.org/abs/2606.03978, rather than the
Nature Communications entry printed in ARGOS. These references require
checking before external circulation. The commercial-status sentence is
limited to no dedicated commercial solution identified in the search,
not an established absence of all commercial products.

## CRYSP and COCOA slides

Content slides 15 and 16 adapt source PDF pages 3 and 4. Detector illustrations
were cropped without alteration from embedded 1672 × 941 pixel artwork:

| Asset | Source page | Crop (x, y, width, height) |
| --- | --- | --- |
| crysp_crystal.png | 3 | 40, 350, 260, 300 |
| crysp_monolithic.png | 3 | 600, 330, 260, 340 |
| crysp_ring.png | 3 | 1110, 326, 330, 334 |
| cocoa_scatterer.png | 4 | 35, 260, 470, 326 |
| cocoa_absorber.png | 4 | 580, 266, 486, 316 |
| cocoa_satellite.png | 4 | 1104, 234, 530, 361 |

References checked against the papers:
https://doi.org/10.1088/1361-6560/ae35c8
https://doi.org/10.1016/j.astropartphys.2025.103135

## Deployment and clinical-trial slides

Slides 21 and 22 reproduce embedded artwork from source PDF pages 6 and 7.
`proton_facilities_world_2021.png`, `proton_facilities_europe.png` and
`proton_patients_europe.png` are from page 6; `proton_trials_indications.png`
and `proton_trials_phase3.png` are from page 7. No plotted data were modified.
The world map is dated April 2021. The European patient graph attributes
its data to PTCOG, without an underlying table. The trial graphics cite
trial.gov, with July 2026 on the phase III chart; the slide provides no
registry identifiers or search criteria. These quantitative series have
not been independently verified; this is indicated in the draft slides.
