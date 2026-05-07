from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    session_id: str | None = Field(default=None, alias="sessionId")
    content: str | None = None
    message: str | None = None

    model_config = {
        "populate_by_name": True,
    }

    def normalized_content(self) -> str:
        return (self.content or self.message or "").strip()

