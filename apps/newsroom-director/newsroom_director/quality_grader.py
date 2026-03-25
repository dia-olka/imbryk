"""Quality grading for LLM-generated newspaper articles.

Two complementary evaluation layers:

1. **Deterministic metrics** — readability, vocabulary richness, sentence
   structure.  Cheap, always consistent, good for drift detection.

2. **LLM-as-judge** — a separate Flash-tier call scores each newspaper on
   a structured rubric (voice, coherence, originality, depth, headlines,
   prompt coverage).  The judge is a *different model tier* than the
   generator (Flash vs Pro), which reduces self-consistency bias.

Scores are stored in the article's ``metadata.quality`` field and fed back
into editorial reflections and generation prompts, creating a closed
improvement loop:

    Generate → Grade → Gate (reject if bad) → Save (with scores)
              → Reflect (with scores) → Generate (with score history)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field

from .generation import GenerationStrategy

logger = logging.getLogger(__name__)


# ── Deterministic text metrics ───────────────────────────────────────────────

_SENTENCE_RE = re.compile(r"[.!?]+(?:\s|$)")
_WORD_RE = re.compile(r"[a-zA-Z\u00C0-\u024F]+(?:['\u2019][a-zA-Z]+)?")
_VOWEL_GROUPS = re.compile(r"[aeiouy]+", re.I)
_PARA_SPLIT = re.compile(r"\n\s*\n")


def _syllable_count(word: str) -> int:
    w = word.lower().rstrip("e")
    count = len(_VOWEL_GROUPS.findall(w))
    return max(count, 1)


@dataclass
class TextMetrics:
    """Deterministic text quality metrics for a single article body."""

    word_count: int = 0
    sentence_count: int = 0
    avg_sentence_len: float = 0.0
    type_token_ratio: float = 0.0
    flesch_reading_ease: float = 0.0
    flesch_kincaid_grade: float = 0.0
    paragraph_count: int = 0


def compute_text_metrics(body: str) -> TextMetrics:
    """Compute deterministic text metrics for an article body."""
    words = _WORD_RE.findall(body)
    word_count = len(words)
    if word_count == 0:
        return TextMetrics()

    sentences = [s.strip() for s in _SENTENCE_RE.split(body) if s.strip()]
    sentence_count = max(len(sentences), 1)

    unique_words = set(w.lower() for w in words)
    total_syllables = sum(_syllable_count(w) for w in words)

    avg_sentence_len = word_count / sentence_count
    ttr = len(unique_words) / word_count
    syl_per_word = total_syllables / word_count

    fre = 206.835 - 1.015 * avg_sentence_len - 84.6 * syl_per_word
    fkg = 0.39 * avg_sentence_len + 11.8 * syl_per_word - 15.59

    paragraphs = [p.strip() for p in _PARA_SPLIT.split(body) if p.strip()]

    return TextMetrics(
        word_count=word_count,
        sentence_count=sentence_count,
        avg_sentence_len=round(avg_sentence_len, 1),
        type_token_ratio=round(ttr, 3),
        flesch_reading_ease=round(fre, 1),
        flesch_kincaid_grade=round(fkg, 1),
        paragraph_count=len(paragraphs),
    )


# ── LLM-as-judge rubric ─────────────────────────────────────────────────────

QUALITY_DIMENSIONS = [
    "voice_consistency",
    "coherence",
    "originality",
    "prompt_coverage",
    "headline_quality",
    "depth",
]


@dataclass
class DimensionScore:
    score: int  # 1-5
    note: str


@dataclass
class QualityReport:
    """Full quality report for one newspaper's edition output."""

    scores: dict[str, DimensionScore] = field(default_factory=dict)
    overall: float = 0.0
    critical_issues: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    text_metrics: TextMetrics = field(default_factory=TextMetrics)

    def to_dict(self) -> dict:
        """Serialize for storage in article metadata."""
        return {
            "scores": {
                k: {"score": v.score, "note": v.note}
                for k, v in self.scores.items()
            },
            "overall": self.overall,
            "critical_issues": self.critical_issues,
            "strengths": self.strengths,
            "text_metrics": asdict(self.text_metrics),
        }

    @staticmethod
    def from_dict(data: dict) -> QualityReport:
        """Deserialize from article metadata."""
        scores = {}
        for k, v in data.get("scores", {}).items():
            scores[k] = DimensionScore(score=v["score"], note=v["note"])
        tm_data = data.get("text_metrics", {})
        return QualityReport(
            scores=scores,
            overall=data.get("overall", 0.0),
            critical_issues=data.get("critical_issues", []),
            strengths=data.get("strengths", []),
            text_metrics=TextMetrics(**{
                k: v for k, v in tm_data.items()
                if k in TextMetrics.__dataclass_fields__
            }),
        )

    def passes_gate(self, threshold: float = 2.5) -> bool:
        """Return True if quality is above the minimum threshold."""
        if not self.scores:
            return True  # no scores = grading failed, don't block
        # Fail if overall < threshold or any dimension scored 1
        if self.overall < threshold:
            return False
        return not any(d.score <= 1 for d in self.scores.values())

    def format_critique(self) -> str:
        """Format a concise critique for injection into a regeneration prompt."""
        parts = []
        low_dims = [
            (k, v) for k, v in self.scores.items() if v.score <= 2
        ]
        if low_dims:
            parts.append("QUALITY ISSUES THAT MUST BE FIXED:")
            for dim, ds in low_dims:
                label = dim.replace("_", " ").title()
                parts.append(f"- {label} ({ds.score}/5): {ds.note}")
        if self.critical_issues:
            parts.append("\nCRITICAL PROBLEMS:")
            for issue in self.critical_issues:
                parts.append(f"- {issue}")
        return "\n".join(parts)

    def format_for_reflection(self) -> str:
        """Format scores for the editorial reflection prompt."""
        lines = ["QUALITY SCORES FOR TODAY'S EDITION:"]
        for dim in QUALITY_DIMENSIONS:
            ds = self.scores.get(dim)
            if ds:
                label = dim.replace("_", " ").title()
                lines.append(f"  {label}: {ds.score}/5 — {ds.note}")
        lines.append(f"  Overall: {self.overall:.1f}/5")

        tm = self.text_metrics
        if tm.word_count > 0:
            lines.append("")
            lines.append("TEXT METRICS:")
            lines.append(f"  Total word count: {tm.word_count}")
            lines.append(f"  Avg sentence length: {tm.avg_sentence_len} words")
            lines.append(f"  Vocabulary richness (TTR): {tm.type_token_ratio}")
            lines.append(f"  Readability (Flesch): {tm.flesch_reading_ease}")

        if self.critical_issues:
            lines.append("")
            lines.append("CRITICAL ISSUES:")
            for issue in self.critical_issues:
                lines.append(f"  - {issue}")
        if self.strengths:
            lines.append("")
            lines.append("STRENGTHS:")
            for s in self.strengths:
                lines.append(f"  - {s}")

        return "\n".join(lines)

    def format_for_generation(self) -> str:
        """Format a compact score summary for injection into generation prompts."""
        if not self.scores:
            return ""
        parts = ["YOUR LAST EDITION'S QUALITY SCORES:"]
        for dim in QUALITY_DIMENSIONS:
            ds = self.scores.get(dim)
            if ds:
                label = dim.replace("_", " ").title()
                parts.append(f"  {label}: {ds.score}/5")
        parts.append(f"  Overall: {self.overall:.1f}/5")
        weak = [
            dim.replace("_", " ").title()
            for dim in QUALITY_DIMENSIONS
            if dim in self.scores and self.scores[dim].score <= 3
        ]
        if weak:
            parts.append(f"  Focus on improving: {', '.join(weak)}")
        return "\n".join(parts)


