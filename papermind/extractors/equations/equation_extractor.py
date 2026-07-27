# =============================================================================
# PaperMind AI — Equation Extractor
# =============================================================================
# Detects and extracts mathematical equations from document elements using
# pattern matching and heuristic classification. Supports inline equations,
# display equations, and LaTeX-formatted content.
# Produces ExtractedEquation domain objects.
# =============================================================================

from __future__ import annotations

import re
import uuid

from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import (
    DocumentElement,
    ElementType,
    ExtractedEquation,
)

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Regex patterns for equation detection
# ---------------------------------------------------------------------------

# LaTeX delimiters
_LATEX_DISPLAY = re.compile(
    r"\$\$(.+?)\$\$"
    r"|\\begin\{(?:equation|align|gather|multline|eqnarray)\*?\}(.+?)\\end\{(?:equation|align|gather|multline|eqnarray)\*?\}",
    re.DOTALL,
)
_LATEX_INLINE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)")

# Numbered equation labels: (1), (2.3), (A.1), etc.
_EQUATION_LABEL = re.compile(r"\(\s*(?:[A-Za-z]?\d+(?:\.\d+)?)\s*\)\s*$")

# Math operator density pattern
_MATH_OPERATORS = re.compile(r"[=<>≤≥≠±∓∑∏∫∂∇≈∝∞→←↔⊂⊃∈∉∪∩⊕⊗]")

# Greek letter sequences (Unicode)
_GREEK_LETTERS = re.compile(r"[αβγδεζηθικλμνξπρστυφχψωΓΔΘΛΞΠΣΦΨΩ]")

# Function notation: f(x), g(x,y), P(A|B), etc.
_FUNC_NOTATION = re.compile(r"\b[a-zA-Z]\s*\([a-zA-Z0-9,\s|]+\)")

# Superscripts/subscripts patterns
_SUB_SUP = re.compile(r"[_\^]\{.*?\}|[_\^][a-zA-Z0-9]")

# Common LaTeX commands
_LATEX_COMMANDS = re.compile(
    r"\\(?:frac|sqrt|sum|prod|int|lim|log|exp|sin|cos|tan|max|min|sup|inf"
    r"|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|sigma|omega|phi|psi"
    r"|mathbb|mathcal|mathbf|mathrm|mathit|text|operatorname"
    r"|left|right|big|Big|bigg|Bigg"
    r"|cdot|times|div|pm|mp|leq|geq|neq|approx|equiv|sim|propto"
    r"|infty|partial|nabla|forall|exists|in|notin|subset|supset"
    r"|cup|cap|oplus|otimes|vec|hat|bar|tilde|dot)\b"
)

# Variable extraction pattern
_VARIABLE_PATTERN = re.compile(r"\b([a-zA-Z](?:_\{[^}]+\}|_[a-zA-Z0-9])?)\b")


