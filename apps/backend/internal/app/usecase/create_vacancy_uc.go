package usecase

import (
	"context"
	"errors"

	"ai-job-assistant/backend/internal/app/dto"
	ucerrs "ai-job-assistant/backend/internal/app/errs"
	"ai-job-assistant/backend/internal/app/mapper"
	"ai-job-assistant/backend/internal/domain/port"
	pkgerrs "ai-job-assistant/backend/pkg/errs"
)

type CreateVacancyUC struct {
	vacancy port.VacancyRepository
}

func NewCreateVacancyUC(vacancy port.VacancyRepository) *CreateVacancyUC {
	return &CreateVacancyUC{vacancy: vacancy}
}

func (uc *CreateVacancyUC) Execute(ctx context.Context, in dto.CreateVacancyInput) (*dto.CreateVacancyOutput, error) {
	vacancy, err := mapper.ToVacancyDomain(in)
	if err != nil {
		return nil, ucerrs.Wrap(ucerrs.ErrInvalidInput, err)
	}

	err = uc.vacancy.Create(ctx, vacancy)
	if err != nil {
		if errors.Is(err, pkgerrs.ErrObjectAlreadyExists) {
			return nil, ucerrs.ErrVacancyAlreadyExists
		}
		return nil, ucerrs.Wrap(ucerrs.ErrCreateVacancyDB, err)
	}

	return mapper.ToCreateVacancyOutput(vacancy), nil
}
