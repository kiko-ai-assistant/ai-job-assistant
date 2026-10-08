package postgres

import (
	"context"

	"ai-job-assistant/backend/internal/adapter/out/postgres/sqlc"
	pkgpostgres "ai-job-assistant/backend/pkg/postgres"

	trmpgx "github.com/avito-tech/go-transaction-manager/drivers/pgxv5/v2"
	"github.com/jackc/pgx/v5/pgxpool"
)

type BaseRepository struct {
	q      *sqlc.Queries
	pool   *pgxpool.Pool
	getter *trmpgx.CtxGetter
}

func NewBaseRepository(pgClient *pkgpostgres.Client, getter *trmpgx.CtxGetter) BaseRepository {
	return BaseRepository{
		q:      sqlc.New(),
		pool:   pgClient.Pool,
		getter: getter,
	}
}

func (b *BaseRepository) db(ctx context.Context) sqlc.DBTX {
	return b.getter.DefaultTrOrDB(ctx, b.pool)
}
