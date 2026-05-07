from pydantic import BaseModel


class EventReportRequest(BaseModel):
    operator: str | None = None
    remark: str | None = None

