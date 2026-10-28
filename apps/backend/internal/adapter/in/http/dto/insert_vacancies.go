package dto

type InsertVacanciesRequest struct {
	Vacancies []VacancyRequest `json:"vacancies"`
}

type InsertVacanciesResponse struct {
	Inserted int `json:"inserted"`
	Ignored  int `json:"ignored"`
}
