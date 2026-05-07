from pydantic import BaseModel


class EventReportRequest(BaseModel):
    operator: str | None = None
    remark: str | None = None


class DesensitizePreviewRequest(BaseModel):
    content: str | None = None
    text: str | None = None

    def normalized_content(self) -> str:
        return (self.content or self.text or "").strip()
