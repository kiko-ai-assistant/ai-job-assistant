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
	if in.ID == uuid.Nil {
		return nil, ucerrs.Wrap(ucerrs.ErrInvalidInput, pkgerrs.NewValueRequiredError("id"))
	}

	vacancy, err := uc.vacancy.Get(ctx, in.ID)
	if err != nil {
		if errors.Is(err, pkgerrs.ErrObjectNotFound) {
			return nil, ucerrs.ErrVacancyNotFound
		}
		return nil, ucerrs.Wrap(ucerrs.ErrGetVacancyDB, err)
	}
	return mapper.ToGetVacancyOutput(vacancy), nil
}
