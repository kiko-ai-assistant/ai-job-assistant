package dto

type GetVacancyRequest struct {
	ID string `param:"id"`
}

type GetVacancyResponse VacancyResponse