class EquationExtractor:
    """
    Extracts mathematical equations from document elements.

    Detection strategies:
      1. LaTeX-delimited: $...$ for inline, $$...$$ or \\begin{equation} for display.
      2. Element type: Elements already classified as EQUATION by the parser.
      3. Content heuristics: High density of math operators, Greek letters,
         and function notation in text elements.
    """

    def __init__(
        self,
        min_math_score: float = 0.55,
        min_operators: int = 1,
    ) -> None:
        """
        Args:
            min_math_score: Minimum "math density" score to classify as equation.
            min_operators: Minimum number of math operators for heuristic detection.
        """
        self._min_math_score = min_math_score
        self._min_operators = min_operators

    def extract_equations(
        self,
        elements: list[DocumentElement],
    ) -> list[ExtractedEquation]:
        """
        Extract equations from a list of document elements.

        Args:
            elements: Flat list of DocumentElements from the document.

        Returns:
            List of ExtractedEquation domain objects.
        """
        equations: list[ExtractedEquation] = []
        seen_texts: set[str] = set()

        for element in elements:
            # 1. Elements already tagged as equations by the parser
            if element.element_type == ElementType.EQUATION:
                eq = self._create_equation(element, is_inline=False)
                if eq and eq.raw_text not in seen_texts:
                    equations.append(eq)
                    seen_texts.add(eq.raw_text)
                continue

            content = element.content

            # 2. LaTeX display equations
            for match in _LATEX_DISPLAY.finditer(content):
                latex_text = match.group(1) or match.group(2)
                if latex_text and latex_text.strip() not in seen_texts:
                    eq = ExtractedEquation(
                        id=str(uuid.uuid4()),
                        page_number=element.page_number,
                        bounding_box=element.bounding_box,
                        raw_text=match.group(0).strip(),
                        latex=latex_text.strip(),
                        is_inline=False,
                        variables=self._extract_variables(latex_text),
                    )
                    equations.append(eq)
                    seen_texts.add(latex_text.strip())

            # 3. LaTeX inline equations
            for match in _LATEX_INLINE.finditer(content):
                latex_text = match.group(1)
                if latex_text and latex_text.strip() not in seen_texts:
                    eq = ExtractedEquation(
                        id=str(uuid.uuid4()),
                        page_number=element.page_number,
                        bounding_box=element.bounding_box,
                        raw_text=match.group(0).strip(),
                        latex=latex_text.strip(),
                        is_inline=True,
                        variables=self._extract_variables(latex_text),
                    )
                    equations.append(eq)
                    seen_texts.add(latex_text.strip())

            # 4. Heuristic detection: high math density (only for shorter, concentrated math expressions)
            if element.element_type == ElementType.PARAGRAPH and len(content) < 250:
                math_score = self._compute_math_score(content)
                if math_score >= self._min_math_score:
                    eq_text = content.strip()
                    if eq_text not in seen_texts:
                        eq = ExtractedEquation(
                            id=str(uuid.uuid4()),
                            page_number=element.page_number,
                            bounding_box=element.bounding_box,
                            raw_text=eq_text,
                            latex=self._clean_to_latex(eq_text),
                            is_inline=len(eq_text) < 80,
                            variables=self._extract_variables(eq_text),
                        )
                        equations.append(eq)
                        seen_texts.add(eq_text)

        log.info(
            "Equation extraction complete",
            total_equations=len(equations),
            inline=sum(1 for eq in equations if eq.is_inline),
            display=sum(1 for eq in equations if not eq.is_inline),
        )
        return equations

    def _clean_to_latex(self, text: str) -> str:
        """Convert raw math text into clean LaTeX syntax for KaTeX rendering."""
        clean = text.strip()
        clean = re.sub(r"^\$\$\s*", "", clean)
        clean = re.sub(r"\s*\$\$$", "", clean)
        clean = clean.replace("∈R", r"\in \mathbb{R}")
        clean = clean.replace("∈ R", r"\in \mathbb{R}")
        clean = clean.replace("Proj (", r"\text{Proj}(")
        clean = clean.replace("Enc (", r"\text{Enc}(")
        clean = clean.replace("Aug (", r"\text{Aug}(")
        clean = clean.replace("exp (", r"\exp(")
        clean = clean.replace("•", r"\cdot")
        return clean

    def _create_equation(
        self,
        element: DocumentElement,
        is_inline: bool,
    ) -> ExtractedEquation | None:
        """Create an ExtractedEquation from a DocumentElement."""
        content = element.content.strip()
        if not content:
            return None

        # Try to extract LaTeX if present
        latex = None
        latex_match = _LATEX_DISPLAY.search(content) or _LATEX_INLINE.search(content)
        if latex_match:
            latex = (latex_match.group(1) or latex_match.group(0)).strip()
        else:
            latex = self._clean_to_latex(content)

        # Strip equation labels like (1), (2.3)
        label_match = _EQUATION_LABEL.search(content)
        raw = content
        if label_match:
            raw = content[: label_match.start()].strip()

        return ExtractedEquation(
            id=str(uuid.uuid4()),
            page_number=element.page_number,
            bounding_box=element.bounding_box,
            raw_text=raw,
            latex=latex,
            is_inline=is_inline,
            variables=self._extract_variables(content),
        )

    def _compute_math_score(self, text: str) -> float:
        """Compute a heuristic 'math density' score for a text string."""
        if not text or len(text) < 3:
            return 0.0

        text_len = len(text)
        score = 0.0

        # Math operators
        operators = len(_MATH_OPERATORS.findall(text))
        if operators >= self._min_operators:
            score += min(0.4, operators * 0.15)

        # Greek letters
        greek = len(_GREEK_LETTERS.findall(text))
        if greek > 0:
            score += min(0.3, greek * 0.1)

        # LaTeX commands
        latex_cmds = len(_LATEX_COMMANDS.findall(text))
        if latex_cmds > 0:
            score += min(0.4, latex_cmds * 0.15)

        # Function notation
        funcs = len(_FUNC_NOTATION.findall(text))
        if funcs > 0:
            score += min(0.2, funcs * 0.05)

        # Subscripts/superscripts
        subsup = len(_SUB_SUP.findall(text))
        if subsup > 0:
            score += min(0.2, subsup * 0.05)

        # Short lines with operators are more likely equations
        if text_len < 100 and operators >= 1:
            score += 0.2

        # Penalize long prose paragraphs
        if text_len > 180:
            score -= 0.3

        # Equation label at end
        if _EQUATION_LABEL.search(text):
            score += 0.25

        return max(0.0, min(1.0, score))

    @staticmethod
    def _extract_variables(text: str) -> list[str]:
        """Extract likely variable names from equation text."""
        exclude = {
            "and", "or", "not", "the", "for", "all", "any", "let", "if",
            "then", "else", "where", "with", "from", "into", "over", "under",
            "sin", "cos", "tan", "log", "exp", "lim", "max", "min", "sup", "inf",
            "frac", "sqrt", "sum", "prod", "int", "text", "mathrm", "mathbf",
            "left", "right", "big", "cdot", "times", "div",
        }

        matches = _VARIABLE_PATTERN.findall(text)
        variables = []
        seen: set[str] = set()
        for var in matches:
            var_clean = var.strip()
            if (
                var_clean
                and var_clean.lower() not in exclude
                and var_clean not in seen
                and len(var_clean) <= 10
            ):
                variables.append(var_clean)
                seen.add(var_clean)

        return variables
