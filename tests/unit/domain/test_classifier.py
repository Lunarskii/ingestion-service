from types import SimpleNamespace
import re

import pytest

from app.domain.classifier.rules import Classifier


class TestClassifier:
    @pytest.fixture(autouse=True)
    def patch_loader(self, monkeypatch):
        monkeypatch.setattr(
            "app.domain.classifier.rules.load_rules_from_yaml",
            lambda path: [],
        )
        yield

    def test_normalize_text(self):
        assert Classifier._normalize_text("  HeLLo World  ") == "hello world"

    def test_count_keyword_occurrences(self):
        assert Classifier._count_keyword_occurrences(
            "aaa b a a", "a"
        ) == "aaa b a a".count("a")
        assert Classifier._count_keyword_occurrences("", "a") == 0
        assert Classifier._count_keyword_occurrences("text", "") == 0

    def test_count_regex_occurrences(self):
        pattern = re.compile(r"\d+")
        assert Classifier._count_regex_occurrences("123 abc 45", pattern) == 2
        assert Classifier._count_regex_occurrences("", pattern) == 0

    def test_score_rule_keyword_and_regex(self):
        classifier = Classifier("/does/not/matter.yml")

        rule = SimpleNamespace(
            negative_keywords=[],
            keywords=["foo"],
            regex=[re.compile(r"bar$"), re.compile(r"\sfoo\s")],
            body_weight=2,
            weight=1.5,
            topic="topic",
            min_score=0,
        )

        text = "foo foo bar bar bar"
        score, detail = classifier.score_rule(text, rule)

        # keywords: 2 совпадения * 2 (body_weight) = 4
        # regex: 2 совпадения * 2 (body_weight) = 4
        # score = 8, итоговый = 8 * weight(1.5) = 12
        assert score == pytest.approx(12.0)

        assert len(detail.keyword_matches) == 1
        keyword_match = detail.keyword_matches[0]
        assert keyword_match.keyword == "foo"
        assert keyword_match.count == 2

        assert len(detail.regex_matches) == 2
        regex_match0 = detail.regex_matches[0]
        assert regex_match0.regex == r"bar$"
        assert regex_match0.count == 1
        regex_match1 = detail.regex_matches[1]
        assert regex_match1.regex == r"\sfoo\s"
        assert regex_match1.count == 1

    def test_score_rule_negative_keyword_blocks(self):
        classifier = Classifier("/does/not/matter.yml")

        rule = SimpleNamespace(
            negative_keywords=["not good"],
            keywords=["not good"],
            regex=[re.compile(r"^this|ignored$|\sgood\s")],
            body_weight=1,
            weight=1,
            topic="topic",
            min_score=0,
        )

        text = "this is not good and should be ignored"
        score, detail = classifier.score_rule(text, rule)

        assert score == 0
        assert detail.keyword_matches == []
        assert detail.regex_matches == []

    def test_classify_text_top_k_and_min_score(self):
        classifier = Classifier("/does/not/matter.yml")

        r1 = SimpleNamespace(
            negative_keywords=[],
            keywords=["aaa"],
            regex=[],
            body_weight=1,
            weight=2.0,
            topic="high",
            min_score=0,
        )
        r2 = SimpleNamespace(
            negative_keywords=[],
            keywords=["b"],
            regex=[],
            body_weight=1,
            weight=1.0,
            topic="low",
            min_score=0,
        )

        text = "aaa aaa b"

        # r1: 2 совпадения * 1 * 2.0 = 4.0
        # r2: 1 совпадение * 1 * 1.0 = 1.0
        results = classifier.classify_text(text, rules=[r1, r2])
        assert [result.topic for result in results] == ["high", "low"]

        top1 = classifier.classify_text(text, rules=[r1, r2], top_k=1)
        assert len(top1) == 1
        assert top1[0].topic == "high"

        filtered = classifier.classify_text(text, rules=[r1, r2], min_score=2)
        assert len(filtered) == 1
        assert filtered[0].topic == "high"

    # @pytest.mark.asyncio
    # async def test_classify_document_success(
    #     self,
    #     monkeypatch,
    #     mock_silver_storage: MagicMock,
    #     document_id: str = ValueGenerator.uuid(),
    #     silver_storage_path: str = "some/path/document.json",
    # ):
    #     classifier = Classifier("/does/not/matter.yml")
    #
    #     class DummyDocumentRepository:
    #         def __init__(self, session): ...
    #
    #         async def get(self, id):
    #             return SimpleNamespace(silver_storage_path=silver_storage_path)
    #
    #     monkeypatch.setattr(
    #         "app.domain.classifier.rules.DocumentRepository",
    #         DummyDocumentRepository,
    #     )
    #
    #     mock_silver_storage.get.return_value = (
    #         b'[{"text": "foo bar"}, {"text": "bar baz"}]'
    #     )
    #
    #     rule = SimpleNamespace(
    #         negative_keywords=[],
    #         keywords=["bar"],
    #         regex=[],
    #         body_weight=1,
    #         weight=1.0,
    #         topic="has_bar",
    #         min_score=0,
    #     )
    #
    #     results = await classifier.classify_document(
    #         document_id=document_id,
    #         silver_storage=mock_silver_storage,
    #         rules=[rule],
    #     )
    #
    #     assert len(results) == 1
    #     result = results[0]
    #     assert result.topic == "has_bar"
    #     assert result.score == pytest.approx(2.0)
    #
    #     assert_called_once_with(
    #         mock_silver_storage.get,
    #         path=silver_storage_path,
    #     )
    #
    # @pytest.mark.asyncio
    # async def test_classify_document_missing_silver_path_raises(
    #     self,
    #     monkeypatch,
    #     mock_document_repo: MagicMock,
    #     mock_silver_storage: MagicMock,
    #     document_id: str = ValueGenerator.uuid(),
    # ):
    #     classifier = Classifier("/does/not/matter.yml")
    #
    #     class DummyDocumentRepository:
    #         def __init__(self, session): ...
    #
    #         async def get(self, id):
    #             return SimpleNamespace(silver_storage_path=None)
    #
    #     monkeypatch.setattr(
    #         "app.domain.classifier.rules.DocumentRepository",
    #         DummyDocumentRepository,
    #     )
    #
    #     with pytest.raises(RuntimeError):
    #         await classifier.classify_document(
    #             document_id=document_id,
    #             silver_storage=mock_silver_storage,
    #         )
