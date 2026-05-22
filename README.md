The tool reads a structured mathematical proof document and produces a dual-layer output: every section restored alongside a metaphorical reading. The architecture is:

    Math Extractor — pulls all $...$ and $$...$$ expressions, replaces them with safe placeholders
    Section Parser — identifies structural blocks (definitions, theorems, proofs, gaps, tables) via regex patterns
    Metaphor Engine — a hand-crafted bank of ~40 concept-to-metaphor mappings, each with a frame template that re-introduces math at the right positions; complemented by section-level metaphor transformations for major theorems/gaps
    Reassembler — generates the final dual-column markdown output

Design Decisions
Decision	Rationale
Zero external dependencies	Runs anywhere with Python 3.7+. No nltk, no spacy, no ML model — the metaphors are hand-crafted, not generated.
Placeholder-based math extraction	Math ($...$, $$...$$) is extracted first, replaced with {{MATH_N}} placeholders, so metaphor generation never corrupts LaTeX. Restored at the end.
Two-tier metaphor system	Metaphor bank handles inline concept replacement; section metaphors provide pre-written holistic readings for major theorems and gaps. This ensures quality — fully automatic metaphor generation from technical prose is not reliable enough.
Dual-layer output format	Every section shows original first (📐), then metaphor (🌊). Nothing is deleted. The reader can move between rigor and intuition.
Extensible metaphor bank	New MetaphorEntry objects can be added to build_metaphor_bank() without touching any other code. New section-level metaphors can be added to get_section_metaphor().
Gaps are translated too	Every [GAP N] gets a metaphor reading that honestly frames what's unknown — "The Unfinished Story" framing acknowledges the gap while providing geometric intuition for what a proof would need.
Known Limitations & Extensibility Points

    The metaphor bank currently covers ~15 core concepts. For sections that don't match any trigger, the tool falls through to the original text (no bad metaphors are worse than no metaphors). Expanding the bank is the highest-leverage improvement.

    Section-level metaphors are hand-written for theorems T1, T3, T4, T7, T9, T11, T12, T14, T17 and gaps G1, G2, G10, G11, G12, G15. Adding the remaining theorems (T2, T5, T6, T8, T10, T13, T16) and gaps (G3–G9, G13–G16) would complete the coverage.

    The concept-level metaphor matching uses simple substring matching. For production use, one could replace this with TF-IDF or embedding-based similarity to handle synonymy and phrasing variation.

    The tool could be extended to accept a user's own proof markdown and a custom metaphor bank file, making it a general-purpose mathematical metaphor engine rather than one specific to this framework.
