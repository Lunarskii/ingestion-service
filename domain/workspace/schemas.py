from datetime import datetime
from typing import Annotated
import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class WorkspaceDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Annotated[str, Field(default_factory=lambda: str(uuid.uuid4()))] # noqa
    name: str
    created_at: Annotated[datetime, Field(default_factory=datetime.now)]
