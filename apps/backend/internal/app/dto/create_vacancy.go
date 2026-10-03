package dto

import "time"

type CreateVacancyInput struct {
	ExternalID      string
	Source          string
	Title           string
	Company         *string
	Salary          *SalaryDTO
	Grade           string
	EmploymentTypes []string
	Location        *LocationDTO
	Description     string
	URL             string
	PublishedAt     time.Time
	ParsedAt        time.Time
}

type CreateVacancyOutput VacancyDTO
