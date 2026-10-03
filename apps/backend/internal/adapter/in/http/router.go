package http

import (
	"context"
	"log/slog"
	"net/http"
	"os"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
	echoSwagger "github.com/swaggo/echo-swagger"
)

type Router struct {
	Vacancy *VacancyHandler
}

func NewRouter(vacancy *VacancyHandler) *Router {
	return &Router{
		Vacancy: vacancy,
	}
}

func findDocPath(relPath string) string {
	candidates := []string{
		relPath,
		"../../../../" + relPath,
		"../../../" + relPath,
		"../../" + relPath,
		"../" + relPath,
	}
	for _, path := range candidates {
		if _, err := os.Stat(path); err == nil {
			return path
		}
	}
	return relPath
}

func (r *Router) InitRoutes() *echo.Echo {
	router := echo.New()

	router.Use(middleware.CORSWithConfig(middleware.CORSConfig{
		AllowOrigins: []string{"*"},
		AllowMethods: []string{http.MethodGet, http.MethodPut, http.MethodPatch, http.MethodPost, http.MethodDelete, http.MethodOptions},
		AllowHeaders: []string{echo.HeaderOrigin, echo.HeaderContentType, echo.HeaderAccept, echo.HeaderAuthorization, "X-API-Key"},
	}))

	router.Use(middleware.Recover())
	router.Use(middleware.RequestLoggerWithConfig(middleware.RequestLoggerConfig{
		Skipper: func(c echo.Context) bool {
			return c.Path() == "/health" || c.Request().URL.Path == "/health"
		},
		LogLatency:       true,
		LogProtocol:      false,
		LogRemoteIP:      true,
		LogHost:          true,
		LogMethod:        true,
		LogURI:           true,
		LogRequestID:     true,
		LogUserAgent:     true,
		LogStatus:        true,
		LogError:         true,
		LogContentLength: true,
		LogResponseSize:  true,
		HandleError:      true,
		LogValuesFunc: func(c echo.Context, v middleware.RequestLoggerValues) error {
			if v.Error == nil {
				slog.LogAttrs(context.Background(), slog.LevelInfo, "REQUEST",
					slog.String("method", v.Method),
					slog.String("uri", v.URI),
					slog.Int("status", v.Status),
					slog.Duration("latency", v.Latency),
					slog.String("host", v.Host),
					slog.String("bytes_in", v.ContentLength),
					slog.Int64("bytes_out", v.ResponseSize),
					slog.String("user_agent", v.UserAgent),
					slog.String("remote_ip", v.RemoteIP),
					slog.String("request_id", v.RequestID),
				)
			} else {
				slog.LogAttrs(context.Background(), slog.LevelError, "REQUEST_ERROR",
					slog.String("method", v.Method),
					slog.String("uri", v.URI),
					slog.Int("status", v.Status),
					slog.Duration("latency", v.Latency),
					slog.String("host", v.Host),
					slog.String("bytes_in", v.ContentLength),
					slog.Int64("bytes_out", v.ResponseSize),
					slog.String("user_agent", v.UserAgent),
					slog.String("remote_ip", v.RemoteIP),
					slog.String("request_id", v.RequestID),
					slog.String("error", v.Error.Error()),
				)
			}
			return nil
		},
	}))

	// --- HEALTH CHECK ---
	router.GET("/health", func(c echo.Context) error {
		return c.JSON(http.StatusOK, map[string]string{"status": "ok"})
	})

	// --- SWAGGER ---
	publicDocPath := findDocPath("docs/api/openapi-public.yaml")
	partnerDocPath := findDocPath("docs/api/openapi-partner.yaml")

	router.File("/swagger/public/openapi.yaml", publicDocPath)
	router.GET("/swagger/public", func(c echo.Context) error {
		return c.Redirect(http.StatusMovedPermanently, "/swagger/public/index.html")
	})
	router.GET("/swagger/public/", func(c echo.Context) error {
		return c.Redirect(http.StatusMovedPermanently, "/swagger/public/index.html")
	})
	router.GET("/swagger/public/*", echoSwagger.EchoWrapHandler(func(c *echoSwagger.Config) {
		c.URLs = []string{"/swagger/public/openapi.yaml"}
	}))

	router.File("/swagger/partner/openapi.yaml", partnerDocPath)
	router.GET("/swagger/partner", func(c echo.Context) error {
		return c.Redirect(http.StatusMovedPermanently, "/swagger/partner/index.html")
	})
	router.GET("/swagger/partner/", func(c echo.Context) error {
		return c.Redirect(http.StatusMovedPermanently, "/swagger/partner/index.html")
	})
	router.GET("/swagger/partner/*", echoSwagger.EchoWrapHandler(func(c *echoSwagger.Config) {
		c.URLs = []string{"/swagger/partner/openapi.yaml"}
	}))

	router.GET("/swagger", func(c echo.Context) error {
		return c.Redirect(http.StatusMovedPermanently, "/swagger/public/index.html")
	})
	router.GET("/swagger/", func(c echo.Context) error {
		return c.Redirect(http.StatusMovedPermanently, "/swagger/public/index.html")
	})

	// --- PUBLIC API (/api/v1) ---
	v1 := router.Group("/api/v1")
	{
		vacancies := v1.Group("/vacancies")
		{
			vacancies.POST("", r.Vacancy.Create)
			vacancies.POST("/batch", r.Vacancy.Insert)
			vacancies.GET("/:id", r.Vacancy.Get)
		}
	}

	return router
}
