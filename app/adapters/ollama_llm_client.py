import ollama

from app.interfaces import LLMClient
from app.core import logger


class OllamaClient(LLMClient):
    """
    LLM клиент, который работает с моделями Ollama.
    """

    def __init__(
        self,
        model: str,
        url: str | None = None,
        api_key: str | None = None,
        timeout: int = 30,
    ):
        self.client = ollama.Client(
            host=url,
            headers={"Authorization": api_key} if api_key else None,
            timeout=timeout,
        )
        self.model: str = model
        self._logger = logger.bind(
            url=url,
            model_name=model,
            timeout=timeout,
        )

        try:
            self.available_models = [
                ollama_model.model for ollama_model in self.client.list().models
            ]
        except ollama.ResponseError as e:
            self._logger.error(
                "Произошла ошибка при извлечении списка моделей: возможно, Ollama API недоступен",
                error_message=str(e),
            )
            raise e

        if self.model not in self.available_models:
            try:
                self.client.pull(model)
            except ollama.ResponseError as e:
                self._logger.warning(
                    f"Произошла ошибка при загрузке модели: возможно, модель '{model}' уже загружена",
                    error_message=str(e),
                )

    def generate(self, prompt: str) -> str:
        """
        Принимает на вход текстовый запрос (``prompt``) и возвращает ответ LLM.

        :param prompt: Исходный запрос для LLM.

        :return: Ответ LLM.
        """

        response: ollama.GenerateResponse = self.client.generate(
            model=self.model,
            prompt=prompt,
        )
        return response.response
