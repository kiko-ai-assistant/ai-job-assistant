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

func NewItemHandler(
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
	var req httpdto.CreateItemRequest

	if err := c.Bind(&req); err != nil {
		return h.returnErr(c, "binding failed", pkgerrs.ErrInvalidJSON)
	}

	out, err := h.createItemUC.Execute(
		c.Request().Context(),
		mapper.MapRequestToCreateItem(req),
	)
	if err != nil {
		return h.returnErr(c, "failed to create item", err)
	}

	h.log.InfoContext(
		c.Request().Context(), "vacancy created",
		slog.Any("name", req.Name),
		slog.Any("description", req.Description),
		slog.Any("category", req.Category),
		slog.Any("photo_url", req.PhotoURL),
		slog.Any("nutrition", req.Nutrition),
	)

	return c.JSON(http.StatusCreated, mapper.MapOutputToCreateItem(out))
}

func (h *VacancyHandler) Get(c echo.Context) error {
	var req httpdto.GetItemRequest

	err := c.Bind(&req)
	if err != nil {
		return h.returnErr(c, "binding failed", pkgerrs.ErrInvalidIdentifier)
	}

	if _, err = uuid.Parse(req.ID); err != nil {
		return h.returnErr(c, "failed to parse uuid", pkgerrs.ErrInvalidIdentifier)
	}

	out, err := h.getItemUC.Execute(
		c.Request().Context(),
		mapper.MapRequestToGetItem(req),
	)
	if err != nil {
		return h.returnErr(c, "failed to get item", err)
	}

	return c.JSON(http.StatusOK, mapper.MapOutputToGetItem(out))
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
