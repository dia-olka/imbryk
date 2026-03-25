"""Tests for the quality grading module."""

import json

from newsroom_director.generation import StubGenerationStrategy
from newsroom_director.quality_grader import (
    DimensionScore,
    QualityReport,
    _parse_grader_response,
    compute_text_metrics,
    embed_quality_scores,
    extract_quality_report,
    format_quality_history,
    grade_newspaper,
)

# ── Sample data ──────────────────────────────────────────────────────────────

_SAMPLE_BODY = (
    "The government announced sweeping reforms to the financial sector today. "
    "Markets responded with cautious optimism as investors weighed the long-term "
    "implications of the new regulatory framework.\n\n"
    "Analysts predict the changes will benefit smaller institutions while placing "
    "additional compliance burdens on the largest banks. The reform package, "
    "which includes provisions for digital currency oversight, represents the "
    "most significant overhaul in two decades.\n\n"
    "Critics argue that the timeline is too aggressive, pointing to the "
    "complexity of implementing cross-border regulatory harmonisation."
)

_SAMPLE_NEWSPAPER_JSON = json.dumps({
    "newspaper_name": "The Sovereign",
    "frontPageImagePrompt": "A dramatic shot of parliament",
    "articles": [
        {
            "headline": "Financial Reform Package Signals New Era of Oversight",
            "body": _SAMPLE_BODY,
        },
        {
            "headline": "Coalition Fractures Over Defence Spending",
            "body": "The ruling coalition faces internal tensions over the proposed "
                    "defence budget increase. Senior party officials have privately "
                    "expressed concern about the allocation priorities.",
        },
    ],
    "metadata": None,
})

_VALID_GRADER_RESPONSE = json.dumps({
    "scores": {
        "voice_consistency": {"score": 4, "note": "Strong sovereign tone throughout"},
        "coherence": {"score": 3, "note": "Abrupt transition in article 2"},
        "originality": {"score": 2, "note": "Several generic LLM phrases"},
        "prompt_coverage": {"score": 4, "note": "All topics meaningfully addressed"},
        "headline_quality": {"score": 3, "note": "Informative but not engaging"},
        "depth": {"score": 4, "note": "Good analysis in lead article"},
    },
    "critical_issues": ["Article 2 lacks supporting evidence"],
    "strengths": ["Lead article provides strong regulatory analysis"],
})

_LOW_QUALITY_GRADER_RESPONSE = json.dumps({
    "scores": {
        "voice_consistency": {"score": 1, "note": "Completely generic output"},
        "coherence": {"score": 2, "note": "Disjointed paragraphs"},
        "originality": {"score": 1, "note": "Pure boilerplate"},
        "prompt_coverage": {"score": 2, "note": "Topics barely mentioned"},
        "headline_quality": {"score": 2, "note": "Generic clickbait"},
        "depth": {"score": 1, "note": "Surface-level only"},
    },
    "critical_issues": ["Entire edition reads like generic AI output"],
    "strengths": [],
})


# ── Deterministic metrics ────────────────────────────────────────────────────


class TestComputeTextMetrics:
    def test_basic_text(self):
        metrics = compute_text_metrics(_SAMPLE_BODY)
        assert metrics.word_count > 50
        assert metrics.sentence_count >= 3
        assert metrics.avg_sentence_len > 10
        assert 0 < metrics.type_token_ratio <= 1
        assert metrics.paragraph_count == 3

    def test_empty_text(self):
        metrics = compute_text_metrics("")
        assert metrics.word_count == 0
        assert metrics.sentence_count == 0
        assert metrics.type_token_ratio == 0

    def test_single_sentence(self):
        metrics = compute_text_metrics("Hello world this is a test.")
        assert metrics.word_count == 6
        assert metrics.sentence_count == 1
        assert metrics.paragraph_count == 1

    def test_readability_range(self):
        metrics = compute_text_metrics(_SAMPLE_BODY)
        # Flesch Reading Ease: typical journalism is 30-70
        assert -50 < metrics.flesch_reading_ease < 120
        # FK Grade: typical journalism is 8-16
        assert 0 < metrics.flesch_kincaid_grade < 25

    def test_vocabulary_richness(self):
        # Repetitive text should have lower TTR
        repetitive = "the cat sat. the cat sat. the cat sat. the cat sat."
        diverse = "the quick brown fox jumped over the lazy sleeping dog."
        rep_metrics = compute_text_metrics(repetitive)
        div_metrics = compute_text_metrics(diverse)
        assert rep_metrics.type_token_ratio < div_metrics.type_token_ratio


