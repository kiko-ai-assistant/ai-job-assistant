package postgres

import (
	"context"
	"errors"

	"ai-job-assistant/backend/internal/adapter/out/postgres/mapper"
	"ai-job-assistant/backend/internal/domain/model"
	"ai-job-assistant/backend/internal/domain/port"
	pkgerrs "ai-job-assistant/backend/pkg/errs"
	pkgpostgres "ai-job-assistant/backend/pkg/postgres"

	trmpgx "github.com/avito-tech/go-transaction-manager/drivers/pgxv5/v2"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
)

var _ port.VacancyRepository = (*VacancyRepository)(nil)

type VacancyRepository struct {
	BaseRepository
}

func NewVacancyRepository(
	pgClient *pkgpostgres.Client,
	getter *trmpgx.CtxGetter,
) *VacancyRepository {
	return &VacancyRepository{
		BaseRepository: NewBaseRepository(pgClient, getter),
	}
}

func (r *VacancyRepository) Create(ctx context.Context, vacancy *model.Vacancy) error {
	params := mapper.ToSQLCCreate(vacancy)
	err := r.q.CreateVacancy(ctx, r.db(ctx), params)
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23505" {
			return pkgerrs.NewObjectAlreadyExistsError("vacancy")
		}
		return err
	}
	return nil
}

func (r *VacancyRepository) CreateMany(ctx context.Context, vacancies []*model.Vacancy) (port.CreateManyResult, error) {
	if len(vacancies) == 0 {
		return port.CreateManyResult{}, nil
	}

	params := mapper.ToSQLCCreateMany(vacancies)
	results := r.q.CreateManyVacancies(ctx, r.db(ctx), params)

	var res port.CreateManyResult
	var firstErr error

	results.QueryRow(func(i int, id uuid.UUID, err error) {
		if firstErr != nil {
			return
		}
		if err == nil {
			res.Inserted++
		} else if errors.Is(err, pgx.ErrNoRows) {
			res.Ignored++
		} else {
			firstErr = err
		}
	})

	if firstErr != nil {
		return port.CreateManyResult{}, firstErr
	}

	return res, nil
}

func (r *VacancyRepository) Get(ctx context.Context, id uuid.UUID) (*model.Vacancy, error) {
	row, err := r.q.GetVacancy(ctx, r.db(ctx), id)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, pkgerrs.NewObjectNotFoundError("vacancy", id.String())
		}
		return nil, err
	}
	return mapper.ToDomainVacancy(row), nil
}

func (r *VacancyRepository) List(ctx context.Context, query port.ListVacanciesQuery) ([]*model.Vacancy, error) {
	rows, err := r.q.ListVacancies(ctx, r.db(ctx))
	if err != nil {
		return nil, err
	}
	return mapper.ToDomainVacancies(rows), nil
}
