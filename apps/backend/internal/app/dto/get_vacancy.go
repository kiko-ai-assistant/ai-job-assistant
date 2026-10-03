package dto

import "github.com/google/uuid"

type GetVacancyInput struct {
	ID uuid.UUID
}

type GetVacancyOutput VacancyDTO
