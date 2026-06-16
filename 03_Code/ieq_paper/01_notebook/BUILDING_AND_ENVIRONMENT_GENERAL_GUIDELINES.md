Building and Environment — general manuscript formatting instructions
General formatting and style rules for preparing a LaTeX manuscript for Building and Environment.
These instructions are intended for manuscript editing, LaTeX generation, Python figure generation, table formatting, and final submission checks.
________________________________________
1. Target journal
Journal:
•	Building and Environment
•	Publisher: Elsevier
•	Typical article type: Original research article
The manuscript must be written as a complete scientific article with clear research motivation, rigorous methods, results supported by data, and a concise discussion of significance and limitations.
________________________________________
2. LaTeX document format
Use an Elsevier-compatible LaTeX template, preferably elsarticle.
Recommended review setup:
\documentclass[preprint,review,12pt]{elsarticle}
Use this review format unless there is a specific reason to use another Elsevier option.
Do not manually force a journal-production layout. Final typesetting is handled after acceptance.
Recommended packages:
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{siunitx}
\usepackage{amsmath}
\usepackage{lineno}
\usepackage{hyperref}
General rules:
•	Submit editable .tex source files.
•	Do not submit PDF as the only source file.
•	Double-column formatting is allowed for LaTeX submissions, but review/preprint format is usually easier to read.
•	Use double line spacing for review readability.
•	Do not manually override margins unless necessary.
•	Prefer the default margins from the Elsevier template.
•	If custom margins are unavoidable, use conservative review margins of about 2.5 cm / 1 inch.
•	Do not use decorative fonts.
•	Do not use underlined or strikethrough text unless scientifically meaningful.
•	Use consistent cross-references:
o	Fig.~\ref{fig:...}
o	Table~\ref{tab:...}
o	Section~\ref{sec:...}
o	Eq.~\eqref{eq:...}
________________________________________
3. Font and spacing
For LaTeX manuscripts:
•	Use 12 pt manuscript font in review mode.
•	Do not manually select a custom font unless the journal template requires it.
•	Keep line spacing double or review-friendly.
•	Use standard LaTeX heading styles.
•	Do not reduce font size to fit more text.
•	Do not use tiny table or figure text that becomes unreadable after scaling.
•	Avoid excessive footnotes.
•	Avoid dense paragraphs; scientific readability is more important than compressing length.
Recommended Python figure font sizes for manuscript graphics:
Prepare figures as final artwork, not as enlarged review-only graphics. Use 11 pt as the default figure text size for primary labels. The LaTeX manuscript may use 12 pt in review mode, but final figures should normally use 11 pt. Tick labels, dense annotations, and legends may be reduced to 9-10 pt when needed. Short panel headings may be 11-11.5 pt; use 12 pt only when a full-page figure genuinely needs it. Avoid long figure titles inside the plot when the caption already explains the figure.
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9.5,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})
For final figures, all labels must remain readable when inserted into LaTeX at single-column or full-page width.
________________________________________
4. Page layout and margins
Use the default layout of the Elsevier elsarticle template.
Do not manually change:
•	margins,
•	text width,
•	column width,
•	caption spacing,
•	heading spacing,
unless there is a clear technical need.
If custom page geometry is absolutely necessary for a draft, use simple review-style margins:
\usepackage[margin=2.5cm]{geometry}
Remove manual geometry changes before submission if they conflict with the Elsevier template.
________________________________________
5. Manuscript length
For an Original Research Article:
•	Maximum length: less than 10,000 words
•	References are not counted in this limit.
•	Tables and figures count toward the manuscript length.
Recommended internal target:
•	7,000–9,000 words for the main text.
•	Shorter is better if the argument remains complete.
General limits:
•	Keep total Figures + Tables ≤ 20.
•	Prefer fewer than 5 main tables.
•	Prefer fewer than 15 main figures.
•	Move secondary material to Supplementary Material.
________________________________________
6. General article structure
Use clearly numbered sections.
Recommended structure:
Title page
Abstract
Keywords
Highlights

1 Introduction
2 Materials and methods
3 Results
4 Discussion
5 Conclusions