# ── Grading prompt ───────────────────────────────────────────────────────────

_GRADER_SYSTEM = """\
You are an editorial quality assessor. You evaluate AI-generated newspaper \
articles on a structured rubric. You are NOT the author — you are an \
independent critic. Be honest and specific.

Score each dimension from 1 (terrible) to 5 (excellent):

1. **voice_consistency** — Does the writing have a distinctive editorial \
voice? Would a reader recognise which newspaper this is from without \
seeing the name? (1 = generic LLM output, 5 = unmistakable persona)

2. **coherence** — Does each article flow logically? Are paragraphs \
connected? Is there a clear narrative arc? (1 = disjointed, 5 = seamless)

3. **originality** — Does this feel fresh, or like boilerplate? Are there \
surprising angles, vivid language, or genuine insight? \
(1 = generic/formulaic, 5 = genuinely distinctive)

4. **prompt_coverage** — Are the underlying topics meaningfully explored, \
not just name-dropped? Does the article add analysis beyond restating \
the topic? (1 = topics ignored/superficial, 5 = thorough coverage)

5. **headline_quality** — Are headlines specific, engaging, and true to \
the persona's style? Do they promise something the article delivers? \
(1 = generic/clickbait, 5 = compelling and accurate)

6. **depth** — Does the article explore the topic with substance, or just \
skim the surface? Are there concrete details, examples, implications? \
(1 = surface-level, 5 = thoroughly explored)

Respond with ONLY valid JSON matching this exact schema:
{
  "scores": {
    "voice_consistency": {"score": <1-5>, "note": "<one sentence>"},
    "coherence": {"score": <1-5>, "note": "<one sentence>"},
    "originality": {"score": <1-5>, "note": "<one sentence>"},
    "prompt_coverage": {"score": <1-5>, "note": "<one sentence>"},
    "headline_quality": {"score": <1-5>, "note": "<one sentence>"},
    "depth": {"score": <1-5>, "note": "<one sentence>"}
  },
  "critical_issues": ["<issue>", ...],
  "strengths": ["<strength>", ...]
}

critical_issues: list problems that would make a reader stop reading or \
lose trust (e.g. contradictions, repetitive paragraphs, factual nonsense). \
Empty list if none.
strengths: list 1-2 things the edition did well.

Be concise. Each note is ONE sentence. Do not be generous — a 3 is average, \
not bad. Reserve 5 for genuinely impressive work."""


