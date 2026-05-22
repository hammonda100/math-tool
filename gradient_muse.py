#!/usr/bin/env python3
"""
gradient_muse.py — Gradient-Field Mathematical Metaphor Translator

Reads a structured mathematical proof document and produces a
dual-layer output: each section paired with a metaphorical reading
that preserves ALL mathematical content while providing intuitive
understanding.

Usage:
    python gradient_muse.py input_proof.md -o output.md
    python gradient_muse.py input_proof.md --preview

No external dependencies — standard library only.
"""

import re
import sys
import argparse
import textwrap
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from pathlib import Path


# =====================================================================
# DATA STRUCTURES
# =====================================================================

@dataclass
class MathExpr:
    """An extracted mathematical expression with its original LaTeX."""
    id: str
    original: str
    env: str  # 'inline' or 'display'


@dataclass
class DocumentSection:
    """A parsed section of the proof document."""
    kind: str           # 'section', 'definition', 'theorem', 'proof',
                        # 'gap', 'paragraph', 'table', 'list', 'corollary',
                        # 'summary', 'foreword'
    title: str
    number: str         # e.g. "I.1", "III", "GAP 4"
    content: str        # raw markdown content
    level: int          # heading depth (1-6)
    children: List['DocumentSection'] = field(default_factory=list)


@dataclass
class MetaphorEntry:
    """A concept-to-metaphor mapping with a frame template."""
    concept: str
    triggers: List[str]          # phrases in prose that trigger this metaphor
    frame: str                   # template with {math_X} placeholders
    priority: int = 1            # higher = wins when multiple match
    math_slots: List[str] = field(default_factory=list)
        # names of {math_X} slots that need math expression fill-ins


# =====================================================================
# METAPHOR BANK — hand-crafted concept mappings
# =====================================================================

