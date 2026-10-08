package mapper

import (
	httpdto "ai-job-assistant/backend/internal/adapter/in/http/dto"
	"errors"
	"net/http"

	ucerrs "ai-job-assistant/backend/internal/app/errs"
	pkgerrs "ai-job-assistant/backend/pkg/errs"
)

func MapErrorToResponse(msg string) httpdto.ErrorResponse {
	return httpdto.ErrorResponse{
		Error: msg,
	}
}

func HttpError(err error) *pkgerrs.OutErr {
	if err == nil {
		return nil
	}

	switch {
	case errors.Is(err, pkgerrs.ErrInvalidJSON),
		errors.Is(err, pkgerrs.ErrInvalidIdentifier),
		errors.Is(err, pkgerrs.ErrValueIsInvalid):
		return pkgerrs.NewOutError(
			http.StatusBadRequest,
			err.Error(),
			err,
		)
	}

	var w *ucerrs.WrappedError
	if errors.As(err, &w) {
		switch {
		case errors.Is(err, ucerrs.ErrCreateVacancyDB),
			errors.Is(err, ucerrs.ErrCreateManyVacanciesDB),
			errors.Is(err, ucerrs.ErrGetVacancyDB),
			errors.Is(err, ucerrs.ErrListVacanciesDB):
			return pkgerrs.NewOutError(
				http.StatusInternalServerError,
				w.Public.Error(),
				w.Reason,
			)

		case errors.Is(err, ucerrs.ErrInvalidInput):
			return pkgerrs.NewOutError(
				http.StatusBadRequest,
				w.Public.Error()+": "+w.Reason.Error(),
				w.Reason,
			)

		default:
			return pkgerrs.NewOutError(
				http.StatusInternalServerError,
				"internal error",
				w.Reason,
			)
		}
	}

	switch {
	case errors.Is(err, ucerrs.ErrVacancyNotFound):
		return pkgerrs.NewOutError(
			http.StatusNotFound,
			err.Error(),
			nil,
		)

	case errors.Is(err, ucerrs.ErrVacancyAlreadyExists):
		return pkgerrs.NewOutError(
			http.StatusConflict,
			err.Error(),
			nil,
		)
	}

	return pkgerrs.NewOutError(
		http.StatusInternalServerError,
		"internal error",
		nil,
	)
}
