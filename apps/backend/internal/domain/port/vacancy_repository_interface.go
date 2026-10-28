package port

import (
	"ai-job-assistant/backend/internal/domain/model"
	"context"

	"github.com/google/uuid"
)

type CreateManyResult struct {
	Inserted int
	Ignored  int
}

type ListVacanciesQuery struct {
}

type VacancyRepository interface {
	Create(ctx context.Context, vacancy *model.Vacancy) error
	CreateMany(ctx context.Context, vacancies []*model.Vacancy) (CreateManyResult, error)
	Get(ctx context.Context, id uuid.UUID) (*model.Vacancy, error)
	List(ctx context.Context, query ListVacanciesQuery) ([]*model.Vacancy, error)
}
