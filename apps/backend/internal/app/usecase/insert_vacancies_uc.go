package usecase

import (
	"context"

	"ai-job-assistant/backend/internal/app/dto"
	ucerrs "ai-job-assistant/backend/internal/app/errs"
	"ai-job-assistant/backend/internal/app/mapper"
	"ai-job-assistant/backend/internal/domain/port"
)

type InsertVacanciesUC struct {
	vacancy port.VacancyRepository
}

func NewInsertVacanciesUC(vacancy port.VacancyRepository) *InsertVacanciesUC {
	return &InsertVacanciesUC{vacancy: vacancy}
}

func (uc *InsertVacanciesUC) Execute(ctx context.Context, in dto.InsertVacanciesInput) (*dto.InsertVacanciesOutput, error) {
	if len(in.Vacancies) == 0 {
		return &dto.InsertVacanciesOutput{}, nil
	}

	// Create vacancies rich-models
	vacancies, err := mapper.ToVacanciesDomain(in.Vacancies)
	if err != nil {
		return nil, ucerrs.Wrap(ucerrs.ErrInvalidInput, err)
	}

	// Save them in database
	res, err := uc.vacancy.CreateMany(ctx, vacancies)
	if err != nil {
		return nil, ucerrs.Wrap(ucerrs.ErrCreateManyVacanciesDB, err)
	}

	// Output
	return mapper.ToInsertVacanciesOutput(res), nil
}