Declaration of generative AI use, if applicable
CRediT author statement
Declaration of competing interest
Funding
Data availability
Acknowledgements
References
Appendix / Supplementary material
Alternative structures are acceptable if they remain clear and numbered.
Rules:
•	Number main sections as 1, 2, 3.
•	Number subsections as 1.1, 1.2, 2.1, etc.
•	Use 1.1.1 only when necessary.
•	Do not include the abstract in section numbering.
•	Use section numbers when cross-referencing.
•	Avoid vague references such as “the text above” or “the following section” when a numbered reference is clearer.
________________________________________
7. Title page
The title page must include:
•	Article title.
•	Author names.
•	Author affiliations.
•	Corresponding author.
•	Corresponding author contact details.
•	Present/permanent address footnotes, if relevant.
Title rules:
•	Keep the title concise and informative.
•	Avoid unnecessary abbreviations.
•	Avoid formulae unless widely understood.
•	Avoid claims that are broader than the actual study.
•	Avoid titles suggesting a multi-part paper.
________________________________________
8. Abstract
Maximum length:
•	250 words
The abstract must:
•	Be concise and factual.
•	Stand alone without the full article.
•	State the purpose of the research.
•	State the main methods or approach.
•	State principal results.
•	State major conclusions.
•	Avoid references unless essential.
•	Define any non-standard abbreviation at first mention.
•	Avoid hype and overclaiming.
Recommended abstract structure:
Background / problem
Objective
Methods
Main results
Conclusion / implication
Do not include:
•	Undefined acronyms.
•	Literature review detail.
•	Excessive numeric detail.
•	Claims not supported in the manuscript.
•	Future work unless central to the conclusion.
________________________________________
9. Keywords
Use:
•	1–7 keywords
•	English keywords
•	Searchable scientific terms
Avoid:
•	Overly long keyword phrases.
•	Keywords with unnecessary “and” or “of”.
•	Rare abbreviations.
•	Duplicating only words from the title.
Use abbreviations only if they are firmly established in the field.
________________________________________
10. Highlights
Highlights are required at submission.
Rules:
•	Submit as a separate editable file.
•	Filename must include the word highlights.
•	Use 3–5 bullet points.
•	Each bullet must be no more than 85 characters including spaces.
•	Highlights should summarize novel results and/or new methods.
•	Keep them specific and concise.
Do not write verbose highlights.
Good highlight style:
A new method is validated against full-scale building measurements
Sensor uncertainty is quantified across three operating conditions
Model performance improves after local calibration
Bad highlight style:
This paper presents a very important and detailed study with many interesting results
________________________________________
11. Graphical abstract
A graphical abstract is encouraged but optional.
Rules:
•	Submit as a separate file.
•	Minimum size: 531 × 1328 pixels or proportionally larger.
•	Must be readable at approximately 5 × 13 cm.
•	Preferred formats: TIFF, EPS, PDF, or MS Office files.
•	Keep the design concise, pictorial, and professional.
•	Obtain permission for third-party material.
•	Do not use generative AI to create or alter submitted artwork unless its use is part of the research method and is reported reproducibly.
Recommended style:
•	One clear visual workflow.
•	Minimal text.
•	No dense legends.
•	No decorative icons unless they clarify meaning.
•	No screenshot-like clutter.
________________________________________
12. Tables
Tables must be editable text, not images.
Use LaTeX tables with booktabs.
Required table rules:
•	Cite every table in the manuscript text.
•	Number tables consecutively by order of appearance.
•	Provide a clear caption for every table.
•	Place table notes below the table body.
•	Avoid vertical rules.
•	Avoid shaded table cells.
•	Avoid duplicating data already shown in figures or text.
•	Use tables sparingly.
Recommended LaTeX table style:
\begin{table}[t]
\centering
\caption{Descriptive caption explaining the table content.}
\label{tab:example}
\begin{tabular}{lccc}
\toprule
Variable & Mean & SD & Unit \\
\midrule
Temperature & 22.4 & 1.8 & \si{\degreeCelsius} \\
Relative humidity & 45.2 & 8.7 & \si{\percent} \\
\bottomrule
\end{tabular}
\end{table}
Numeric formatting:
•	Use consistent decimal precision.
•	Align comparable numeric values.
•	Include units in column headers, not repeated in every cell.
•	Use siunitx for units and numeric alignment where useful.
•	Do not report more decimals than justified by the data.
Recommended precision:
•	Measured environmental quantities: usually 1–2 decimals.
•	Model metrics: usually 3 decimals.
•	Percentages: usually 1 decimal.
•	Counts: integers.
________________________________________
13. Figures, graphs, and artwork
All figures must be publication-ready.
Required figure rules:
•	Cite every figure in the manuscript text.
•	Number figures consecutively by order of appearance.
•	Submit figures as separate files using logical names:
o	Figure_1.pdf
o	Figure_2.pdf
o	Figure_3.tiff
•	Every figure must have a caption.
•	The caption should include:
o	a brief title,
o	a description of what is shown,
o	explanations of symbols or abbreviations if needed.
•	Keep text inside figures to a minimum.
•	Do not put a long title inside the figure if the caption already explains it.
•	Make all labels readable at final size.
Preferred file formats:
•	Vector plots and diagrams: PDF or EPS.
•	Photographs: TIFF, JPG, or PNG.
•	Mixed raster/vector artwork: high-resolution TIFF, PNG, or PDF.
Resolution requirements:
•	Photographs / halftones: minimum 300 dpi.
•	Bitmapped line drawings: minimum 1000 dpi.
•	Combined line + halftone images: minimum 500 dpi.
Pixel guidance:
•	300 dpi single-column image: at least 1063 px wide.
•	300 dpi full-page image: at least 2244 px wide.
•	1000 dpi single-column line drawing: at least 3543 px wide.
•	1000 dpi full-page line drawing: at least 7480 px wide.
•	500 dpi single-column combination image: at least 1772 px wide.
•	500 dpi full-page combination image: at least 3740 px wide.
Do not submit:
•	Low-resolution images.
•	Screenshots of plots.
•	Screenshots of tables.
•	Images with text too small to read.
•	Disproportionately large images with tiny fonts.
•	Overcrowded multi-panel figures.
•	Decorative 3D charts.
•	Figures with unexplained colors, symbols, or abbreviations.
________________________________________
14. Color figures
Color figures are acceptable.
Rules:
•	Color figures will appear in color online if usable.
•	Colors must be accessible to readers with impaired color vision.
•	Do not rely on color alone to communicate meaning.
•	Use line style, marker shape, labels, or direct annotation in addition to color.
•	Avoid red–green-only contrasts.
•	Prefer colorblind-safe palettes.
•	Ensure grayscale readability where possible.
For Python plots:
•	Use restrained colors.
•	Use consistent colors for the same category across figures.
•	Do not use rainbow colormaps.
•	Prefer perceptually uniform colormaps for continuous data.
•	Include colorbar labels with units where relevant.
Recommended Python colormaps:
# Continuous data
"viridis"
"cividis"

