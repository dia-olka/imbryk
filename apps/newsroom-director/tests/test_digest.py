"""Tests for the cluster digest construction module."""

import numpy as np

from newsroom_director.distillation.digest import (
    _extract_keywords,
    build_digest,
    build_digests,
    serialize_digest,
)
from newsroom_director.distillation.types import Cluster, Prompt, WeightedPrompt


def _make_wp(text: str, weight: float) -> WeightedPrompt:
    return WeightedPrompt(
        prompt=Prompt(text=text, payment_amount=weight),
        weight=weight,
        embedding=np.random.rand(8).astype(np.float32),
    )


class TestBuildDigest:
    def test_small_cluster_all_verbatim(self):
        cluster = Cluster(
            cluster_id=1,
            prompts=[_make_wp("prompt a", 10.0), _make_wp("prompt b", 5.0)],
            aggregate_weight=15.0,
        )

        digest = build_digest(cluster)

        assert digest.cluster_id == 1
        assert digest.cluster_size == 2
        assert digest.aggregate_weight == 15.0
        assert len(digest.verbatim_prompts) == 2
        # Sorted by weight descending
        assert digest.verbatim_prompts[0][0] == 10.0
        assert digest.verbatim_prompts[1][0] == 5.0
        assert digest.long_tail_summary == ""

    def test_large_cluster_has_summary(self):
        prompts = [_make_wp(f"prompt {i}", float(25 - i)) for i in range(25)]
        cluster = Cluster(
            cluster_id=2,
            prompts=prompts,
            aggregate_weight=sum(wp.weight for wp in prompts),
        )

        digest = build_digest(cluster)

        assert len(digest.verbatim_prompts) == 20  # MAX_VERBATIM
        assert digest.long_tail_summary != ""
        assert digest.cluster_size == 25

    def test_keywords_extracted(self):
        cluster = Cluster(
            cluster_id=0,
            prompts=[
                _make_wp("solar panel efficiency dropping", 5.0),
                _make_wp("solar battery storage options", 5.0),
                _make_wp("solar energy grid connection", 5.0),
            ],
            aggregate_weight=15.0,
        )

        digest = build_digest(cluster)

        assert "solar" in digest.keywords


class TestBuildDigests:
    def test_builds_multiple(self):
        clusters = [
            Cluster(
                cluster_id=i,
                prompts=[_make_wp(f"p{i}", 1.0)],
                aggregate_weight=1.0,
            )
            for i in range(3)
        ]

        digests = build_digests(clusters)
        assert len(digests) == 3


class TestSerializeDigest:
    def test_contains_cluster_header(self):
        cluster = Cluster(
            cluster_id=5,
            prompts=[_make_wp("test prompt", 100.0)],
            aggregate_weight=100.0,
        )
        digest = build_digest(cluster)
        text = serialize_digest(digest)

        assert "CLUSTER #5" in text
        assert "aggregate_weight: 100" in text
        assert "prompt_count: 1" in text

    def test_contains_verbatim_prompts(self):
        cluster = Cluster(
            cluster_id=0,
            prompts=[_make_wp("important event happened", 50.0)],
            aggregate_weight=50.0,
        )
        digest = build_digest(cluster)
        text = serialize_digest(digest)

        assert "important event happened" in text
        assert "[w:50]" in text

    def test_contains_keywords(self):
        cluster = Cluster(
            cluster_id=0,
            prompts=[_make_wp("solar panel efficiency", 5.0)],
            aggregate_weight=5.0,
        )
        digest = build_digest(cluster)
        text = serialize_digest(digest)

        assert "Keywords:" in text

    def test_source_url_included_when_present(self):
        wp = WeightedPrompt(
            prompt=Prompt(
                text="EU AI Act enforcement begins",
                payment_amount=10.0,
                source_url="https://example.com/ai-act",
            ),
            weight=10.0,
            embedding=np.random.rand(8).astype(np.float32),
        )
        cluster = Cluster(cluster_id=0, prompts=[wp], aggregate_weight=10.0)
        digest = build_digest(cluster)
        text = serialize_digest(digest)

        assert "EU AI Act enforcement begins" in text
        assert "Source: https://example.com/ai-act" in text

    def test_source_url_omitted_when_empty(self):
        cluster = Cluster(
            cluster_id=0,
            prompts=[_make_wp("regular prompt text", 5.0)],
            aggregate_weight=5.0,
        )
        digest = build_digest(cluster)
        text = serialize_digest(digest)

        assert "Source:" not in text


