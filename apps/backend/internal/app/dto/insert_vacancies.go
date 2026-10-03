package dto

type InsertVacanciesInput struct {
	Vacancies []VacancyDTO
}

type InsertVacanciesOutput struct {
	Inserted int
	Ignored  int
}
