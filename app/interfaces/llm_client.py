from typing import Protocol


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str:
        """
        Принимает на вход текстовый запрос (``prompt``) и возвращает ответ LLM.

        :param prompt: Исходный запрос для LLM.

        :return: Ответ LLM.
        """

        ...