class TestExtractKeywords:
    def test_filters_stop_words(self):
        keywords = _extract_keywords(["the sun is shining brightly today"])
        assert "the" not in keywords
        assert "is" not in keywords

    def test_returns_frequent_words(self):
        keywords = _extract_keywords([
            "solar panel installation",
            "solar panel maintenance",
            "solar energy storage",
        ])
        assert keywords[0] == "solar"

    def test_short_words_excluded(self):
        keywords = _extract_keywords(["an AI is helping us"])
        # "an" is a stop word, "AI" is only 2 chars, "is" is a stop word
        assert "an" not in keywords
        assert "ai" not in keywords

    def test_empty_keywords_all_stop_words(self):
        keywords = _extract_keywords(["the and or but in on at to for of"])
        assert keywords == []


class TestDigestEdgeCases:
    def test_single_prompt_verbatim_only(self):
        cluster = Cluster(
            cluster_id=0,
            prompts=[_make_wp("only prompt", 10.0)],
            aggregate_weight=10.0,
        )
        digest = build_digest(cluster)

        assert len(digest.verbatim_prompts) == 1
        assert digest.long_tail_summary == ""

    def test_exactly_max_verbatim_no_long_tail(self):
        from newsroom_director.distillation.digest import MAX_VERBATIM

        prompts = [_make_wp(f"prompt {i}", float(20 - i)) for i in range(MAX_VERBATIM)]
        cluster = Cluster(
            cluster_id=0,
            prompts=prompts,
            aggregate_weight=sum(wp.weight for wp in prompts),
        )
        digest = build_digest(cluster)

        assert len(digest.verbatim_prompts) == MAX_VERBATIM
        assert digest.long_tail_summary == ""

    def test_one_over_max_verbatim_has_long_tail(self):
        from newsroom_director.distillation.digest import MAX_VERBATIM

        count = MAX_VERBATIM + 1
        prompts = [_make_wp(f"prompt {i}", float(count - i)) for i in range(count)]
        cluster = Cluster(
            cluster_id=0,
            prompts=prompts,
            aggregate_weight=sum(wp.weight for wp in prompts),
        )
        digest = build_digest(cluster)

        assert len(digest.verbatim_prompts) == MAX_VERBATIM
        assert digest.long_tail_summary != ""

    def test_non_ascii_keywords_extracted(self):
        # Non-ASCII words should not crash keyword extraction
        cluster = Cluster(
            cluster_id=0,
            prompts=[
                _make_wp("太阳能 renewable energy", 5.0),
                _make_wp("太阳能 solar power", 5.0),
            ],
            aggregate_weight=10.0,
        )
        digest = build_digest(cluster)

        # Must not raise; keywords list is valid (may be empty for CJK-only words)
        assert isinstance(digest.keywords, list)

    def test_lexrank_with_fewer_texts_than_max_sentences(self):
        # LexRank asked for 5 sentences but only 3 available — must not raise
        from newsroom_director.distillation.digest import _lexrank_select

        texts = ["solar panels", "wind turbines", "nuclear power"]
        embeddings = [np.random.rand(8).astype(np.float32) for _ in texts]

        result = _lexrank_select(texts, embeddings, max_sentences=5)

        # All texts should appear since there are fewer than max_sentences
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_cluster_handled_gracefully(self):
        # A cluster with zero prompts should not raise
        cluster = Cluster(
            cluster_id=0,
            prompts=[],
            aggregate_weight=0.0,
        )
        digest = build_digest(cluster)

        assert digest.cluster_size == 0
        assert digest.verbatim_prompts == []
        assert digest.long_tail_summary == ""
        assert digest.keywords == []