# ── LLM grader response parsing ─────────────────────────────────────────────


class TestParseGraderResponse:
    def test_valid_response(self):
        report = _parse_grader_response(_VALID_GRADER_RESPONSE)
        assert len(report.scores) == 6
        assert report.scores["voice_consistency"].score == 4
        assert report.scores["originality"].score == 2
        assert 2.0 < report.overall < 5.0
        assert len(report.critical_issues) == 1
        assert len(report.strengths) == 1

    def test_markdown_fenced_response(self):
        fenced = f"```json\n{_VALID_GRADER_RESPONSE}\n```"
        report = _parse_grader_response(fenced)
        assert len(report.scores) == 6
        assert report.scores["voice_consistency"].score == 4

    def test_score_clamping(self):
        bad = json.dumps({
            "scores": {
                "voice_consistency": {"score": 99, "note": "test"},
                "coherence": {"score": -5, "note": "test"},
            },
            "critical_issues": [],
            "strengths": [],
        })
        report = _parse_grader_response(bad)
        assert report.scores["voice_consistency"].score == 5
        assert report.scores["coherence"].score == 1

    def test_missing_dimensions(self):
        partial = json.dumps({
            "scores": {
                "voice_consistency": {"score": 3, "note": "ok"},
            },
            "critical_issues": [],
            "strengths": [],
        })
        report = _parse_grader_response(partial)
        assert len(report.scores) == 1
        assert report.overall == 3.0


# ── Quality gate ─────────────────────────────────────────────────────────────


class TestQualityGate:
    def test_passes_with_good_scores(self):
        report = _parse_grader_response(_VALID_GRADER_RESPONSE)
        assert report.passes_gate is True

    def test_fails_with_low_overall(self):
        report = _parse_grader_response(_LOW_QUALITY_GRADER_RESPONSE)
        assert report.passes_gate is False
        assert report.overall < 2.5

    def test_fails_with_any_score_1(self):
        # Even if overall is above 2.5, a single 1 triggers failure
        scores = {
            "voice_consistency": DimensionScore(score=1, note="bad"),
            "coherence": DimensionScore(score=5, note="great"),
            "originality": DimensionScore(score=5, note="great"),
            "prompt_coverage": DimensionScore(score=5, note="great"),
            "headline_quality": DimensionScore(score=5, note="great"),
            "depth": DimensionScore(score=5, note="great"),
        }
        report = QualityReport(scores=scores, overall=4.3)
        assert report.passes_gate is False

    def test_passes_gate_when_no_scores(self):
        # Grading failure should not block the pipeline
        report = QualityReport()
        assert report.passes_gate is True


# ── Embed / extract round-trip ───────────────────────────────────────────────


class TestEmbedExtract:
    def test_round_trip(self):
        report = _parse_grader_response(_VALID_GRADER_RESPONSE)
        report.text_metrics = compute_text_metrics(_SAMPLE_BODY)

        embedded = embed_quality_scores(_SAMPLE_NEWSPAPER_JSON, report)
        parsed = json.loads(embedded)
        assert "quality" in parsed["metadata"]

        extracted = extract_quality_report(embedded)
        assert extracted is not None
        assert extracted.overall == report.overall
        assert extracted.scores["voice_consistency"].score == 4
        assert extracted.text_metrics.word_count == report.text_metrics.word_count

    def test_embed_preserves_existing_metadata(self):
        with_meta = json.dumps({
            "newspaper_name": "Test",
            "articles": [],
            "metadata": {"existing_key": "value"},
        })
        report = QualityReport(
            scores={"depth": DimensionScore(score=3, note="ok")},
            overall=3.0,
        )
        embedded = embed_quality_scores(with_meta, report)
        parsed = json.loads(embedded)
        assert parsed["metadata"]["existing_key"] == "value"
        assert "quality" in parsed["metadata"]

    def test_extract_returns_none_when_no_quality(self):
        assert extract_quality_report(_SAMPLE_NEWSPAPER_JSON) is None

    def test_embed_handles_invalid_json(self):
        result = embed_quality_scores("not json", QualityReport())
        assert result == "not json"


