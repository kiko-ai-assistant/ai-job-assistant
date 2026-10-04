from pydantic import BaseModel, Field


class CreateVacancyRequest(BaseModel):
    external_id: str
    source: str = "Telegram"
    title: str
    url: str
    company: str | None = None
    salary_text: str | None = None
    location: str | None = None
    description: str | None = None


class BatchCreateVacanciesRequest(BaseModel):
    vacancies: list[CreateVacancyRequest] = Field(default_factory=list)


class BatchIngestVacanciesResponse(BaseModel):
    inserted: int
    ignored: int
