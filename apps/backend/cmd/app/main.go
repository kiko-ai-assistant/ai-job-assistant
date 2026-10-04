package main

import (
	"ai-job-assistant/backend/cmd/app/config"
	adapterhttp "ai-job-assistant/backend/internal/adapter/in/http"
	adapterpg "ai-job-assistant/backend/internal/adapter/out/postgres"
	"ai-job-assistant/backend/internal/app/usecase"
	pkgpostgres "ai-job-assistant/backend/pkg/postgres"
	"context"
	"errors"
	"fmt"
	"log"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	trmpgx "github.com/avito-tech/go-transaction-manager/drivers/pgxv5/v2"
)

const (
	apiVersion      = "v0.1"
	shutdownTimeout = 10 * time.Second
)

func parseLogLevel(level string) slog.Level {
	switch level {
	case "DEBUG":
		return slog.LevelDebug
	case "INFO":
		return slog.LevelInfo
	case "WARN":
		return slog.LevelWarn
	case "ERROR":
		return slog.LevelError
	default:
		return slog.LevelInfo
	}
}

func newLogger(level string) *slog.Logger {
	logLevel := parseLogLevel(level)
	return slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: logLevel,
	}))
}

func newPostgresClient(ctx context.Context, cfg *config.Config) (*pkgpostgres.Client, error) {
	pgConfig := pkgpostgres.NewConfig(
		cfg.DbHost, cfg.DbPort, cfg.DbUser, cfg.DbPassword,
		cfg.DBName, cfg.DbSSLMode, cfg.DbMaxConn,
		cfg.DbMinConn, cfg.DbMaxConnLifeTime, cfg.DbMaxConnIdleTime,
	)

	pgClient, err := pkgpostgres.NewClient(ctx, pgConfig)
	if err != nil {
		return nil, err
	}

	return pgClient, nil
}

func closePostgresClient(
	ctx context.Context,
	logger *slog.Logger,
	pgClient *pkgpostgres.Client,
) {
	logger.InfoContext(ctx, "closing postgres connection...")
	pgClient.Close()
}

func runServer(ctx context.Context, cfg *config.Config, logger *slog.Logger) error {
	// Postgres client
	pgClient, err := newPostgresClient(ctx, cfg)
	if err != nil {
		return fmt.Errorf("failed to init postgres client: %w", err)
	}

	// Close Postgres
	defer closePostgresClient(ctx, logger, pgClient)

	// Repositories
	vacancyRepo := adapterpg.NewVacancyRepository(pgClient, trmpgx.DefaultCtxGetter)

	// UCs
	createVacancyUC := usecase.NewCreateVacancyUC(vacancyRepo)
	insertVacanciesUC := usecase.NewInsertVacanciesUC(vacancyRepo)
	getVacancyUC := usecase.NewGetVacancyUC(vacancyRepo)

	// Handlers
	vacancyHandler := adapterhttp.NewVacancyHandler(
		logger, createVacancyUC,
		insertVacanciesUC, getVacancyUC,
	)

	// Router
	router := adapterhttp.NewRouter(vacancyHandler).InitRoutes()

	// Launch server with graceful shutdown
	srv := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.HttpPort),
		Handler: router,

		BaseContext: func(_ net.Listener) context.Context {
			return ctx
		},
	}

	errCh := make(chan error, 1)

	go func() {
		logger.InfoContext(ctx, "starting server", slog.String("address", fmt.Sprintf(":%d", cfg.HttpPort)))
		if err = srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			errCh <- err
			return
		}
		errCh <- nil
	}()

	select {
	case <-ctx.Done():
		logger.InfoContext(ctx, "shutdown signal received")
	case err = <-errCh:
		if err != nil {
			logger.ErrorContext(ctx, "server failed", slog.Any("err", err))
			return err
		}
		logger.InfoContext(ctx, "server stopped")
		return nil
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), shutdownTimeout)
	defer cancel()

	if err = srv.Shutdown(shutdownCtx); err != nil {
		logger.ErrorContext(ctx, "graceful shutdown failed", slog.Any("err", err))
		_ = srv.Close() // fallback
		return err
	}

	logger.InfoContext(ctx, "server exited properly")
	return nil
}

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("failed to load config: %v", err)
	}

	logger := newLogger(cfg.LogLevel)

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	if err = runServer(ctx, cfg, logger); err != nil {
		logger.Error(err.Error())
		os.Exit(1)
	}
}
