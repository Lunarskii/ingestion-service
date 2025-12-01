from typing import Any
import os
import yaml
import re

from pydantic import ValidationError

from app.domain.classifier.repositories import TopicRepository
from app.domain.classifier.schemas import (
    Topic,
    TopicDTO,
    Rule,
)
from app.domain.database.dependencies import async_scoped_session_ctx
from app.core import logger


def load_rules_from_yaml(rules_path: str) -> list[Rule]:
    """
    Загружает набор правил из файла ``rules_path`` и возвращает их как список схем ``Rule``.

    :param rules_path: Путь к файлу .yml с правилами по каждой теме.
    """

    if not os.path.isfile(rules_path):
        message: str = (
            "Неверный путь к правилам топиков. Определите новый и попробуйте еще раз"
        )
        logger.error(message, rules_path=rules_path)
        raise ValueError(message)

    with open(rules_path, "r") as file:
        text: str = file.read()
    data: list[Any] = yaml.safe_load(text)
    rules: list[Rule] = []

    for item in data:
        topic: str = item.get("topic") or item.get("code") or item.get("slug")
        if not topic:
            continue
        rules.append(
            Rule(
                topic=topic,
                keywords=[
                    str(keyword).strip().lower() for keyword in item.get("keywords", [])
                ],
                regex=[
                    re.compile(
                        pattern=regex,
                        flags=re.IGNORECASE,
                    )
                    for regex in item.get("regex", [])
                ],
                negative_keyword=[
                    str(keyword).strip().lower()
                    for keyword in item.get("negative_keywords", [])
                ],
                weight=float(item.get("weight", 1.0)),
                body_weight=float(item.get("body_weight", 1.0)),
                min_score=float(item.get("min_score", 1.0)),
            ),
        )

    return rules


def load_topics_from_yaml(topics_path: str) -> list[Topic]:
    """
    Загружает набор тем из файла ``topics_path`` и возвращает их как список схем ``Topic``.

    :param topics_path: Путь к файлу .yml с темами.
    """

    if not os.path.isfile(topics_path):
        message: str = "Неверный путь к топикам. Определите новый и попробуйте еще раз"
        logger.error(message, topics_path=topics_path)
        raise ValueError(message)

    with open(topics_path, "r") as file:
        text: str = file.read()
    data: list[Any] = yaml.safe_load(text)
    topics: list[Topic] = []

    for item in data:
        try:
            topics.append(
                Topic(
                    code=item.get("code"),
                    title=item.get("title"),
                    description=item.get("description"),
                ),
            )
        except ValidationError as e:
            logger.warning(
                "В топике отсутствуют одно или несколько требуемых полей",
                topics_path=topics_path,
                error_message=str(e),
            )

    return topics


async def sync_topics_with_db(topics_path: str) -> None:
    """
    Синхронизирует темы из файла ``topics_path`` с темами из БД таблицы ``topics``.
    Синхронизация изменяет только таблицу в базе данных, исходный файл не затрагивается.
    """

    context_logger = logger.bind(topics_path=topics_path)

    if not os.path.isfile(topics_path):
        context_logger.warning(
            "Невозможно синхронизировать topics.yml с БД: неверный путь к топикам",
        )
        return

    pending_topics: list[Topic] = load_topics_from_yaml(topics_path)
    pending_codes: set[str] = set()

    for pending_topic in pending_topics:
        if pending_topic.code in pending_codes:
            context_logger.warning(
                f"Найден дублирующийся код в topics.yml: {pending_topic.code}",
                topic_code=pending_topic.code,
            )
        else:
            pending_codes.add(pending_topic.code)

    async with async_scoped_session_ctx() as session:
        topic_repo = TopicRepository(session)
        db_topics: list[TopicDTO] = await topic_repo.get_n()

        db_map: dict[str, TopicDTO] = {topic.code: topic for topic in db_topics}
        pending_map: dict[str, Topic] = {topic.code: topic for topic in pending_topics}

        for code, pending_topic in pending_map.items():
            db_topic: TopicDTO | None = db_map.get(code)

            if db_topic is None:
                context_logger.info(
                    "Синхронизация топиков: Добавлен новый топик",
                    topic_code=pending_topic.code,
                )
                await topic_repo.create(**pending_topic.model_dump())
                continue
            if not db_topic.is_active:
                context_logger.info(
                    "Синхронизация топиков: Активация/обновление топика",
                    topic_code=db_topic.code,
                )
                await topic_repo.update(
                    id=db_topic.id,
                    **pending_topic.model_dump(),
                )
                continue

            db_topic_dict = db_topic.model_dump(include={"title", "description"})
            pending_topic_dict = pending_topic.model_dump(
                include={"title", "description"}
            )
            if db_topic_dict != pending_topic_dict:
                context_logger.info(
                    "Синхронизация топиков: Обновление метаданных топика",
                    topic_code=db_topic.code,
                )
                await topic_repo.update(
                    id=db_topic.id,
                    **pending_topic.model_dump(),
                )

        for db_topic in db_topics:
            if db_topic.is_active and db_topic.code not in pending_codes:
                context_logger.info(
                    "Синхронизация топиков: Деактивация топика",
                    topic_code=db_topic.code,
                )
                await topic_repo.update(
                    id=db_topic.id,
                    is_active=False,
                )
