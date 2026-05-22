The tool reads a structured mathematical proof document and produces a dual-layer output: every section restored alongside a metaphorical reading. The architecture is:

    Math Extractor — pulls all $...$ and $$...$$ expressions, replaces them with safe placeholders
    Section Parser — identifies structural blocks (definitions, theorems, proofs, gaps, tables) via regex patterns
    Metaphor Engine — a hand-crafted bank of ~40 concept-to-metaphor mappings, each with a frame template that re-introduces math at the right positions; complemented by section-level metaphor transformations for major theorems/gaps
    Reassembler — generates the final dual-column markdown output
