from typing import Mapping

import openai
from openai.types.chat import ChatCompletionUserMessageParam
import httpx

from app.interfaces import LLMClient
from app.core import logger


class OpenAIClient(LLMClient):
    def __init__(
        self,
        model: str,
        url: str | None = None,
        websocket_url: str | httpx.URL | None = None,
        api_key: str | None = None,
        organization: str | None = None,
        project: str | None = None,
        webhook_secret: str | None = None,
        timeout: float | httpx.Timeout | None | openai.NotGiven = openai.not_given,
        max_retries: int = openai.DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.Client | None = None,
        strict_response_validation: bool = False,
    ):
        self.client = openai.OpenAI(
            api_key=api_key,
            organization=organization,
            project=project,
            webhook_secret=webhook_secret,
            base_url=url,
            websocket_base_url=websocket_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            default_query=default_query,
            http_client=http_client,
            _strict_response_validation=strict_response_validation,
        )
        self.model: str = model
        self._logger = logger.bind(
            model=self.model,
            url=url,
            websocket_url=websocket_url,
            timeout=timeout,
        )

    def generate(self, prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                ChatCompletionUserMessageParam(
                    content=prompt,
                    role="user",
                ),
            ]
        )
        content = completion.choices[0].message.content
        if not content:
            self._logger.warning("Нет ответа от LLM")
            return ""
        return content
