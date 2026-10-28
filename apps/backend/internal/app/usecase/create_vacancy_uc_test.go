package usecase

import (
	"context"
	"errors"
	"testing"
	"time"

	"ai-job-assistant/backend/internal/app/dto"
	ucerrs "ai-job-assistant/backend/internal/app/errs"
	"ai-job-assistant/backend/internal/domain/port/mocks"
	pkgerrs "ai-job-assistant/backend/pkg/errs"
	pkgutils "ai-job-assistant/backend/pkg/utils"

	"github.com/brianvoe/gofakeit/v7"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

func fakeValidDescription() string {
	desc := gofakeit.ProductDescription()
	for len(desc) < 300 {
		desc += " " + gofakeit.ProductDescription()
	}
	if len(desc) > 2500 {
		desc = desc[:2500]
	}
	return desc
}

func fakeValidTitle() string {
	title := gofakeit.ProductName()
	if len(title) < 3 {
		title = title + " Job"
	}
	if len(title) > 100 {
		title = title[:100]
	}
	return title
}

func fakeValidCompany() string {
	company := gofakeit.Company()
	if len(company) < 2 {
		company = company + " Co"
	}
	if len(company) > 100 {
		company = company[:100]
	}
	return company
}

func fakeValidURL() string {
	url := gofakeit.URL()
	if len(url) < 10 {
		url = "https://example.com/" + url
	}
	if len(url) > 1024 {
		url = url[:1024]
	}
	return url
}

func TestCreateVacancyUC_Execute(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)

	validExtID := gofakeit.UUID()
	validTitle := fakeValidTitle()
	validCompany := fakeValidCompany()
	validDesc := fakeValidDescription()
	validURL := fakeValidURL()

	validFullInput := dto.CreateVacancyInput{
		ExternalID: validExtID,
		Source:     "hh",
		Title:      validTitle,
		Company:    pkgutils.VPtr(validCompany),
		Salary: &dto.SalaryDTO{
			Text:     pkgutils.VPtr("100k - 150k"),
			From:     pkgutils.VPtr(100000),
			To:       pkgutils.VPtr(150000),
			Currency: pkgutils.VPtr("RUB"),
		},
		Grade:           "middle",
		EmploymentTypes: []string{"remote", "office"},
		Location: &dto.LocationDTO{
			Text:    pkgutils.VPtr("Moscow"),
			Country: pkgutils.VPtr("Russia"),
			City:    pkgutils.VPtr("Moscow"),
		},
		Description: validDesc,
		URL:         validURL,
		PublishedAt: pubAt,
		ParsedAt:    parsedAt,
	}

	validMinInput := dto.CreateVacancyInput{
		ExternalID:      gofakeit.UUID(),
		Source:          "telegram",
		Title:           fakeValidTitle(),
		Company:         nil,
		Salary:          nil,
		Grade:           "senior",
		EmploymentTypes: []string{"hybrid"},
		Location:        nil,
		Description:     fakeValidDescription(),
		URL:             fakeValidURL(),
		PublishedAt:     pubAt,
		ParsedAt:        parsedAt,
	}

	invalidInput := dto.CreateVacancyInput{
		ExternalID:      "",
		Source:          "hh",
		Title:           validTitle,
		Company:         pkgutils.VPtr(validCompany),
		Salary:          nil,
		Grade:           "middle",
		EmploymentTypes: []string{"remote"},
		Location:        nil,
		Description:     validDesc,
		URL:             validURL,
		PublishedAt:     pubAt,
		ParsedAt:        parsedAt,
	}

	dbErr := errors.New("database connection failed")

	tests := []struct {
		name        string
		input       dto.CreateVacancyInput
		repoErr     error
		wantErr     bool
		expectedErr error
	}{
		{
			name:        "successful creation with full fields",
			input:       validFullInput,
			repoErr:     nil,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "successful creation with minimal fields",
			input:       validMinInput,
			repoErr:     nil,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "domain validation error on input wrapped as ErrInvalidInput",
			input:       invalidInput,
			repoErr:     nil,
			wantErr:     true,
			expectedErr: ucerrs.ErrInvalidInput,
		},
		{
			name:        "repository returns ErrObjectAlreadyExists returns ErrVacancyAlreadyExists",
			input:       validFullInput,
			repoErr:     pkgerrs.ErrObjectAlreadyExists,
			wantErr:     true,
			expectedErr: ucerrs.ErrVacancyAlreadyExists,
		},
		{
			name:        "repository returns unexpected error wrapped as ErrCreateVacancyDB",
			input:       validFullInput,
			repoErr:     dbErr,
			wantErr:     true,
			expectedErr: ucerrs.ErrCreateVacancyDB,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			repo := mocks.NewMockVacancyRepository(t)
			if !tt.wantErr || tt.repoErr != nil {
				repo.EXPECT().Create(mock.Anything, mock.Anything).Return(tt.repoErr).Once()
			}

			uc := NewCreateVacancyUC(repo)
			out, err := uc.Execute(context.Background(), tt.input)

			if tt.wantErr {
				assert.Error(t, err)
				assert.Nil(t, out)
				assert.True(t, errors.Is(err, tt.expectedErr))
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, out)
				assert.Equal(t, tt.input.ExternalID, out.ExternalID)
				assert.Equal(t, tt.input.Source, out.Source)
				assert.Equal(t, tt.input.Title, out.Title)
				assert.Equal(t, tt.input.Company, out.Company)
				assert.Equal(t, tt.input.Grade, out.Grade)
				assert.Equal(t, tt.input.Description, out.Description)
				assert.Equal(t, tt.input.URL, out.URL)
				assert.Equal(t, tt.input.PublishedAt, out.PublishedAt)
				assert.Equal(t, tt.input.ParsedAt, out.ParsedAt)

				if tt.input.Salary != nil {
					assert.Equal(t, tt.input.Salary, out.Salary)
				} else {
					assert.Nil(t, out.Salary)
				}

				if tt.input.Location != nil {
					assert.Equal(t, tt.input.Location, out.Location)
				} else {
					assert.Nil(t, out.Location)
				}
			}
		})
	}
}
