package usecase

import (
	"context"
	"errors"

	"ai-job-assistant/backend/internal/app/dto"
	ucerrs "ai-job-assistant/backend/internal/app/errs"
	"ai-job-assistant/backend/internal/app/mapper"
	"ai-job-assistant/backend/internal/domain/port"
	pkgerrs "ai-job-assistant/backend/pkg/errs"

	"github.com/google/uuid"
)

type GetVacancyUC struct {
	vacancy port.VacancyRepository
}

func NewGetVacancyUC(vacancy port.VacancyRepository) *GetVacancyUC {
	return &GetVacancyUC{vacancy: vacancy}
}

func (uc *GetVacancyUC) Execute(ctx context.Context, in dto.GetVacancyInput) (*dto.GetVacancyOutput, error) {
	// Premier validation
	if err := uc.validateInput(&in); err != nil {
		return nil, err
	}

	// Get the vacancy
	vacancy, err := uc.vacancy.Get(ctx, in.ID)
	if err != nil {
		if errors.Is(err, pkgerrs.ErrObjectNotFound) {
			return nil, ucerrs.ErrVacancyNotFound
		}
		return nil, ucerrs.Wrap(ucerrs.ErrGetVacancyDB, err)
	}

	// Output
	return mapper.ToGetVacancyOutput(vacancy), nil
}

func (uc *GetVacancyUC) validateInput(in *dto.GetVacancyInput) error {
	if in.ID == uuid.Nil {
		return ucerrs.Wrap(
			ucerrs.ErrInvalidInput,
			pkgerrs.NewValueRequiredError("id"),
		)
	}
	return nil
}