def _build_grader_user_prompt(
    newspaper_id: str,
    paper_name: str,
    ideology: str,
    content_json: str,
) -> str:
    return (
        f"NEWSPAPER: {paper_name} (id: {newspaper_id})\n"
        f"EDITORIAL IDENTITY: {ideology}\n\n"
        f"TODAY'S OUTPUT:\n{content_json}"
    )


# ── Public API ───────────────────────────────────────────────────────────────


def grade_newspaper(
    newspaper_id: str,
    paper_name: str,
    ideology: str,
    content_json: str,
    generation_strategy: GenerationStrategy,
) -> QualityReport:
    """Grade a single newspaper's output. Returns a QualityReport.

    Uses Flash tier for cost efficiency. If the grading call fails,
    returns an empty report (does not block the pipeline).
    """
    # Compute deterministic metrics across all articles
    try:
        parsed = json.loads(content_json)
        articles = parsed.get("articles", [])
        all_bodies = [a.get("body", "") for a in articles if a.get("body")]
        combined_body = "\n\n".join(all_bodies)
        text_metrics = compute_text_metrics(combined_body)
    except (json.JSONDecodeError, TypeError, AttributeError):
        text_metrics = TextMetrics()

    # LLM-as-judge call
    user_prompt = _build_grader_user_prompt(
        newspaper_id, paper_name, ideology, content_json,
    )

    try:
        raw = generation_strategy.generate(
            _GRADER_SYSTEM, "flash", user_prompt,
        )
        report = _parse_grader_response(raw)
        report.text_metrics = text_metrics
        return report
    except Exception:
        logger.exception("Quality grading failed for %s", newspaper_id)
        return QualityReport(text_metrics=text_metrics)


def _parse_grader_response(raw: str) -> QualityReport:
    """Parse the JSON response from the grading LLM."""
    # Strip markdown fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last lines (fences)
        lines = [line for line in lines if not line.strip().startswith("```")]
        cleaned = "\n".join(lines)

    parsed = json.loads(cleaned)

    scores: dict[str, DimensionScore] = {}
    raw_scores = parsed.get("scores", {})
    for dim in QUALITY_DIMENSIONS:
        entry = raw_scores.get(dim)
        if isinstance(entry, dict):
            score = int(entry.get("score", 3))
            score = max(1, min(5, score))  # clamp
            note = str(entry.get("note", ""))
            scores[dim] = DimensionScore(score=score, note=note)

    overall = (
        sum(d.score for d in scores.values()) / len(scores)
        if scores else 0.0
    )

    return QualityReport(
        scores=scores,
        overall=round(overall, 1),
        critical_issues=parsed.get("critical_issues", []),
        strengths=parsed.get("strengths", []),
    )


def embed_quality_scores(content_json: str, report: QualityReport) -> str:
    """Embed quality scores into the article's metadata.quality field.

    Returns the updated JSON string. If parsing fails, returns the original.
    """
    try:
        parsed = json.loads(content_json)
        if not isinstance(parsed, dict):
            return content_json
        if parsed.get("metadata") is None:
            parsed["metadata"] = {}
        parsed["metadata"]["quality"] = report.to_dict()
        return json.dumps(parsed, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return content_json


def extract_quality_report(content_json: str) -> QualityReport | None:
    """Extract a QualityReport from article metadata, if present."""
    try:
        parsed = json.loads(content_json)
        meta = parsed.get("metadata") or {}
        quality = meta.get("quality")
        if quality:
            return QualityReport.from_dict(quality)
    except (json.JSONDecodeError, TypeError, KeyError):
        pass
    return None


def format_quality_history(
    reports: list[tuple[str, QualityReport]],
) -> str:
    """Format a list of (date, QualityReport) pairs into a trend summary.

    Available for future use: inject multi-edition score trends into generation
    prompts to show the persona its score trajectory over time. Currently the
    pipeline injects only the previous edition's single scorecard via
    ``QualityReport.format_for_generation()``.
    # TODO: wire up in main.py / format_journal_for_generation once multi-edition
    # history is fetched and passed through the pipeline.
    """
    if not reports:
        return ""

    lines = ["QUALITY SCORE HISTORY (recent editions):"]
    for date, report in reports[-5:]:  # last 5 editions max
        if not report.scores:
            continue
        dim_strs = []
        for dim in QUALITY_DIMENSIONS:
            ds = report.scores.get(dim)
            if ds:
                dim_strs.append(f"{dim.replace('_', ' ')[:5]}={ds.score}")
        lines.append(f"  {date}: overall={report.overall:.1f} | {' '.join(dim_strs)}")

    # Compute trend
    scored_reports = [(d, r) for d, r in reports if r.scores]
    if len(scored_reports) >= 2:
        first_avg = scored_reports[0][1].overall
        last_avg = scored_reports[-1][1].overall
        delta = last_avg - first_avg
        if abs(delta) > 0.3:
            direction = "improving" if delta > 0 else "declining"
            lines.append(f"  Trend: {direction} ({delta:+.1f} over {len(scored_reports)} editions)")

    return "\n".join(lines)
