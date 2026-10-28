package http

import (
	"net/http"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
)

type Router struct {
	Vacancy *VacancyHandler
}

func NewRouter(vacancy *VacancyHandler) *Router {
	return &Router{
		Vacancy: vacancy,
	}
}

func (r *Router) InitRoutes() *echo.Echo {
	router := echo.New()

	// TODO: Switch it to the editable list of ips (config)
	router.Use(middleware.CORSWithConfig(middleware.CORSConfig{
		AllowOrigins: []string{"*"},
		AllowMethods: []string{http.MethodGet, http.MethodPut, http.MethodPatch, http.MethodPost, http.MethodDelete, http.MethodOptions},
		AllowHeaders: []string{echo.HeaderOrigin, echo.HeaderContentType, echo.HeaderAccept, echo.HeaderAuthorization, "X-API-Key"},
	}))

	router.Use(middleware.Recover())
	router.Use(middleware.RequestLogger())

	// --- HEALTH CHECK ---
	router.GET("/health", func(c echo.Context) error {
		return c.JSON(http.StatusOK, map[string]string{"status": "ok"})
	})

	// --- SWAGGER ---
	// TODO: Add swagger
	//router.File("/swagger/doc.json", "api/openapi.yaml")

	//router.GET("/swagger", func(c echo.Context) error {
	//	return c.Redirect(http.StatusMovedPermanently, "/swagger/index.html")
	//})
	//
	//router.GET("/swagger/*", echoSwagger.WrapHandler)

	// --- API V1 ---
	v1 := router.Group("/api/v1")
	{
		// --- VACANCIES ---
		vacancies := v1.Group("/vacancies")
		{
			vacancies.POST("", r.Vacancy.Create)
			vacancies.POST("/batch", r.Vacancy.Insert)
			vacancies.GET("/:id", r.Vacancy.Get)
		}
	}

	return router
}
