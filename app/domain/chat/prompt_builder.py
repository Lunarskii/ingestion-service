from typing import Iterable

import tiktoken


INSTRUCTION = "Основываясь на следующем контексте, ответь на вопрос."


class PromptBuilder:
    def __init__(
        self,
        max_prompt_tokens: int = 4096,
        *,
        tokenizer_encoding_name: str = "cl100k_base",
    ):
        self.max_prompt_tokens = max_prompt_tokens
        self.tokenizer_encoding_name = tokenizer_encoding_name

    def _apply_instruction(
        self,
        instruction: str,
        question: str,
        context: str,
    ) -> str:
        return "\n".join(
            (
                "Инструкция:",
                instruction,
                "---",
                "Вопрос:",
                question,
                "---",
                "Контекст:",
                context,
            ),
        )

    def _build_prompts(
        self,
        instruction: str,
        question: str,
        context: Iterable[str],
        *,
        context_seperator: str = "\n",
    ) -> list[str]:
        tokenizer: tiktoken.Encoding = tiktoken.get_encoding(self.tokenizer_encoding_name)
        def _num_tokens(s: str) -> int:
            return len(tokenizer.encode(s))

        system_prompt: str = self._apply_instruction(
            instruction=instruction,
            question=question,
            context="",
        )
        system_prompt_tokens: int = _num_tokens(system_prompt)
        max_body_tokens: int = self.max_prompt_tokens - system_prompt_tokens

        prompts: list[str] = []
        buffer_parts: list[str] = []
        buffer_tokens: int = 0

        for part in context:
            if not part:
                continue

            part_tokens: int = _num_tokens(part)

            if part_tokens > max_body_tokens:
                prompts.append(
                    self._apply_instruction(
                        instruction=instruction,
                        question=question,
                        context=part,
                    ),
                )
                continue

            if buffer_tokens + part_tokens <= max_body_tokens:
                buffer_parts.append(part)
                buffer_tokens += part_tokens
            else:
                if buffer_parts:
                    prompts.append(
                        self._apply_instruction(
                            instruction=instruction,
                            question=question,
                            context=context_seperator.join(buffer_parts),
                        ),
                    )
                buffer_parts = [part]
                buffer_tokens = part_tokens

        if buffer_parts:
            prompts.append(
                self._apply_instruction(
                    instruction=instruction,
                    question=question,
                    context=context_seperator.join(buffer_parts),
                ),
            )

        return prompts

    def build(
        self,
        question: str,
        context: str | Iterable[str],
        *,
        instruction: str = INSTRUCTION,
    ) -> list[str]:
        if isinstance(context, str):
            context = (context,)
        return self._build_prompts(
            instruction=instruction,
            question=question,
            context=context,
        )
