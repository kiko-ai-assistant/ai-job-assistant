package dto

import (
	"time"

	"github.com/google/uuid"
)

type SalaryDTO struct {
	Text     *string
	From     *int
	To       *int
	Currency *string
}

type LocationDTO struct {
	Text    *string
	Country *string
	City    *string
}

type VacancyDTO struct {
	ID              uuid.UUID
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
