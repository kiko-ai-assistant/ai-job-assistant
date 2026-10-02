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
	vacancies, err := mapper.ToVacanciesDomain(in.Vacancies)
	if err != nil {
		return nil, ucerrs.Wrap(ucerrs.ErrInvalidInput, err)
	}

	res, err := uc.vacancy.CreateMany(ctx, vacancies)
	if err != nil {
		return nil, ucerrs.Wrap(ucerrs.ErrCreateManyVacanciesDB, err)
	}

	return mapper.ToInsertVacanciesOutput(res), nil
}
