package mapper

import (
	"testing"

	"ai-job-assistant/backend/internal/adapter/out/postgres/sqlc"
	"ai-job-assistant/backend/internal/domain/model"
	pkgutils "ai-job-assistant/backend/pkg/utils"

	"github.com/brianvoe/gofakeit/v7"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/stretchr/testify/assert"
)

func TestToSQLCCreate(t *testing.T) {
	fullID := uuid.New()
	fullExtID := gofakeit.UUID()
	fullTitle := gofakeit.ProductName()
	fullCompany := gofakeit.Company()
	fullSalaryText := gofakeit.ProductDescription()
	fullSalaryFrom := gofakeit.IntRange(50000, 100000)
	fullSalaryTo := gofakeit.IntRange(100001, 200000)
	fullSalaryCur := gofakeit.CurrencyShort()
	fullLocText := gofakeit.ProductDescription()
	fullCountry := gofakeit.Country()
	fullCity := gofakeit.City()
	fullDesc := gofakeit.ProductDescription()
	fullURL := gofakeit.URL()
	fullPubAt := gofakeit.Date()
	fullParsedAt := gofakeit.Date()

	fullSalary := model.RestoreSalary(
		pkgutils.VPtr(fullSalaryText),
		pkgutils.VPtr(fullSalaryFrom),
		pkgutils.VPtr(fullSalaryTo),
		pkgutils.VPtr(fullSalaryCur),
	)
	fullLoc := model.RestoreLocation(
		pkgutils.VPtr(fullLocText),
		pkgutils.VPtr(fullCountry),
		pkgutils.VPtr(fullCity),
	)
	fullVacancy := model.RestoreVacancy(
		fullID,
		fullExtID,
		model.SourceHH,
		fullTitle,
		pkgutils.VPtr(fullCompany),
		fullSalary,
		model.GradeJunior,
		[]model.EmploymentType{model.EmploymentRemote, model.EmploymentOffice},
		fullLoc,
		fullDesc,
		fullURL,
		fullPubAt,
		fullParsedAt,
	)

	minID := uuid.New()
	minExtID := gofakeit.UUID()
	minTitle := gofakeit.ProductName()
	minDesc := gofakeit.ProductDescription()
	minURL := gofakeit.URL()
	minPubAt := gofakeit.Date()
	minParsedAt := gofakeit.Date()
	minVacancy := model.RestoreVacancy(
		minID,
		minExtID,
		model.SourceTelegram,
		minTitle,
		nil,
		nil,
		model.GradeSenior,
		nil,
		nil,
		minDesc,
		minURL,
		minPubAt,
		minParsedAt,
	)

	partialSalaryText := gofakeit.ProductDescription()
	partialCity := gofakeit.City()
	partialSalary := model.RestoreSalary(pkgutils.VPtr(partialSalaryText), nil, nil, nil)
	partialLoc := model.RestoreLocation(nil, nil, pkgutils.VPtr(partialCity))
	partialVacancy := model.RestoreVacancy(
		uuid.New(),
		gofakeit.UUID(),
		model.SourceOzon,
		gofakeit.ProductName(),
		nil,
		partialSalary,
		model.GradeMiddle,
		[]model.EmploymentType{model.EmploymentHybrid},
		partialLoc,
		gofakeit.ProductDescription(),
		gofakeit.URL(),
		gofakeit.Date(),
		gofakeit.Date(),
	)

	tests := []struct {
		name    string
		vacancy *model.Vacancy
		want    sqlc.CreateVacancyParams
	}{
		{
			name:    "nil vacancy returns empty params",
			vacancy: nil,
			want:    sqlc.CreateVacancyParams{},
		},
		{
			name:    "full vacancy maps all fields",
			vacancy: fullVacancy,
			want: sqlc.CreateVacancyParams{
				ID:         fullID,
				ExternalID: fullExtID,
				Source:     model.SourceHH.String(),
				Title:      fullTitle,
				Company:    pgtype.Text{String: fullCompany, Valid: true},
				SalaryText: pgtype.Text{String: fullSalaryText, Valid: true},
				SalaryFrom: pgtype.Int4{Int32: int32(fullSalaryFrom), Valid: true},
				SalaryTo:   pgtype.Int4{Int32: int32(fullSalaryTo), Valid: true},
				Currency:   pgtype.Text{String: fullSalaryCur, Valid: true},
				Grade:      sqlc.Grade(model.GradeJunior),
				EmploymentTypes: []sqlc.EmploymentType{
					sqlc.EmploymentType(model.EmploymentRemote),
					sqlc.EmploymentType(model.EmploymentOffice),
				},
				LocationText: pgtype.Text{String: fullLocText, Valid: true},
				Country:      pgtype.Text{String: fullCountry, Valid: true},
				City:         pgtype.Text{String: fullCity, Valid: true},
				Description:  fullDesc,
				Url:          fullURL,
				PublishedAt:  fullPubAt,
				ParsedAt:     fullParsedAt,
			},
		},
		{
			name:    "minimal vacancy maps required fields with empty optional fields",
			vacancy: minVacancy,
			want: sqlc.CreateVacancyParams{
				ID:              minID,
				ExternalID:      minExtID,
				Source:          model.SourceTelegram.String(),
				Title:           minTitle,
				Company:         pgtype.Text{},
				SalaryText:      pgtype.Text{},
				SalaryFrom:      pgtype.Int4{},
				SalaryTo:        pgtype.Int4{},
				Currency:        pgtype.Text{},
				Grade:           sqlc.Grade(model.GradeSenior),
				EmploymentTypes: []sqlc.EmploymentType{},
				LocationText:    pgtype.Text{},
				Country:         pgtype.Text{},
				City:            pgtype.Text{},
				Description:     minDesc,
				Url:             minURL,
				PublishedAt:     minPubAt,
				ParsedAt:        minParsedAt,
			},
		},
		{
			name:    "partial vacancy maps specified optional fields",
			vacancy: partialVacancy,
			want: sqlc.CreateVacancyParams{
				ID:              partialVacancy.ID(),
				ExternalID:      partialVacancy.ExternalID(),
				Source:          partialVacancy.Source().String(),
				Title:           partialVacancy.Title(),
				Company:         pgtype.Text{},
				SalaryText:      pgtype.Text{String: partialSalaryText, Valid: true},
				SalaryFrom:      pgtype.Int4{},
				SalaryTo:        pgtype.Int4{},
				Currency:        pgtype.Text{},
				Grade:           sqlc.Grade(partialVacancy.Grade()),
				EmploymentTypes: []sqlc.EmploymentType{sqlc.EmploymentType(model.EmploymentHybrid)},
				LocationText:    pgtype.Text{},
				Country:         pgtype.Text{},
				City:            pgtype.Text{String: partialCity, Valid: true},
				Description:     partialVacancy.Description(),
				Url:             partialVacancy.URL(),
				PublishedAt:     partialVacancy.PublishedAt(),
				ParsedAt:        partialVacancy.ParsedAt(),
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ToSQLCCreate(tt.vacancy)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestToSQLCCreateMany(t *testing.T) {
	vID := uuid.New()
	vExtID := gofakeit.UUID()
	vTitle := gofakeit.ProductName()
	vDesc := gofakeit.ProductDescription()
	vURL := gofakeit.URL()
	vPubAt := gofakeit.Date()
	vParsedAt := gofakeit.Date()
	v := model.RestoreVacancy(
		vID,
		vExtID,
		model.SourceMTS,
		vTitle,
		nil,
		nil,
		model.GradeLead,
		[]model.EmploymentType{model.EmploymentContract},
		nil,
		vDesc,
		vURL,
		vPubAt,
		vParsedAt,
	)

	expectedParam := sqlc.CreateManyVacanciesParams{
		ID:              vID,
		ExternalID:      vExtID,
		Source:          model.SourceMTS.String(),
		Title:           vTitle,
		Company:         pgtype.Text{},
		SalaryText:      pgtype.Text{},
		SalaryFrom:      pgtype.Int4{},
		SalaryTo:        pgtype.Int4{},
		Currency:        pgtype.Text{},
		Grade:           sqlc.Grade(model.GradeLead),
		EmploymentTypes: []sqlc.EmploymentType{sqlc.EmploymentType(model.EmploymentContract)},
		LocationText:    pgtype.Text{},
		Country:         pgtype.Text{},
		City:            pgtype.Text{},
		Description:     vDesc,
		Url:             vURL,
		PublishedAt:     vPubAt,
		ParsedAt:        vParsedAt,
	}

	tests := []struct {
		name      string
		vacancies []*model.Vacancy
		want      []sqlc.CreateManyVacanciesParams
	}{
		{
			name:      "nil vacancies returns nil",
			vacancies: nil,
			want:      nil,
		},
		{
			name:      "empty vacancies returns empty slice",
			vacancies: []*model.Vacancy{},
			want:      []sqlc.CreateManyVacanciesParams{},
		},
		{
			name:      "valid slice with vacancies and nil item maps correctly",
			vacancies: []*model.Vacancy{v, nil},
			want: []sqlc.CreateManyVacanciesParams{
				expectedParam,
				{},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ToSQLCCreateMany(tt.vacancies)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestToDomainVacancy(t *testing.T) {
	fullID := uuid.New()
	fullExtID := gofakeit.UUID()
	fullTitle := gofakeit.ProductName()
	fullCompany := gofakeit.Company()
	fullSalaryText := gofakeit.ProductDescription()
	fullSalaryFrom := int32(gofakeit.IntRange(50000, 100000))
	fullSalaryTo := int32(gofakeit.IntRange(100001, 200000))
	fullSalaryCur := gofakeit.CurrencyShort()
	fullLocText := gofakeit.ProductDescription()
	fullCountry := gofakeit.Country()
	fullCity := gofakeit.City()
	fullDesc := gofakeit.ProductDescription()
	fullURL := gofakeit.URL()
	fullPubAt := gofakeit.Date()
	fullParsedAt := gofakeit.Date()

	rawFull := sqlc.Vacancy{
		ID:              fullID,
		ExternalID:      fullExtID,
		Source:          "HH",
		Title:           fullTitle,
		Company:         pgtype.Text{String: fullCompany, Valid: true},
		SalaryText:      pgtype.Text{String: fullSalaryText, Valid: true},
		SalaryFrom:      pgtype.Int4{Int32: fullSalaryFrom, Valid: true},
		SalaryTo:        pgtype.Int4{Int32: fullSalaryTo, Valid: true},
		Currency:        pgtype.Text{String: fullSalaryCur, Valid: true},
		Grade:           sqlc.GradeJUNIOR,
		EmploymentTypes: []sqlc.EmploymentType{sqlc.EmploymentTypeREMOTE, sqlc.EmploymentTypeOFFICE},
		LocationText:    pgtype.Text{String: fullLocText, Valid: true},
		Country:         pgtype.Text{String: fullCountry, Valid: true},
		City:            pgtype.Text{String: fullCity, Valid: true},
		Description:     fullDesc,
		Url:             fullURL,
		PublishedAt:     fullPubAt,
		ParsedAt:        fullParsedAt,
	}

	expectedFullSalary := model.RestoreSalary(
		pkgutils.VPtr(fullSalaryText),
		pkgutils.VPtr(int(fullSalaryFrom)),
		pkgutils.VPtr(int(fullSalaryTo)),
		pkgutils.VPtr(fullSalaryCur),
	)
	expectedFullLoc := model.RestoreLocation(
		pkgutils.VPtr(fullLocText),
		pkgutils.VPtr(fullCountry),
		pkgutils.VPtr(fullCity),
	)
	expectedFullVacancy := model.RestoreVacancy(
		fullID,
		fullExtID,
		model.SourceHH,
		fullTitle,
		pkgutils.VPtr(fullCompany),
		expectedFullSalary,
		model.GradeJunior,
		[]model.EmploymentType{model.EmploymentRemote, model.EmploymentOffice},
		expectedFullLoc,
		fullDesc,
		fullURL,
		fullPubAt,
		fullParsedAt,
	)

	minID := uuid.New()
	minExtID := gofakeit.UUID()
	minTitle := gofakeit.ProductName()
	minDesc := gofakeit.ProductDescription()
	minURL := gofakeit.URL()
	minPubAt := gofakeit.Date()
	minParsedAt := gofakeit.Date()

	rawMin := sqlc.Vacancy{
		ID:              minID,
		ExternalID:      minExtID,
		Source:          "TELEGRAM",
		Title:           minTitle,
		Company:         pgtype.Text{Valid: false},
		SalaryText:      pgtype.Text{Valid: false},
		SalaryFrom:      pgtype.Int4{Valid: false},
		SalaryTo:        pgtype.Int4{Valid: false},
		Currency:        pgtype.Text{Valid: false},
		Grade:           sqlc.GradeSENIOR,
		EmploymentTypes: nil,
		LocationText:    pgtype.Text{Valid: false},
		Country:         pgtype.Text{Valid: false},
		City:            pgtype.Text{Valid: false},
		Description:     minDesc,
		Url:             minURL,
		PublishedAt:     minPubAt,
		ParsedAt:        minParsedAt,
	}

	expectedMinVacancy := model.RestoreVacancy(
		minID,
		minExtID,
		model.SourceTelegram,
		minTitle,
		nil,
		nil,
		model.GradeSenior,
		[]model.EmploymentType{},
		nil,
		minDesc,
		minURL,
		minPubAt,
		minParsedAt,
	)

	partialID := uuid.New()
	partialExtID := gofakeit.UUID()
	partialTitle := gofakeit.ProductName()
	partialSalaryText := gofakeit.ProductDescription()
	partialCity := gofakeit.City()
	partialDesc := gofakeit.ProductDescription()
	partialURL := gofakeit.URL()
	partialPubAt := gofakeit.Date()
	partialParsedAt := gofakeit.Date()

	rawPartial := sqlc.Vacancy{
		ID:              partialID,
		ExternalID:      partialExtID,
		Source:          "ozon",
		Title:           partialTitle,
		Company:         pgtype.Text{Valid: false},
		SalaryText:      pgtype.Text{String: partialSalaryText, Valid: true},
		SalaryFrom:      pgtype.Int4{Valid: false},
		SalaryTo:        pgtype.Int4{Valid: false},
		Currency:        pgtype.Text{Valid: false},
		Grade:           sqlc.GradeMIDDLE,
		EmploymentTypes: []sqlc.EmploymentType{sqlc.EmploymentTypeHYBRID},
		LocationText:    pgtype.Text{Valid: false},
		Country:         pgtype.Text{Valid: false},
		City:            pgtype.Text{String: partialCity, Valid: true},
		Description:     partialDesc,
		Url:             partialURL,
		PublishedAt:     partialPubAt,
		ParsedAt:        partialParsedAt,
	}

	expectedPartialSalary := model.RestoreSalary(pkgutils.VPtr(partialSalaryText), nil, nil, nil)
	expectedPartialLoc := model.RestoreLocation(nil, nil, pkgutils.VPtr(partialCity))
	expectedPartialVacancy := model.RestoreVacancy(
		partialID,
		partialExtID,
		model.SourceOzon,
		partialTitle,
		nil,
		expectedPartialSalary,
		model.GradeMiddle,
		[]model.EmploymentType{model.EmploymentHybrid},
		expectedPartialLoc,
		partialDesc,
		partialURL,
		partialPubAt,
		partialParsedAt,
	)

	tests := []struct {
		name string
		raw  sqlc.Vacancy
		want *model.Vacancy
	}{
		{
			name: "full raw vacancy maps to domain model",
			raw:  rawFull,
			want: expectedFullVacancy,
		},
		{
			name: "minimal raw vacancy maps to domain model",
			raw:  rawMin,
			want: expectedMinVacancy,
		},
		{
			name: "partial raw vacancy maps to domain model",
			raw:  rawPartial,
			want: expectedPartialVacancy,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ToDomainVacancy(tt.raw)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestToDomainVacancies(t *testing.T) {
	id1 := uuid.New()
	raw1 := sqlc.Vacancy{
		ID:              id1,
		ExternalID:      gofakeit.UUID(),
		Source:          "HH",
		Title:           gofakeit.ProductName(),
		Company:         pgtype.Text{Valid: false},
		SalaryText:      pgtype.Text{Valid: false},
		SalaryFrom:      pgtype.Int4{Valid: false},
		SalaryTo:        pgtype.Int4{Valid: false},
		Currency:        pgtype.Text{Valid: false},
		Grade:           sqlc.GradeLEAD,
		EmploymentTypes: []sqlc.EmploymentType{sqlc.EmploymentTypeCONTRACT},
		LocationText:    pgtype.Text{Valid: false},
		Country:         pgtype.Text{Valid: false},
		City:            pgtype.Text{Valid: false},
		Description:     gofakeit.ProductDescription(),
		Url:             gofakeit.URL(),
		PublishedAt:     gofakeit.Date(),
		ParsedAt:        gofakeit.Date(),
	}

	id2 := uuid.New()
	raw2 := sqlc.Vacancy{
		ID:              id2,
		ExternalID:      gofakeit.UUID(),
		Source:          "telegram",
		Title:           gofakeit.ProductName(),
		Company:         pgtype.Text{Valid: false},
		SalaryText:      pgtype.Text{Valid: false},
		SalaryFrom:      pgtype.Int4{Valid: false},
		SalaryTo:        pgtype.Int4{Valid: false},
		Currency:        pgtype.Text{Valid: false},
		Grade:           sqlc.GradeINTERN,
		EmploymentTypes: nil,
		LocationText:    pgtype.Text{Valid: false},
		Country:         pgtype.Text{Valid: false},
		City:            pgtype.Text{Valid: false},
		Description:     gofakeit.ProductDescription(),
		Url:             gofakeit.URL(),
		PublishedAt:     gofakeit.Date(),
		ParsedAt:        gofakeit.Date(),
	}

	want1 := ToDomainVacancy(raw1)
	want2 := ToDomainVacancy(raw2)

	tests := []struct {
		name    string
		rawList []sqlc.Vacancy
		want    []*model.Vacancy
	}{
		{
			name:    "nil rawList returns nil",
			rawList: nil,
			want:    nil,
		},
		{
			name:    "empty rawList returns empty slice",
			rawList: []sqlc.Vacancy{},
			want:    []*model.Vacancy{},
		},
		{
			name:    "multiple raw vacancies maps all items",
			rawList: []sqlc.Vacancy{raw1, raw2},
			want:    []*model.Vacancy{want1, want2},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ToDomainVacancies(tt.rawList)
			assert.Equal(t, tt.want, got)
		})
	}
}
