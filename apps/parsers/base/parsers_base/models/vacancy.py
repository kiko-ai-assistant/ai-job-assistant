from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class SalaryDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str | None = None
    from_: int | None = Field(default=None, alias="from")
    to: int | None = None
    currency: str | None = None
    gross: bool | None = None


class LocationDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str | None = None
    country: str | None = None
    city: str | None = None


class CreateVacancyRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    external_id: str
    source: str
    title: str
    company: str | None = None
    salary: SalaryDTO | None = None
    grade: str
    employment_types: list[str] = Field(default_factory=list)
    location: LocationDTO | None = None
    description: str
    url: str
    published_at: datetime
    parsed_at: datetime
    raw_text: str | None = None


class BatchCreateVacanciesRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    vacancies: list[CreateVacancyRequest] = Field(
        default_factory=list,
        validation_alias=AliasChoices("vacancies", "items"),
    )


class BatchCreateVacanciesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    inserted: int
    ignored: int


BatchIngestVacanciesResponse = BatchCreateVacanciesResponse
