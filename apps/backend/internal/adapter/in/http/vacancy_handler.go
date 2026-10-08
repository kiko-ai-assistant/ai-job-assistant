package http

import (
	httpdto "ai-job-assistant/backend/internal/adapter/in/http/dto"
	"ai-job-assistant/backend/internal/adapter/in/http/mapper"
	"ai-job-assistant/backend/internal/app/usecase"
	pkgerrs "ai-job-assistant/backend/pkg/errs"
	"log/slog"
	"net/http"

	"github.com/google/uuid"
	"github.com/labstack/echo/v4"
)

type VacancyHandler struct {
	log               *slog.Logger
	createVacancyUC   *usecase.CreateVacancyUC
	insertVacanciesUC *usecase.InsertVacanciesUC
	getVacancyUC      *usecase.GetVacancyUC
}

func NewVacancyHandler(
	log *slog.Logger,
	createVacancyUC *usecase.CreateVacancyUC,
	insertVacanciesUC *usecase.InsertVacanciesUC,
	getVacancyUC *usecase.GetVacancyUC,
) *VacancyHandler {
	return &VacancyHandler{
		log:               log,
		createVacancyUC:   createVacancyUC,
		insertVacanciesUC: insertVacanciesUC,
		getVacancyUC:      getVacancyUC,
	}
}

func (h *VacancyHandler) Create(c echo.Context) error {
	var req httpdto.CreateVacancyRequest

	if err := c.Bind(&req); err != nil {
		return h.returnErr(c, "binding failed", pkgerrs.ErrInvalidJSON)
	}

	out, err := h.createVacancyUC.Execute(
		c.Request().Context(),
		mapper.MapRequestToCreateVacancy(req),
	)
	if err != nil {
		return h.returnErr(c, "failed to create vacancy", err)
	}

	h.log.InfoContext(
		c.Request().Context(), "vacancy created",
		slog.String("id", out.ID.String()),
		slog.String("external_id", out.ExternalID),
		slog.Any("source", out.Source),
		slog.Any("title", out.Title),
		slog.Any("url", out.URL),
		slog.Any("published_at", out.PublishedAt),
	)

	return c.JSON(http.StatusCreated, mapper.MapOutputToCreateVacancy(out))
}

func (h *VacancyHandler) Insert(c echo.Context) error {
	var req httpdto.InsertVacanciesRequest

	if err := c.Bind(&req); err != nil {
		return h.returnErr(c, "binding failed", pkgerrs.ErrInvalidJSON)
	}

	out, err := h.insertVacanciesUC.Execute(
		c.Request().Context(),
		mapper.MapRequestToInsertVacancies(req),
	)
	if err != nil {
		return h.returnErr(c, "failed to insert vacancies", err)
	}

	h.log.InfoContext(
		c.Request().Context(), "vacancies inserted",
		slog.Int("total", len(req.Vacancies)),
		slog.Int("inserted", out.Inserted),
		slog.Int("ignored", out.Ignored),
	)

	return c.JSON(http.StatusOK, mapper.MapOutputToInsertVacancies(out))
}

func (h *VacancyHandler) Get(c echo.Context) error {
	var req httpdto.GetVacancyRequest

	err := c.Bind(&req)
	if err != nil {
		return h.returnErr(c, "binding failed", pkgerrs.ErrInvalidIdentifier)
	}

	if _, err = uuid.Parse(req.ID); err != nil {
		return h.returnErr(c, "failed to parse uuid", pkgerrs.ErrInvalidIdentifier)
	}

	out, err := h.getVacancyUC.Execute(
		c.Request().Context(),
		mapper.MapRequestToGetVacancy(req),
	)
	if err != nil {
		return h.returnErr(c, "failed to get vacancy", err)
	}

	return c.JSON(http.StatusOK, mapper.MapOutputToGetVacancy(out))
}

func (h *VacancyHandler) returnErr(c echo.Context, msg string, err error) error {
	if err == nil {
		return c.NoContent(http.StatusBadRequest)
	}

	outErr := mapper.HttpError(err)

	h.log.ErrorContext(c.Request().Context(), msg,
		slog.Int("code", outErr.Code),
		slog.String("public_msg", outErr.Message),
		slog.Any("cause", outErr.Reason),
	)

	return c.JSON(outErr.Code, mapper.MapErrorToResponse(outErr.Message))
}