# Diverging data
"coolwarm"  # only when a meaningful midpoint exists
Avoid:
"jet"
"rainbow"
________________________________________
15. Python figure-generation rules
When generating manuscript figures in Python:
Prefer:
•	matplotlib
•	numpy
•	pandas
•	scipy
•	sklearn where relevant
Avoid:
•	decorative plotting styles,
•	default screenshots,
•	low-resolution exports,
•	unnecessary 3D plots,
•	inconsistent fonts,
•	excessive annotations,
•	unreadable legends.
Use clear figure sizes:
# Single-column style
fig, ax = plt.subplots(figsize=(3.5, 2.6))

# Wider figure
fig, ax = plt.subplots(figsize=(7.0, 3.5))
Save vector plots as PDF:
fig.savefig("Figure_1.pdf", bbox_inches="tight")
Also save raster preview if needed:
fig.savefig("Figure_1.png", dpi=300, bbox_inches="tight")
For line drawings or dense diagrams, prefer vector PDF/EPS.
For heatmaps or raster-heavy plots, save high-resolution PNG/TIFF.
All final figure-generation scripts should be reproducible and should not depend on manual editing after export.
________________________________________
16. Figure captions
Every figure needs a caption.
Caption structure:
Figure X. Brief title. One or two sentences explaining what is shown,
including sample size, normalization, uncertainty intervals, abbreviations,
or statistical meaning where relevant.
Good caption:
Figure 2. Model performance across validation folds. Bars show mean values
and error bars show one standard deviation across folds.
Bad caption:
Figure 2. Results.
Do not rely on the caption alone to explain the main result. The result should also be discussed in the main text.
________________________________________
17. Equations and mathematical notation
Equations must be editable LaTeX, not images.
Rules:
•	Use inline equations for simple expressions.
•	Display important equations separately.
•	Number only equations that are referenced later.
•	Number equations consecutively in the order they are cited.
•	Use italic variables.
•	Use exp(...) for powers of e where appropriate.
•	Use / for simple inline fractions where it improves readability.
•	Define all variables close to the equation.
•	Use consistent notation throughout the manuscript.
Example:
\begin{equation}
y = \beta_0 + \beta_1 x + \epsilon,
\label{eq:linear_model}
\end{equation}
________________________________________
18. Units and symbols
Use SI units where possible.
Rules:
•	Use consistent units throughout.
•	Define non-standard symbols.
•	Use siunitx for unit formatting.
•	Put units in table headers and axis labels.
•	Do not mix unit styles.
Examples:
\SI{22.5}{\degreeCelsius}
\SI{850}{ppm}
\SI{45}{\percent}
\SI{300}{lx}
Axis labels:
Temperature (°C)
CO₂ concentration (ppm)
Illuminance (lx)
Sound level (dB)
________________________________________
19. References
Use numbered references.
Rules:
•	Cite references in the text using numbers in square brackets.
•	Number references in the order they appear.
•	Every in-text citation must appear in the reference list.
•	Every reference-list item must be cited in the text.
•	Be consistent in formatting.
•	Include DOI where available.
•	Abbreviate journal names according to standard journal abbreviation rules where required.
•	References in the abstract should be avoided; if essential, cite author(s) and year(s) in full.
In-text examples:
Previous studies have reported similar effects [3,6].
Barnaby and Jones [8] obtained a different result.
Dataset references:
•	Cite relevant datasets in the text.
•	Include dataset references in the reference list.
•	Include author names, dataset title, repository, version if available, year, and persistent identifier.
•	Add [dataset] before dataset references where appropriate.
Software references:
•	Cite software if it is central to the work.
•	Include version and persistent identifier where possible.
________________________________________
20. Supplementary material
Supplementary material should be used for relevant supporting information that is too detailed for the main article.
Rules:
•	Cite every supplementary file in the manuscript.
•	Submit supplementary material at the same time as the manuscript.
•	Provide a concise descriptive caption for each supplementary item.
•	Ensure files are accurate and relevant.
•	Do not include unpolished working notes.
•	Do not include exploratory material that is not referenced.
•	Remember that supplementary material may appear online exactly as submitted.
Recommended naming:
Supplementary_Table_S1.xlsx
Supplementary_Figure_S1.pdf
Supplementary_Methods_S1.pdf
________________________________________
21. Data availability and research data
A data availability statement is required.
If data are shared:
Data availability