# ── Formatting ───────────────────────────────────────────────────────────────


class TestFormatting:
    def _make_report(self, overall: float) -> QualityReport:
        scores = {}
        for dim in ["voice_consistency", "coherence", "originality",
                     "prompt_coverage", "headline_quality", "depth"]:
            scores[dim] = DimensionScore(score=round(overall), note="test")
        return QualityReport(scores=scores, overall=overall)

    def test_format_critique(self):
        report = _parse_grader_response(_LOW_QUALITY_GRADER_RESPONSE)
        critique = report.format_critique()
        assert "QUALITY ISSUES" in critique
        assert "Voice Consistency" in critique
        assert "CRITICAL PROBLEMS" in critique

    def test_format_for_reflection(self):
        report = _parse_grader_response(_VALID_GRADER_RESPONSE)
        report.text_metrics = compute_text_metrics(_SAMPLE_BODY)
        text = report.format_for_reflection()
        assert "QUALITY SCORES" in text
        assert "Voice Consistency: 4/5" in text
        assert "TEXT METRICS" in text
        assert "CRITICAL ISSUES" in text

    def test_format_for_generation(self):
        report = _parse_grader_response(_VALID_GRADER_RESPONSE)
        text = report.format_for_generation()
        assert "QUALITY SCORES" in text
        assert "Focus on improving" in text
        # Originality scored 2, should be in focus list
        assert "Originality" in text

    def test_format_quality_history(self):
        reports = [
            ("2026-03-20", self._make_report(3.0)),
            ("2026-03-21", self._make_report(3.5)),
            ("2026-03-22", self._make_report(4.0)),
        ]
        text = format_quality_history(reports)
        assert "QUALITY SCORE HISTORY" in text
        assert "2026-03-20" in text
        assert "improving" in text

    def test_format_quality_history_empty(self):
        assert format_quality_history([]) == ""

    def test_format_quality_history_declining(self):
        reports = [
            ("2026-03-20", self._make_report(4.0)),
            ("2026-03-21", self._make_report(3.5)),
            ("2026-03-22", self._make_report(2.5)),
        ]
        text = format_quality_history(reports)
        assert "declining" in text


# ── Integration: grade_newspaper with StubStrategy ───────────────────────────


class TestGradeNewspaper:
    def test_grade_with_stub_strategy(self):
        stub = StubGenerationStrategy(responses={"flash": _VALID_GRADER_RESPONSE})
        report = grade_newspaper(
            newspaper_id="sovereign",
            paper_name="The Sovereign",
            ideology="establishment conservatism",
            content_json=_SAMPLE_NEWSPAPER_JSON,
            generation_strategy=stub,
        )
        assert report.overall > 0
        assert len(report.scores) == 6
        # Deterministic metrics should also be computed
        assert report.text_metrics.word_count > 0

    def test_grade_handles_llm_failure(self):
        # When the LLM returns garbage, should still return deterministic metrics
        stub = StubGenerationStrategy(responses={"flash": "not json at all"})
        report = grade_newspaper(
            newspaper_id="sovereign",
            paper_name="The Sovereign",
            ideology="establishment conservatism",
            content_json=_SAMPLE_NEWSPAPER_JSON,
            generation_strategy=stub,
        )
        # LLM scores empty, but text metrics computed
        assert len(report.scores) == 0
        assert report.text_metrics.word_count > 0
        # Should pass gate (no scores = don't block)
        assert report.passes_gate is True

    def test_grade_handles_invalid_article_json(self):
        stub = StubGenerationStrategy(responses={"flash": _VALID_GRADER_RESPONSE})
        report = grade_newspaper(
            newspaper_id="sovereign",
            paper_name="The Sovereign",
            ideology="establishment conservatism",
            content_json="not json",
            generation_strategy=stub,
        )
        assert report.text_metrics.word_count == 0
