package mapper

import (
	"errors"
	"net/http"

	httpdto "ai-job-assistant/backend/internal/adapter/in/http/dto"
	appdto "ai-job-assistant/backend/internal/app/dto"
	ucerrs "ai-job-assistant/backend/internal/app/errs"
	pkgerrs "ai-job-assistant/backend/pkg/errs"

	"github.com/google/uuid"
)

func toSalaryAppDTO(s *httpdto.SalaryDTO) *appdto.SalaryDTO {
	if s == nil {
		return nil
	}
	return &appdto.SalaryDTO{
		Text:     s.Text,
		From:     s.From,
		To:       s.To,
		Currency: s.Currency,
	}
}

func toSalaryHTTPDTO(s *appdto.SalaryDTO) *httpdto.SalaryDTO {
	if s == nil {
		return nil
	}
	return &httpdto.SalaryDTO{
		Text:     s.Text,
		From:     s.From,
		To:       s.To,
		Currency: s.Currency,
	}
}

func toLocationAppDTO(l *httpdto.LocationDTO) *appdto.LocationDTO {
	if l == nil {
		return nil
	}
	return &appdto.LocationDTO{
		Text:    l.Text,
		Country: l.Country,
		City:    l.City,
	}
}

func toLocationHTTPDTO(l *appdto.LocationDTO) *httpdto.LocationDTO {
	if l == nil {
		return nil
	}
	return &httpdto.LocationDTO{
		Text:    l.Text,
		Country: l.Country,
		City:    l.City,
	}
}

func toVacancyAppDTO(v httpdto.VacancyRequest) appdto.VacancyDTO {
	return appdto.VacancyDTO{
		ExternalID:      v.ExternalID,
		Source:          v.Source,
		Title:           v.Title,
		Company:         v.Company,
		Salary:          toSalaryAppDTO(v.Salary),
		Grade:           v.Grade,
		EmploymentTypes: v.EmploymentTypes,
		Location:        toLocationAppDTO(v.Location),
		Description:     v.Description,
		URL:             v.URL,
		PublishedAt:     v.PublishedAt,
		ParsedAt:        v.ParsedAt,
	}
}

func toVacancyResponse(v *appdto.VacancyDTO) httpdto.VacancyResponse {
	if v == nil {
		return httpdto.VacancyResponse{}
	}
	return httpdto.VacancyResponse{
		ID:              v.ID.String(),
		ExternalID:      v.ExternalID,
		Source:          v.Source,
		Title:           v.Title,
		Company:         v.Company,
		Salary:          toSalaryHTTPDTO(v.Salary),
		Grade:           v.Grade,
		EmploymentTypes: v.EmploymentTypes,
		Location:        toLocationHTTPDTO(v.Location),
		Description:     v.Description,
		URL:             v.URL,
		PublishedAt:     v.PublishedAt,
		ParsedAt:        v.ParsedAt,
	}
}

func MapRequestToCreateVacancy(req httpdto.CreateVacancyRequest) appdto.CreateVacancyInput {
	return appdto.CreateVacancyInput{
		ExternalID:      req.ExternalID,
		Source:          req.Source,
		Title:           req.Title,
		Company:         req.Company,
		Salary:          toSalaryAppDTO(req.Salary),
		Grade:           req.Grade,
		EmploymentTypes: req.EmploymentTypes,
		Location:        toLocationAppDTO(req.Location),
		Description:     req.Description,
		URL:             req.URL,
		PublishedAt:     req.PublishedAt,
		ParsedAt:        req.ParsedAt,
	}
}

func MapOutputToCreateVacancy(out *appdto.CreateVacancyOutput) httpdto.CreateVacancyResponse {
	if out == nil {
		return httpdto.CreateVacancyResponse{}
	}
	vac := appdto.VacancyDTO(*out)
	return httpdto.CreateVacancyResponse(toVacancyResponse(&vac))
}

func MapRequestToInsertVacancies(req httpdto.InsertVacanciesRequest) appdto.InsertVacanciesInput {
	if req.Vacancies == nil {
		return appdto.InsertVacanciesInput{}
	}

	vacancies := make([]appdto.VacancyDTO, len(req.Vacancies))
	for i, v := range req.Vacancies {
		vacancies[i] = toVacancyAppDTO(v)
	}

	return appdto.InsertVacanciesInput{
		Vacancies: vacancies,
	}
}

func MapOutputToInsertVacancies(out *appdto.InsertVacanciesOutput) httpdto.InsertVacanciesResponse {
	if out == nil {
		return httpdto.InsertVacanciesResponse{}
	}
	return httpdto.InsertVacanciesResponse{
		Inserted: out.Inserted,
		Ignored:  out.Ignored,
	}
}

func MapRequestToGetVacancy(req httpdto.GetVacancyRequest) appdto.GetVacancyInput {
	id, _ := uuid.Parse(req.ID)
	return appdto.GetVacancyInput{
		ID: id,
	}
}

func MapOutputToGetVacancy(out *appdto.GetVacancyOutput) httpdto.GetVacancyResponse {
	if out == nil {
		return httpdto.GetVacancyResponse{}
	}
	vac := appdto.VacancyDTO(*out)
	return httpdto.GetVacancyResponse(toVacancyResponse(&vac))
}

func HttpError(err error) *pkgerrs.OutErr {
	if err == nil {
		return nil
	}

	var notFound *pkgerrs.ObjectNotFoundError
	var alreadyExists *pkgerrs.ObjectAlreadyExistsError
	var valRequired *pkgerrs.ValueRequiredError
	var valInvalid *pkgerrs.ValueInvalidError
	var unauth *pkgerrs.NotAuthenticatedError

	switch {
	case errors.Is(err, pkgerrs.ErrInvalidJSON), errors.Is(err, pkgerrs.ErrInvalidIdentifier):
		return pkgerrs.NewOutError(http.StatusBadRequest, err.Error(), err)
	case errors.Is(err, ucerrs.ErrInvalidInput),
		errors.As(err, &valRequired), errors.Is(err, pkgerrs.ErrValueIsRequired),
		errors.As(err, &valInvalid), errors.Is(err, pkgerrs.ErrValueIsInvalid):
		return pkgerrs.NewOutError(http.StatusBadRequest, err.Error(), err)
	case errors.Is(err, ucerrs.ErrVacancyNotFound),
		errors.As(err, &notFound), errors.Is(err, pkgerrs.ErrObjectNotFound):
		return pkgerrs.NewOutError(http.StatusNotFound, err.Error(), err)
	case errors.Is(err, ucerrs.ErrVacancyAlreadyExists),
		errors.As(err, &alreadyExists), errors.Is(err, pkgerrs.ErrObjectAlreadyExists):
		return pkgerrs.NewOutError(http.StatusConflict, err.Error(), err)
	case errors.As(err, &unauth), errors.Is(err, pkgerrs.ErrNotAuthenticated):
		return pkgerrs.NewOutError(http.StatusUnauthorized, err.Error(), err)
	default:
		return pkgerrs.NewOutError(http.StatusInternalServerError, "internal server error", err)
	}
}

func MapErrorToResponse(msg string) httpdto.ErrorResponse {
	return httpdto.ErrorResponse{
		Error: msg,
	}
}