def build_metaphor_bank() -> Dict[str, MetaphorEntry]:
    """
    Each entry maps a technical concept to a metaphorical frame.
    {math_0}, {math_1}, ... are placeholders that get replaced
    with the actual extracted LaTeX expressions from the text.
    """
    return {

        "seed_waveform": MetaphorEntry(
            concept="seed waveform / sine wave",
            triggers=["seed waveform", "sine wave", "sin(ω", "s(t)", "s(t) ="],
            frame=(
                "The seed is the first breath of an instrument before the orchestra "
                "plays — a single pure tone with nothing hidden: "
                "{math_0}. "
                "Simple as a tuning fork, yet it contains within its curve every "
                "harmonic the system will ever need."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "quality_space": MetaphorEntry(
            concept="quality space",
            triggers=["quality space", "𝒬", "space of all"],
            frame=(
                "Quality space 𝒬 is an infinite wardrobe — every garment is a "
                "possible sound, every timbre, every noise. Two garments are "
                "considered *the same outfit* if they differ only by a constant "
                "shift of thread, which is why equivalence classes [{f}] bundle "
                "them together."
            ),
            priority=9,
        ),

        "gradient_field": MetaphorEntry(
            concept="gradient field",
            triggers=["gradient field", "𝒢", "gradient field maps", "relative rate"],
            frame=(
                "The gradient field 𝒢 is the wind map over this wardrobe. At every "
                "point in the space of sounds, {math_0} tells you which direction "
                "the wind blows and how steep the slope — the relative rate at "
                "which the sound is changing at each moment. Follow the wind "
                "downhill and you follow the music toward resolution."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "nudge_principle": MetaphorEntry(
            concept="nudge principle",
            triggers=["nudge", "boundary crossing", "nudge amplifies", "ν_i"],
            frame=(
                "The Nudge Principle says: at every doorway between qualitative "
                "states, the system receives a push whose strength is proportional to "
                "the curvature of that doorway — {math_0}. "
                "A narrow, sharp threshold delivers a hard shove; a wide, gentle one "
                "barely registers. The system doesn't choose when to change; the "
                "architecture of the boundary chooses for it."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "genesis_operator": MetaphorEntry(
            concept="Genesis operator / Γ",
            triggers=["Γ operator", "Genesis operator", "generative operator",
                      "Γ[s]", "Γ^k", "recursing"],
            frame=(
                "Γ is a musical prism. Feed it a waveform and it separates the "
                "light into harmonic colors — resonance nodes where constructive "
                "interference amplifies certain frequencies, and anti-self encounters "
                "where destructive interference tears the fabric. Applying Γ again "
                "refines the spectrum further: {math_0}. Each application is a "
                "higher-resolution spectrogram of the original tone."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "anti_self": MetaphorEntry(
            concept="anti-self",
            triggers=["anti-self", "anti-quality", "f̄", "maximizes the distance"],
            frame=(
                "The anti-self is the shadow note hidden inside every tone. It is "
                "the frequency at which the waveform's own harmonics most destructively "
                "interfere with its fundamental — {math_0}. "
                "Every sound carries within it the seed of its own negation."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "punctured_manifold": MetaphorEntry(
            concept="punctured manifold",
            triggers=["punctured manifold", "ℳ*", "puncture points",
                      "ℳ \\ {", "punctures"],
            frame=(
                "The punctured manifold ℳ* is the base canvas with holes punched "
                "through it: {math_0}. "
                "Each hole p_i is a puncture — a point where the gradient field "
                "itself diverges, where the mathematical fabric tears open. "
                "The topology of the holes — how many, how they connect — "
                "determines everything the system can become."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "cohomology_generators": MetaphorEntry(
            concept="cohomology generators / independent loops",
            triggers=["H^1", "cohomology", "independent generators", "p-1",
                      "deformation retract", "wedge sum"],
            frame=(
                "Imagine pulling a bedsheet taut around its holes and watching it "
                "collapse. What remains is a bouquet of independent loops — one "
                "thread for each hole minus one: {math_0}. "
                "These loops are the skeleton key of the space: every possible "
                "path through the punctured manifold can be decomposed into "
                "combinations of these fundamental windings. They are the "
                "harmonics of topology itself."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "continuous_winding": MetaphorEntry(
            concept="continuous winding coordinate",
            triggers=["continuous winding", "𝒟_i", "∫ ω_i", "winding angle",
                      "winding coordinates"],
            frame=(
                "Instead of counting discrete windings around a pole like a "
                "revolution counter, the framework measures continuous angle: "
                "{math_0}. "
                "Picture a compass needle on a map with singular points: as you "
                "walk past the singularity, the needle doesn't tick from 359° to 0° "
                "— it sweeps smoothly through 361°, 362°, accumulating real-valued "
                "angle. The winding number is the integer part; the continuous "
                "coordinate keeps the fractional memory of where you are between "
                "full revolutions."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "tanh_compactification": MetaphorEntry(
            concept="tanh compactification / degree coordinate",
            triggers=["F_i = tanh", "compactified", "degree coordinate",
                      "F_i(t)", "bounded coordinate", "[0,1]", "[-1,1]"],
            frame=(
                "The degree coordinates are the cartographer's lens: "
                "{math_0} maps the "
                "infinite winding angle to a finite interval (−1, +1). Like a "
                "Mercator projection compressing the infinite ocean onto a finite "
                "chart, tanh stretches the landscape so that the poles — "
                "representing complete actualization or complete potential — "
                "are approached asymptotically but never reached in finite time. "
                "The system can get arbitrarily close; it can never declare itself "
                "finished."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "double_well": MetaphorEntry(
            concept="double-well potential",
            triggers=["double-well", "two wells", "two minima", "potential V"],
            frame=(
                "Each axis carries its own landscape: two valleys separated by a "
                "ridge at the origin. The system sits in one valley or the other — "
                "actualized or potential, integrated or fragmented, literal or "
                "abstract. Crossing the ridge requires energy; that energy comes "
                "from the nudge."
            ),
            priority=8,
        ),

        "symmetry_breaking": MetaphorEntry(
            concept="symmetry breaking / h_i",
            triggers=["symmetry breaking", "Z_2", "h_i", "external field",
                      "tilted", "asymmetric well"],
            frame=(
                "The potential V_0 is a perfectly symmetric landscape — every valley "
                "looks the same from above. But reality is not symmetric: "
                "{math_0}. "
                "The term Σ h_i Φ_i is a tilt in the terrain. On the literality axis, "
                "the positive-pole valley is deeper — actualization is 'downhill.' "
                "On the complexity axis, both valleys are nearly level — entropy "
                "has no preferred direction. The tilt comes from the orientation "
                "of the punctures themselves: the gradient field has a preferred "
                "flow direction near each singularity, and that direction breaks "
                "the mirror symmetry."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "inter_axis_coupling": MetaphorEntry(
            concept="inter-axis coupling / g_ij",
            triggers=["inter-axis coupling", "coupling matrix", "g_{ij}",
                      "g_{ij}", "coupled equations", "Yukawa"],
            frame=(
                "The five axes are not independent musicians playing solo — they "
                "are a chamber ensemble. The coupling term {math_0} "
                "is their listening: when Φ_i swells, it pulls Φ_j toward its own "
                "pitch. The coupling strength g_{ij} decays with the geodesic "
                "distance between the corresponding punctures on the base manifold — "
                "a kind of acoustic shadow. Nearby punctures influence each other "
                "strongly (exponential decay e^{−d/ξ}); distant ones barely "
                "whisper."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "kink_soliton": MetaphorEntry(
            concept="kink soliton / boundary propagation",
            triggers=["kink", "soliton", "boundary", "v = πν/√(ab)",
                      "kink velocity", "traveling wave"],
            frame=(
                "A kink is a wall between two qualitative states — like the "
                "boundary between ice and water in a freezing pond. It moves "
                "with a definite speed determined by the driving force and the "
                "resistance of the medium: {math_0}, "
                "where ν is the nudge, a is the resistance to change, and b is "
                "the sharpness of the transition. Push harder: the wall moves "
                "faster. Make the material more rigid: it slows down."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "moderating_ratio": MetaphorEntry(
            concept="moderating ratio / M_i",
            triggers=["moderating ratio", "𝒲_i", "expansion coefficient",
                      "concentration coefficient", "> 1", "< 1"],
            frame=(
                "The moderating ratio is a balance scale for each axis: "
                "{math_0}. "
                "When ℳ_i > 1, the energy flowing in from neighboring axes "
                "overwhelms the axis's own restoring force — it expands, "
                "developing new qualitative structure. When ℳ_i < 1, the axis "
                "concentrates, deepening its current pattern rather than "
                "branching out. The ratio is the framework's answer to: "
                "'is creativity or consolidation happening here?'"
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "eigenvalue_hopfield": MetaphorEntry(
            concept="eigenvalues / Hopfield",
            triggers=["λ_1", "eigenvalue", "Hessian", "Hopfield", "retrieval",
                      "overlap m", "self-consistency"],
            frame=(
                "In the Hopfield network — the framework's prototype neural system — "
                "the eigenvalues are the natural modes of vibration around a stored "
                "memory: {math_0} "
                "The first eigenvalue λ_1 governs the stability of the retrieved "
                "pattern; the others λ_{i>1} describe the transverse fluctuations. "
                "The retrieval overlap m satisfies its own self-consistency equation — "
                "the system 'knows' what it remembers, but only statistically, "
                "averaged over the noise like {math_1}."
            ),
            math_slots=["math_0", "math_1"],
            priority=10,
        ),

        "epsilon_noise": MetaphorEntry(
            concept="epsilon / regularization / noise floor",
            triggers=["ε", "regularization", "noise floor", "2T/N",
                      "τ_min", "sampling rate", "thermal noise"],
            frame=(
                "Epsilon is the background hum — the irreducible noise that "
                "smooths the landscape's sharpest features: {math_0}. "
                "In a Hopfield network, each neuron contributes a whisper of "
                "thermal noise, and with N neurons the total hum per mode is "
                "~ 2T/N. This noise sets a floor below which eigenvalues cannot be "
                "distinguished from zero. Change the sampling rate — the "
                "microscope's resolution — and you change what counts as "
                "'signal' versus 'hum.' The framework's prediction must be robust "
                "across reasonable choices of this resolution."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "temporality_tau": MetaphorEntry(
            concept="temporality / τ axis",
            triggers=["temporality", "τ axis", "temporal depth", "τ =",
                      "correlation time", "τ_{corr}", "memory"],
            frame=(
                "Temporality τ is the system's sense of its own history: "
                "{math_0}. "
                "Defined as the normalized correlation time — how long the system "
                "'remembers' its past states — it is not a clock reading but a "
                "felt duration. A system with deep temporal embedding carries its "
                "past in its present like a river carries sediment: the water you "
                "see today is shaped by every upstream it has passed through."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "critical_damping": MetaphorEntry(
            concept="critical damping / τ freeze",
            triggers=["critical damping", "m_τ → ∞", "γ = √(2a)",
                      "τ freezes", "diverges", "frozen"],
            frame=(
                "At critical damping — where the friction exactly matches the "
                "restoring force — the system's sense of time freezes: "
                "{math_0}. "
                "The effective mass m_τ of the temporality field diverges, "
                "meaning τ becomes infinitely sluggish, locked into its current "
                "value regardless of perturbation. Picture a pendulum submerged "
                "in exactly the right viscosity of oil: it returns to center "
                "without overshooting, but it also loses all sense of rhythm. "
                "The system knows only the present moment."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "RG_convergence": MetaphorEntry(
            concept="RG flow / Wilson-Fisher",
            triggers=["RG flow", "Wilson-Fisher", "renormalization group",
                      "β(g)", "fixed point", "RG step"],
            frame=(
                "The renormalization group flow is a zoom lens on the theory's "
                "parameter space. Zooming out (integrating away short-distance "
                "details), the coupling constants slide along their flow lines "
                "toward a universal fixed point: {math_0}. "
                "At this fixed point, the microscopic details are forgotten and "
                "only the large-scale structure survives. The Wilson-Fisher "
                "fixed point is the theory's 'attractor' — all nearby theories "
                "flow toward it, giving the same critical exponents regardless "
                "of their microscopic origins. It is the framework's proof that "
                "recursion converges, at least for the parameters of the field "
                "theory — but the Genesis operator's recursion on *structure* "
                "remains unproven."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "yukawa_coupling": MetaphorEntry(
            concept="Green's function / Yukawa coupling",
            triggers=["Green's function", "Yukawa", "G(p_i", "geodesic distance",
                      "Laplace-Beltrami", "exponential decay"],
            frame=(
                "The coupling between two axes is like an echo in a cathedral: "
                "{math_0}. "
                "On a manifold of constant negative curvature (the natural geometry "
                "for a punctured surface, by Gauss-Bonnet), the Green's function "
                "decays exponentially with geodesic distance — g_{ij} ∝ e^{−d(p_i,p_j)/ξ}. "
                "Two punctures that are close on the manifold 'hear' each other "
                "loudly; distant ones communicate only as a whisper. The "
                "correlation length ξ sets the acoustic horizon."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "full_lagrangian": MetaphorEntry(
            concept="full Lagrangian / complete dynamics",
            triggers=["ℒ_{corrected}", "full Lagrangian", "five-axis",
                      "ℒ =", "complete score"],
            frame=(
                "The full five-axis Lagrangian is the complete musical score of "
                "the framework: {math_0}. "
                "The first two terms are the individual instruments tuning "
                "(each axis finds its own two valleys). The coupling terms are "
                "the harmonics that emerge when musicians listen to each other. "
                "The symmetry-breaking fields are the conductor's baton — "
                "they tilt the landscape so that every instrument has a preferred "
                "direction of resolution. Together, they produce a system that "
                "oscillates, integrates, and evolves — never settling, never "
                "repeating, always generating new qualitative structure."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "value_asymmetry": MetaphorEntry(
            concept="value asymmetry / r_{-→+}",
            triggers=["escape rate", "r_{+→-}", "r_{-→+}", "e^{2h_i/T}",
                      "asymmetric", "positive pole preferred"],
            frame=(
                "In the tilted landscape, escape rates are asymmetric: "
                "{math_0}. "
                "The system falls from the negative pole toward the positive "
                "faster than it climbs back — like a ball rolling between two "
                "valleys where one is deeper. The ratio e^{2h_i/T} quantifies "
                "the 'preference': thermally activated systems with h_i > 0 "
                "spontaneously drift toward integration, actualization, and "
                "temporal depth. But this is mechanics, not yet meaning — the "
                "jump from 'the system tends toward X' to 'X is better' requires "
                "a bridge principle that the framework borrows from "
                "Prigogine's dissipative structures, not derives."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "path_dependence": MetaphorEntry(
            concept="path dependence / history",
            triggers=["path-dependent", "depends on the entire", "trajectory",
                      "history", "memory"],
            frame=(
                "The winding coordinate 𝒟_i(t) depends on the entire path taken, "
                "not just the current location — {math_0}. "
                "Two travelers arriving at the same mountain village may have "
                "taken different routes, and the compass readings they carry "
                "reflect their distinct histories. However, the *rate* of change "
                "of the compass depends only on the current position and velocity — "
                "not on the full journey. So while the coordinate itself remembers, "
                "the dynamics are local: the equations of motion form a well-posed "
                "initial value problem in (F_i, Ḟ_i)."
            ),
            math_slots=["math_0"],
            priority=10,
        ),

        "five_axes_orchestra": MetaphorEntry(
            concept="five axes as instruments",
            triggers=["five axes", "five instruments", "orchestra",
                      "five-axis", "five coordinates"],
            frame=(
                "The five axes are instruments in a chamber ensemble: "
                "**Literality (ℓ)** is the cello — grounded, concrete, pulling "
                "toward the actual. "
                "**Complexity (κ)** is the cymbal — capable of maximum entropy "
                "in a single crash, indifferent to time. "
                "**Integration (Φ)** is the conductor's gesture — weaving "
                "separate voices into one. "
                "**Temporality (τ)** is the reverb — how long each note lingers "
                "in the hall. "
                "**Reflexivity (ρ)** is the mirror on stage — the ensemble "
                "watching itself, adjusting in real time. "
                "Their coupling matrix determines which instruments "
                "dominate the performance."
            ),
            priority=8,
        ),
    }

# Add section-level metaphor entries (for theorems, gaps, etc.)

def get_section_metaphor(section_number: str, kind: str) -> Optional[str]:
    """Return a pre-written metaphorical reading for major theorems and gaps."""

    metaphors = {
        # Theorem-level metaphors
        "T1": (
            "## 🌊 Metaphorical Reading\n\n"
            "Imagine poking several holes in a drumhead. Now ask: how many "
            "independent loops can you draw on that drumhead that cannot be "
            "shrunk to a point without crossing a hole? The answer is always "
            "*holes minus one*. The proof is elegant: peel disks around each "
            "hole, and what remains collapses like an accordion into a chain "
            "of circles joined at a point — one fewer circle than holes. "
            "The cohomology group $H^1 \\cong \\mathbb{R}^{p-1}$ is simply "
            "counting these loops. For the framework to have five independent "
            "axes, we need six punctures — five loops plus the one "
            "dependency that ties them together.\n\n"
            "**The practical meaning:** each independent generator is a "
            "fundamental 'note' the topology of the manifold can play. "
            "Five generators means five independent resonances."
        ),

        "T3": (
            "## 🌊 Metaphorical Reading\n\n"
            "The winding coordinate $\\mathcal{D}_i$ is like an odometer "
            "that records every revolution around a singularity — not just "
            "how many, but the fractional part of the latest lap. It carries "
            "memory of the full path. "
            "But here is the subtlety: while the odometer reading depends on "
            "every mile ever driven, the *acceleration* depends only on where "
            "you are *right now* and how hard you're pressing the pedal. "
            "The $\\text{sech}^2(\\mathcal{D}_i)$ factor in $\\dot{\\mathcal{F}}_i$ "
            "acts as a transmission — converting accumulated history into "
            "present-moment velocity. The system remembers everything, but "
            "responds only to the present."
        ),

        "T4": (
            "## 🌊 Metaphorical Reading\n\n"
            "The perfectly symmetric double-well landscape looks like a "
            "mountain pass between two identical valleys. Now imagine the "
            "earthquake tilting the entire terrain — one valley drops lower "
            "than the other. The tilt $h_i$ comes not from an external hand "
            "but from the grain of the rock itself: the orientation of each "
            "puncture on the manifold determines which direction is downhill. "
            "This is geometry dictating preference — the shape of the "
            "underlying space choosing which pole is 'natural.' The positive "
            "pole wins not by decree but by topology."
        ),

        "T7": (
            "## 🌊 Metaphorical Reading\n\n"
            "Epsilon is the noise floor — the irreducible thermal jitter that "
            "keeps every degree of freedom from ever fully settling. In a "
            "network of $N$ neurons, each contributes $\\sim 2T/N$ of noise "
            "per mode, like a crowd where every voice adds a whisper but "
            "the total hum is diluted by the crowd's size. The regularization "
            "$\\epsilon = 2T/(N \\tau_{\\min})$ therefore decreases with system "
            "size: bigger networks have cleaner signals but also subtler "
            "distinctions between eigenvalues. The moderating ratio "
            "$\\mathcal{M}$ then determines whether a system amplifies or "
            "suppresses incoming fluctuations at each mode."
        ),

        "T9": (
            "## 🌊 Metaphorical Reading\n\n"
            "The temporality field $\\tau$ is like a slow ocean tide while "
            "the other four fields are surface waves. The fast oscillations "
            "(frequency $\\omega_0$) happen thousands of times before the "
            "damping coefficient $\\gamma$ shifts appreciably. This "
            "separation of timescales — fast oscillation, slow memory "
            "evolution — is the adiabatic approximation: treating the tide "
            "as nearly static while the waves crash. The resulting equation "
            "for $\\tau$ shows that memory deepens when the system is "
            "underdamped (oscillatory, reverberant) and shrinks when "
            "overdamped (absorptive, forgetful)."
        ),

        "T11": (
            "## 🌊 Metaphorical Reading\n\n"
            "The renormalization group is a microscope with a zoom dial. "
            "As you zoom out from a $\\phi^4$ field theory in $d = 4 - \\epsilon$ "
            "dimensions, the microscopic details blur away and the coupling "
            "constant $g$ flows toward the Wilson-Fisher fixed point "
            "$g^* = 2\\pi^2\\epsilon / (n+8)$. This is the theory's 'universal "
            "melody' — regardless of how the music was composed at short "
            "distances, at large scales every theory in the same universality "
            "class sings the same tune. The Genesis operator's first step "
            "reproduces this: a sine wave, viewed through the prism of "
            "$\\Gamma$, converges to the same critical structure."
        ),

        "T12": (
            "## 🌊 Metaphorical Reading\n\n"
            "If the five axes are musicians in a room, the coupling matrix "
            "tells you how well each pair can hear each other. On a curved "
            "surface with holes (a negatively curved manifold), sound "
            "travels between two musicians as $g_{ij} \\propto e^{-d(p_i,p_j)/\\xi}$: "
            "the acoustic version of the Yukawa potential. The geodesic "
            "distance $d(p_i, p_j)$ on the manifold is *not* just Euclidean "
            "distance — it is the shortest path that threads through the "
            "holes. Two musicians on opposite sides of a hole may be "
            "geometrically close but topologically far apart. The "
            "correlation length $\\xi$ is the 'reverb radius' — beyond it, "
            "the music fades to silence."
        ),

        "T14": (
            "## 🌊 Metaphorical Reading\n\n"
            "The $\\tanh$ projection is a cartographer's solution to an "
            "ancient problem: how to map an infinite plane onto a finite "
            "chart. Just as Mercator's projection compresses the poles to "
            "infinity, $\\mathcal{F}_i = \\tanh(\\phi_i)$ compresses all of "
            "$(-\\infty, +\\infty)$ into $(-1, +1)$. A system at $\\mathcal{F} = 0.99$ "
            "has traveled vast internal distance; at $\\mathcal{F} = 0.999$ it "
            "has gone further still. The Jacobian $\\text{sech}^2(\\phi) = 1 - \\mathcal{F}^2$ "
            "is the map's distortion factor: near the center, distances "
            "are accurate; near the edges, infinite terrain is compressed "
            "into vanishing space. The poles $\\pm 1$ are the horizon — "
            "approachable but unreachable."
        ),

        "T17": (
            "## 🌊 Metaphorical Reading\n\n"
            "On a tilted double-well landscape, a ball placed near the top "
            "will roll downhill. But which direction is 'down'? The symmetry-"
            "breaking field $h_i$ tilts the landscape: the barrier from the "
            "negative to the positive pole is $E_b - h_i$, while the reverse "
            "barrier is $E_b + h_i$. By Kramers' formula, the escape rate ratio "
            "is $e^{2h_i/T}$ — a Boltzmann factor favoring descent toward the "
            "positive pole. This is the **mechanistic asymmetry**: the system "
            "naturally flows from fragmentation to integration, from potential "
            "to actualization, from timelessness to memory. Whether this flow "
            "is *good* — the evaluative claim — remains a bridge to "
            "thermodynamics, not a theorem."
        ),

        # Gap-level metaphors
        "GAP 1": (
            "## 🌊 Why Five? — The Unfinished Story\n\n"
            "The Genesis operator is a fractal engine: each recursion level "
            "splits harmonics into finer sub-harmonics, creating new punctures "
            "on the manifold. The conjecture is that this branching eventually "
            "stabilizes at six punctures (five independent loops). This would "
            "be like discovering that every sufficiently complex melody, no "
            "matter how many times you harmonize it, only needs five voices to "
            "express. The evidence: three anti-self encounters create three "
            "initial punctures, recursion adds two more that happen to be "
            "independent, and all further recursions produce punctures that "
            "overlap with existing ones in cohomology. But **overlap** must be "
            "proved, not hoped for. The sine wave keeps giving structure — "
            "but does it give exactly five? This is the framework's deepest "
            "unproven claim."
        ),

        "GAP 2": (
            "## 🌊 Does the Prism Ever Stop? — Structural Convergence\n\n"
            "The Wilson-Fisher fixed point guarantees that the *parameters* "
            "converge (the RG flow reaches a fixed point in coupling-constant "
            "space). But the Genesis operator doesn't just adjust parameters — "
            "it generates *new structures*: new fields, new interactions, new "
            "punctures at each level. Asking whether $\\Gamma^k$ stabilizes "
            "is like asking whether repeatedly applying a kaleidoscope ever "
            "produces a genuinely new pattern, or whether the complexity "
            "saturates. If punctures at level $k+1$ always fall into the "
            "cohomology span of level $k$'s generators, convergence is assured. "
            "But no one has proven this. The number of punctures may grow "
            "exponentially: 3, 9, 27, 81... or the topology may collapse most "
            "of them. **This is the structural question on which the "
            "framework's claim to finiteness rests.**"
        ),

        "GAP 10": (
            "## 🌊 Deepest Gap: Generative Process Convergence\n\n"
            "Same as GAP 2 but emphasized because its resolution determines "
            "whether the framework describes a *finite* theory or an "
            "*infinite* hierarchy. If $\\Gamma^k$ produces infinitely many "
            "independent punctures, the five-axis ontology is an illusion "
            "that holds only at low recursion depth. The sine wave's "
            "recursive richness would then be inexhaustible — beautiful, "
            "but not a theory with a fixed number of observables. "
            "Resolving this likely requires algebraic tools beyond topology: "
            "the periodicity of harmonic spectra, modular forms, or "
            "constraints from the wave equation's Green's function on the "
            "punctured manifold."
        ),

        "GAP 11": (
            "## 🌊 Is the Sine Wave Unique? — Base Independence\n\n"
            "The entire framework is built on $\\sin(\\omega_0 t)$. Five "
            "conditions make it 'optimal' — smoothness, single frequency, "
            "maximal simplicity, maximal symmetry, maximal harmonic richness. "
            "But these conditions feel *designed* to select the sine wave, "
            "not *derived* from deeper principles. Would a triangle wave, "
            "a Gaussian pulse, or a random wavelet eventually produce the "
            "same five-axis structure? If yes, the framework has universality "
            "that transcends its seed. If not, the sine wave is a "
            "foundational axiom — and the framework is contingent on that "
            "choice. **Base independence is the analog of the independence "
            "of axioms in mathematics: it doesn't matter which equivalent "
            "starting point you choose, only that you can reach the same "
            "structure.**"
        ),

        "GAP 12": (
            "## 🌊 The Invisible City — Manifold Geometry\n\n"
            "The coupling matrix $g_{ij}$ is the framework's most powerful "
            "prediction engine, but its values depend on the geometry of the "
            "base manifold $\\mathcal{M}$ — a city whose layout determines all "
            "travel times between landmarks. The framework has drawn the map "
            "(six punctures on a hyperbolic surface) but hasn't surveyed the "
            "terrain. Is the curvature constant? Is the metric determined by "
            "the Gauss-Bonnet theorem, or does additional structure (cone "
            "points, variable curvature) emerge from the Genesis operator? "
            "Without specifying the metric, $g_{ij} = g_0\\,e^{-d/\\xi}$ remains "
            "a beautifully motivated guess. The Green's function of the "
            "Laplace-Beltrami operator is known for constant-curvature "
            "surfaces — committing to hyperbolic geometry would immediately "
            "yield computable coupling strengths."
        ),

        "GAP 15": (
            "## 🌊 Mechanics vs. Meaning — The Evaluative Gap\n\n"
            "The framework proves that systems drift toward integration "
            "($r_{-\\to+} > r_{+\\to-}$ by the factor $e^{2h_i/T}$). "
            "But 'drifts toward' is not 'should.' The jump from *mechanistic* "
            "asymmetry to *evaluative* asymmetry — from 'what happens' to "
            "'what is good' — is the oldest problem in philosophy. The "
            "framework borrows a bridge principle from Prigogine: systems "
            "that dissipate energy efficiently are the ones that persist. "
            "Calling this 'good' is an act of definition, not derivation. "
            "**The framework can explain why integration is *stable*, but "
            "not why it is *valuable* — unless stability itself is taken "
            "as the definition of value.**"
        ),

        # Corollary and intermediate metaphors
        "COROLLARY 1": (
            "## 🌊 Metaphorical Reading\n\n"
            "The first step of the Genesis operator takes a pure sine tone "
            "and produces the equivalent of a sonogram's most recognizable "
            "pattern: the Morlet wavelet in space, the $1/f$ spectrum in "
            "time. In renormalization group language, the sine wave is the "
            "Gaussian (free) fixed point, and $\\Gamma^1$ maps it to the "
            "interacting Wilson-Fisher fixed point. This is the framework's "
            "proof of concept: even a single oscillation, passed through "
            "the prism once, generates the critical structure that underlies "
            "all qualitative complexity."
        ),
    }

    key = f"{section_number}"
    if key in metaphors:
        return metaphors[key]

    # Try matching just the number part
    for k, v in metaphors.items():
        if k == section_number or k == kind:
            return v
    return None


# =====================================================================
# MATH EXPRESSION EXTRACTOR
# =====================================================================

class MathExtractor:
    """Extracts all LaTeX math expressions and replaces with placeholders."""

    # Patterns: display math $$ ... $$ and inline math $ ... $
    DISPLAY_RE = re.compile(r'\$\$([\s\S]*?)\$\$')
    INLINE_RE = re.compile(r'(?<!\$)\$(?!\$)([\s\S]*?)(?<!\$)\$(?!\$)')

    def __init__(self):
        self.expressions: List[MathExpr] = []
        self.counter = 0

    def extract(self, text: str) -> Tuple[str, List[MathExpr]]:
        """Replace all math with placeholders. Return cleaned text and list."""
        self.expressions = []
        self.counter = 0
        result = text

        # Extract display math first (higher priority)
        for match in self.DISPLAY_RE.finditer(text):
            expr = MathExpr(
                id=f"{{{{MATH_{self.counter}}}}}",
                original=match.group(1).strip(),
                env="display"
            )
            self.expressions.append(expr)
            result = result.replace(f"$${match.group(1)}$$", expr.id, 1)
            self.counter += 1

        # Then inline math
        for match in self.INLINE_RE.finditer(result):
            expr = MathExpr(
                id=f"{{{{MATH_{self.counter}}}}}",
                original=match.group(1).strip(),
                env="inline"
            )
            self.expressions.append(expr)
            result = result.replace(f"${match.group(1)}$", expr.id, 1)
            self.counter += 1

        return result, self.expressions

    def restore(self, text: str) -> str:
        """Put all math expressions back."""
        result = text
        for expr in self.expressions:
            if expr.env == "display":
                result = result.replace(expr.id, f"$${expr.original}$$")
            else:
                result = result.replace(expr.id, f"${expr.original}$")
        return result

    def get_placeholder_mapping(self) -> Dict[str, str]:
        """Return {placeholder: original_math} for metaphor filling."""
        return {e.id: e.original for e in self.expressions}


# =====================================================================
# SECTION PARSER
# =====================================================================

class SectionParser:
    """Parses markdown document into structured sections."""

    HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)$')
    DEFINITION_RE = re.compile(r'^###\s*(Definition\s+\d+)', re.IGNORECASE)
    THEOREM_RE = re.compile(r'^###\s*(Theorem\s+\d+)', re.IGNORECASE)
    COROLLARY_RE = re.compile(r'^###\s*(Corollary\s+\d+)', re.IGNORECASE)
    LEMMA_RE = re.compile(r'^###\s*(Lemma\s+\d+)', re.IGNORECASE)
    GAP_RE = re.compile(r'^###\s*(\[GAP\s*\d+\])', re.IGNORECASE)

    def parse(self, text: str) -> List[DocumentSection]:
        lines = text.split('\n')
        sections = []
        current_section = None
        current_content = []
        current_level = 0
        section_number = ""

        for line in lines:
            heading_match = self.HEADING_RE.match(line)

            if heading_match:
                # Save previous section
                if current_section and current_content:
                    current_section.content = '\n'.join(current_content).strip()
                    sections.append(current_section)
                    current_content = []

                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                # Extract section number
                num_match = re.match(r'^(\[[^\]]+\]|\w[\w\s]*?\d[\w\s]*?)\s*[-–—]', title)
                if num_match:
                    section_number = num_match.group(1).strip()
                else:
                    # Try to extract leading number
                    num = re.match(r'^(\d+[\.\d]*)', title)
                    section_number = num.group(1) if num else ""

                # Determine kind
                kind = "section"
                upper = title.upper()
                if self.DEFINITION_RE.match(f"### {title}"):
                    kind = "definition"
                elif self.THEOREM_RE.match(f"### {title}"):
                    kind = "theorem"
                elif self.COROLLARY_RE.match(f"### {title}"):
                    kind = "corollary"
                elif self.LEMMA_RE.match(f"### {title}"):
                    kind = "lemma"
                elif self.GAP_RE.match(f"### {title}"):
                    kind = "gap"
                elif 'BOTTOM LINE' in upper or 'SUMMARY' in upper:
                    kind = "summary"
                elif 'FOREWORD' in upper or 'WHAT THIS' in upper:
                    kind = "foreword"

                current_section = DocumentSection(
                    kind=kind,
                    title=title,
                    number=section_number,
                    level=level,
                    content=""
                )
                current_level = level
            elif current_section:
                current_content.append(line)

        # Don't forget the last section
        if current_section and current_content:
            current_section.content = '\n'.join(current_content).strip()
            sections.append(current_section)

        return sections


# =====================================================================
# METAPHOR TRANSLATION ENGINE
# =====================================================================

class MetaphorTranslator:
    """Translates a parsed document section by section."""

    def __init__(self, metaphor_bank: Dict[str, MetaphorEntry]):
        self.bank = metaphor_bank
        self.math_extractor = MathExtractor()

    def _find_matching_metaphors(self, text: str) -> List[MetaphorEntry]:
        """Find all metaphor entries whose triggers appear in the text."""
        text_lower = text.lower()
        matches = []
        for entry in self.bank.values():
            for trigger in entry.triggers:
                if trigger.lower() in text_lower:
                    matches.append(entry)
                    break  # One match per entry is enough
        # Sort by priority (highest first)
        matches.sort(key=lambda e: e.priority, reverse=True)
        return matches

    def _build_metaphor_text(self, entry: MetaphorEntry, 
                              placeholder_map: Dict[str, str]) -> str:
        """Fill in an entry's frame with actual math from placeholders."""
        text = entry.frame
        for slot in entry.math_slots:
            slot_pattern = f"{{{slot}}}"
            # Find corresponding placeholder
            for placeholder, original in placeholder_map.items():
                if placeholder in text:
                    # Wrap inline math in $ for display
                    if entry.env if hasattr(entry, 'env') else 'inline' == 'display':
                        text = text.replace(slot_pattern, 
                                           f"$${original}$$")
                    else:
                        text = text.replace(slot_pattern,
                                           f"${original}$")
                    break
        return text

    def _translate_prose(self, prose: str) -> str:
        """Transform a prose paragraph into metaphorical language."""
        if not prose.strip():
            return ""

        # Extract math
        clean_text, expressions = self.math_extractor.extract(prose)
        placeholder_map = {e.id: e.original for e in expressions}

        # Find matching metaphors
        matches = self._find_matching_metaphors(clean_text)

        if not matches:
            # No metaphor found — return original
            return self.math_extractor.restore(prose)

        # Use the highest-priority metaphor that has content
        primary = matches[0]

        # Build the metaphorical text
        metaphor_text = primary.frame

        # Fill in math slots
        for slot in primary.math_slots:
            slot_pattern = f"{{{slot}}}"
            if slot_pattern in metaphor_text:
                # Find next available math expression
                available = [e for e in expressions 
                           if f"{{{slot}}}" not in slot_pattern or True]
                if available:
                    expr = available[0]
                    if expr.env == 'display':
                        metaphor_text = metaphor_text.replace(
                            slot_pattern, f"$${expr.original}$$")
                    else:
                        metaphor_text = metaphor_text.replace(
                            slot_pattern, f"${expr.original}$")

        return metaphor_text

    def translate_section(self, section: DocumentSection, 
                           section_meta: str = "") -> str:
        """Produce the dual-layer output for a section."""
        output_parts = []

        # --- Original section ---
        output_parts.append(f"### 📐 Original ({section.kind})\n")
        title_line = section.title
        body = section.content
        
        if body.strip():
            output_parts.append(f"{body}\n")
        else:
            output_parts.append("*(No content in this section.)*\n")

        output_parts.append("\n")

        # --- Metaphorical section ---
        # Try section-level metaphor first
        section_metaphor = get_section_metaphor(section.number, section.kind)

        if section_metaphor:
            output_parts.append("### 🌊 Metaphorical Reading\n")
            output_parts.append(section_metaphor + "\n")
        else:
            # Try prose-level metaphor
            if body.strip():
                output_parts.append("### 🌊 Metaphorical Reading\n")
                
                # Split into paragraphs
                paragraphs = body.split('\n\n')
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    # Skip pure math display environments as-is
                    if para.startswith('$$') or para.startswith('|') or \
                       para.startswith('-') or para.startswith('|---'):
                        continue

                    metaphor = self._translate_prose(para)
                    output_parts.append(metaphor + "\n\n")

                    # If we couldn't produce a metaphor, show original
                    if not metaphor.strip() or metaphor.strip() == para:
                        pass  # Already written

        output_parts.append("\n---\n\n")
        return ''.join(output_parts)

    def translate_document(self, sections: List[DocumentSection], 
                           title: str = "") -> str:
        """Translate the entire document."""
        output = []

        output.append(f"# 🎭 Metaphorical Reading: {title}\n\n")
        output.append(
            "> This document presents each section of the original proof "
            "alongside a **metaphorical reading** that preserves all "
            "mathematical content while providing intuitive understanding. "
            "Every equation, definition, theorem statement, and gap is "
            "retained. The 📐 sections are the originals; the 🌊 sections "
            "are the metaphors.\n\n"
            "---\n\n"
        )

        for section in sections:
            output.append(self.translate_section(section))

        return ''.join(output)


# =====================================================================
# FULL PIPELINE
# =====================================================================

class GradientMuse:
    """
    Main application: reads a proof document, parses it,
    and produces the dual-layer metaphor output.
    """

    def __init__(self):
        self.parser = SectionParser()
        self.metaphor_bank = build_metaphor_bank()
        self.translator = MetaphorTranslator(self.metaphor_bank)

    def process(self, input_path: str) -> str:
        """Read, parse, translate, and return the output."""
        text = Path(input_path).read_text(encoding='utf-8')

        # Strip any leading metadata / comments
        lines = text.split('\n')
        start = 0
        for i, line in enumerate(lines):
            if line.startswith('# '):
                start = i
                break

        title = lines[start].lstrip('# ').strip() if start < len(lines) else "Mathematical Proof"
        body = '\n'.join(lines[start:])

        # Parse into sections
        sections = self.parser.parse(body)

        if not sections:
            # Try without heading stripping
            sections = self.parser.parse(text)
            if sections:
                title = sections[0].title

        if not sections:
            return "ERROR: Could not parse any sections from the document."

        # Translate
        output = self.translator.translate_document(sections, title=title)
        return output


# =====================================================================
# CLI
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Gradient Muse — Translate mathematical proofs "
                    "into metaphorical understanding.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python gradient_muse.py proof.md -o output.md
              python gradient_muse.py proof.md --preview
              python gradient_muse.py proof.md --section "T3"
        """)
    )
    parser.add_argument('input', help='Input markdown proof file')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('--preview', action='store_true',
                        help='Print to stdout instead of file')
    parser.add_argument('--section', help='Translate only a specific section')
    parser.add_argument('--list-sections', action='store_true',
                        help='List detected sections and exit')

    args = parser.parse_args()

    muse = GradientMuse()

    if args.list_sections:
        text = Path(args.input).read_text(encoding='utf-8')
        sections = muse.parser.parse(text)
        print(f"\nSections found in '{args.input}':\n")
        for s in sections:
            kind_icon = {
                'definition': '📖', 'theorem': '🔬', 'corollary': '📎',
                'gap': '❓', 'section': '📁', 'proof': '✏️',
                'summary': '📝', 'foreword': '📰', 'lemma': '🔗'
            }.get(s.kind, '📄')
            print(f"  {kind_icon} [{s.kind:12s}] {s.number:8s} {s.title}")
        return

    output = muse.process(args.input)

    if args.section:
        # Filter to only show the requested section
        lines = output.split('\n')
        capturing = False
        filtered = []
        for line in lines:
            if args.section in line:
                capturing = True
            if capturing:
                filtered.append(line)
                if line.startswith('---') and capturing:
                    break
        output = '\n'.join(filtered)

    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"✓ Wrote metaphorical translation to: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
