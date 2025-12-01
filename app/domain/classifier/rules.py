import re

from app.domain.classifier.schemas import (
    ClassificationResult,
    Rule,
    MatchDetail,
    KeywordMatch,
    RegexMatch,
)
from app.domain.classifier.utils import load_rules_from_yaml
from app.core import settings


class Classifier:
    def __init__(self, rules_path: str):
        self.rules = load_rules_from_yaml(rules_path)

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """
        Нормализует текст в общий формат.

        :param text: Текст, который нужно нормализовать.

        :return: Нормализованный текст.
        """

        return text.strip().lower()

    @classmethod
    def _count_keyword_occurrences(cls, text: str, keyword: str) -> int:
        """
        Подсчитывает количество совпадений в тексте с ключевым словом.

        :param text: Текст, в котором будет подсчитываться количество совпадений.
        :param keyword: Ключевое слово, по которому будет искаться совпадение.

        :return: Количество совпадений в тексте.
        """

        if not text or not keyword:
            return 0
        return text.count(keyword)

    @classmethod
    def _count_regex_occurrences(cls, text: str, pattern: re.Pattern) -> int:
        """
        Подсчитывает количество совпадений в тексте с регулярным выражением.

        :param text: Текст, в котором будет подсчитываться количество совпадений.
        :param pattern: Шаблон регулярного выражения, по которому будет искаться совпадение.

        :return: Количество совпадений в тексте.
        """

        if not text:
            return 0
        return len(pattern.findall(text))

    def score_rule(
        self,
        text: str,
        rule: Rule,
    ) -> tuple[float, MatchDetail]:
        """
        Подсчитывает счет по определенному правилу, и также сохраняет все
        ключевые слова и регулярные выражения, если нашлись совпадения в тексте.

        :param text: Текст, который будет анализироваться.
        :param rule: Правило, по которому будет подсчитываться счет для заданного текста,
                     и по которому будут извлекаться найденные ключевые слова и регулярные выражения.

        :return: Счет и результаты совпадений.
        """

        score: float = 0.0
        detail = MatchDetail()

        for negative_keyword in rule.negative_keywords:
            negative_keyword = self._normalize_text(negative_keyword)
            if negative_keyword and negative_keyword in text:
                return score, detail

        for keyword in rule.keywords:
            num_kw_occurrences: int = self._count_keyword_occurrences(
                text=text,
                keyword=keyword,
            )
            if num_kw_occurrences:
                score += num_kw_occurrences * rule.body_weight
                detail.keyword_matches.append(
                    KeywordMatch(
                        keyword=keyword,
                        count=num_kw_occurrences,
                    ),
                )

        for regex in rule.regex:
            num_regex_occurrences: int = self._count_regex_occurrences(
                text=text,
                pattern=regex,
            )
            if num_regex_occurrences:
                score += num_regex_occurrences * rule.body_weight
                detail.regex_matches.append(
                    RegexMatch(
                        regex=regex.pattern,
                        count=num_regex_occurrences,
                    ),
                )

        return score * rule.weight, detail

    def classify_text(
        self,
        text: str,
        *,
        top_k: int = settings.classifier.default_top_k,
        rules: list[Rule] | None = None,
        min_score: int | None = None,
    ) -> list[ClassificationResult]:
        """
        Классифицирует текст на основе заданных правил.

        :param text: Текст, который будет анализироваться.
        :param top_k: Количество предложенных тем. Если возможных предложенных тем будет меньше,
                      чем top_k, то будут предоставлены все темы, иначе будет возвращено top_k тем.
        :param rules: Правила, на основе которых будет анализироваться текст.
        :param min_score: Минимальный счет, который должна преодолеть тема, чтобы попасть в предложенные темы.

        :return: Список предложенный тем, получившийся счет для каждой темы и набор совпадений.
        """

        rules: list[Rule] = rules or self.rules
        result: list[ClassificationResult] = []

        for rule in rules:
            score, detail = self.score_rule(text, rule)

            if score > 0 and score >= (min_score or rule.min_score):
                result.append(
                    ClassificationResult(
                        topic=rule.topic,
                        score=score,
                        matches=detail,
                    ),
                )

        result.sort(
            key=lambda x: x.score,
            reverse=True,
        )
        if top_k:
            return result[:top_k]
        return result