The data supporting this study are available in [repository name] at [DOI/link].
If data cannot be shared:
Data availability

The data supporting this study cannot be made publicly available because
[reason].
For computational studies, consider sharing:
•	raw or processed data where allowed,
•	code,
•	model configuration,
•	random seeds,
•	environment files,
•	scripts used to generate figures and tables.
Research data may include:
•	observations,
•	experimental results,
•	software,
•	code,
•	models,
•	algorithms,
•	protocols,
•	methods.
________________________________________
22. Required declarations
Prepare the following end-of-manuscript sections where applicable:
Declaration of generative AI and AI-assisted technologies in the manuscript preparation process
CRediT author statement
Declaration of competing interest
Funding
Data availability
Acknowledgements
References
Competing interest example:
The authors declare that they have no known competing financial interests
or personal relationships that could have appeared to influence the work
reported in this paper.
No funding example:
This research did not receive any specific grant from funding agencies in
the public, commercial, or not-for-profit sectors.
Generative AI disclosure:
•	Include only if generative AI or AI-assisted tools were used in manuscript preparation.
•	Basic spelling, grammar, and reference-checking tools do not require disclosure.
•	Do not list AI tools as authors.
•	Authors remain fully responsible for accuracy, originality, interpretation, and final content.
________________________________________
23. CRediT author statement
Use CRediT roles where applicable.
Common roles:
Conceptualization
Data curation
Formal analysis
Funding acquisition
Investigation
Methodology
Project administration
Resources
Software
Supervision
Validation
Visualization
Writing – original draft
Writing – review and editing
Only include roles that actually apply.
Example:
Author A: Conceptualization, Methodology, Formal analysis, Writing – original draft.
Author B: Supervision, Writing – review and editing.
________________________________________
24. Acknowledgements
Acknowledgements must be placed in a separate section before the reference list.
Use acknowledgements for:
•	language editing help,
•	technical assistance,
•	proofreading help,
•	administrative support,
•	non-author contributions.
Do not put acknowledgements:
•	on the title page,
•	as a footnote to the title,
•	in an unrelated manuscript section.
________________________________________
25. Appendix formatting
If appendices are used:
•	Label appendices as Appendix A, Appendix B, etc.
•	Number appendix equations separately:
o	Eq. (A.1), Eq. (A.2)
o	Eq. (B.1), Eq. (B.2)
•	Number appendix tables and figures separately:
o	Table A.1
o	Fig. A.1
o	Table B.1
o	Fig. B.1
________________________________________
26. Submission checklist
Before submission, verify:
[ ] Manuscript is within the journal scope.
[ ] Article type is correct.
[ ] Editable LaTeX source files are prepared.
[ ] PDF is not the only source file.
[ ] Abstract is ≤ 250 words.
[ ] Keywords are provided, 1–7 total.
[ ] Highlights file exists.
[ ] Highlights contain 3–5 bullets.
[ ] Each highlight is ≤ 85 characters including spaces.
[ ] Sections and subsections are numbered.
[ ] Tables are editable text, not images.
[ ] All tables are cited in the text.
[ ] All figures are cited in the text.
[ ] All figures have captions.
[ ] Figures are supplied as separate files.
[ ] Figure resolution is sufficient.
[ ] Color figures are colorblind-accessible.
[ ] Equations are editable LaTeX.
[ ] References are numbered in order of appearance.
[ ] All in-text citations appear in the reference list.
[ ] All reference-list items are cited in the text.
[ ] DOI values are included where available.
[ ] Dataset references are included where relevant.
[ ] Data availability statement is included.
[ ] Funding statement is included.
[ ] Competing interest declaration is included.
[ ] CRediT author statement is included.
[ ] Generative AI disclosure is included if applicable.
[ ] Acknowledgements are placed before references.
[ ] Supplementary material is cited and submitted if used.
[ ] Spelling and grammar have been checked.
[ ] Permissions for copyrighted material have been obtained.
________________________________________
27. Common rejection-risk checks
Avoid the following:
[ ] Manuscript is outside journal scope.
[ ] Corresponding author uses a generic email address.
[ ] More than one corresponding author is listed.
[ ] Original research article exceeds 10,000 words.
[ ] Figures + Tables exceed 20.
[ ] Highlights are missing or verbose.
[ ] English quality is poor.
[ ] The manuscript is submitted to another journal simultaneously.
[ ] The title suggests a multi-part paper.
[ ] Conclusions are not supported by the data.
[ ] Tables, graphs, or illustrations are unclear.
________________________________________
28. Codex instructions
When editing LaTeX, figures, or tables for a Building and Environment manuscript:
1.	Preserve the Elsevier/LaTeX manuscript style.
2.	Do not manually compress the manuscript with tiny fonts or narrow margins.
3.	Keep all figures readable at journal scale.
4.	Prefer vector PDF for generated plots.
5.	Use high-resolution raster formats where needed.
6.	Use colorblind-accessible colors.
7.	Do not rely on color alone.
8.	Use booktabs for LaTeX tables.
9.	Do not create tables as images.
10.	Do not use vertical table lines or shaded cells.
11.	Keep captions informative and concise.
12.	Cite every table and figure in the text.
13.	Keep references numbered and ordered by appearance.
14.	Use consistent numeric precision.
15.	Do not invent results or unsupported claims.
16.	Do not change scientific meaning while editing style.
17.	Keep manuscript language concise, factual, and technical.
18.	Avoid hype and overclaiming.
19.	Ensure all required declarations are present.
20.	Check the official journal guide before final submission.
