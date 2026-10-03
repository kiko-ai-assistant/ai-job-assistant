package usecase

import (
	"context"
	"errors"
	"testing"
	"time"

	"ai-job-assistant/backend/internal/app/dto"
	ucerrs "ai-job-assistant/backend/internal/app/errs"
	"ai-job-assistant/backend/internal/domain/model"
	"ai-job-assistant/backend/internal/domain/port"
	"ai-job-assistant/backend/internal/domain/port/mocks"
	pkgutils "ai-job-assistant/backend/pkg/utils"

	"github.com/brianvoe/gofakeit/v7"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

func TestInsertVacanciesUC_Execute(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)

	validDTO1 := dto.VacancyDTO{
		ExternalID: gofakeit.UUID(),
		Source:     "hh",
		Title:      fakeValidTitle(),
		Company:    pkgutils.VPtr(fakeValidCompany()),
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
		Description: fakeValidDescription(),
		URL:         fakeValidURL(),
		PublishedAt: pubAt,
		ParsedAt:    parsedAt,
	}

	validDTO2 := dto.VacancyDTO{
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

	invalidDTO := dto.VacancyDTO{
		ExternalID:      "",
		Source:          "hh",
		Title:           fakeValidTitle(),
		Grade:           "middle",
		EmploymentTypes: []string{"remote"},
		Description:     fakeValidDescription(),
		URL:             fakeValidURL(),
		PublishedAt:     pubAt,
		ParsedAt:        parsedAt,
	}

	dbErr := errors.New("db insert batch failed")

	tests := []struct {
		name        string
		input       dto.InsertVacanciesInput
		mockSetup   func(m *mocks.MockVacancyRepository)
		want        *dto.InsertVacanciesOutput
		wantErr     bool
		expectedErr error
	}{
		{
			name: "successful insertion of multiple vacancies with inserted and ignored counts",
			input: dto.InsertVacanciesInput{
				Vacancies: []dto.VacancyDTO{validDTO1, validDTO2},
			},
			mockSetup: func(m *mocks.MockVacancyRepository) {
				m.EXPECT().CreateMany(mock.Anything, mock.MatchedBy(func(vacs []*model.Vacancy) bool {
					return len(vacs) == 2
				})).Return(port.CreateManyResult{
					Inserted: 1,
					Ignored:  1,
				}, nil).Once()
			},
			want: &dto.InsertVacanciesOutput{
				Inserted: 1,
				Ignored:  1,
			},
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name: "empty vacancies slice handled cleanly",
			input: dto.InsertVacanciesInput{
				Vacancies: []dto.VacancyDTO{},
			},
			mockSetup: func(m *mocks.MockVacancyRepository) {
			},
			want: &dto.InsertVacanciesOutput{
				Inserted: 0,
				Ignored:  0,
			},
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name: "nil vacancies slice handled cleanly",
			input: dto.InsertVacanciesInput{
				Vacancies: nil,
			},
			mockSetup: func(m *mocks.MockVacancyRepository) {
			},
			want: &dto.InsertVacanciesOutput{
				Inserted: 0,
				Ignored:  0,
			},
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name: "domain validation error on input returns ErrInvalidInput without calling repo",
			input: dto.InsertVacanciesInput{
				Vacancies: []dto.VacancyDTO{validDTO1, invalidDTO},
			},
			mockSetup:   func(m *mocks.MockVacancyRepository) {},
			want:        nil,
			wantErr:     true,
			expectedErr: ucerrs.ErrInvalidInput,
		},
		{
			name: "database error returns ErrCreateManyVacanciesDB",
			input: dto.InsertVacanciesInput{
				Vacancies: []dto.VacancyDTO{validDTO1, validDTO2},
			},
			mockSetup: func(m *mocks.MockVacancyRepository) {
				m.EXPECT().CreateMany(mock.Anything, mock.Anything).Return(port.CreateManyResult{}, dbErr).Once()
			},
			want:        nil,
			wantErr:     true,
			expectedErr: ucerrs.ErrCreateManyVacanciesDB,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			repo := mocks.NewMockVacancyRepository(t)
			tt.mockSetup(repo)

			uc := NewInsertVacanciesUC(repo)
			out, err := uc.Execute(context.Background(), tt.input)

			if tt.wantErr {
				assert.Error(t, err)
				assert.Nil(t, out)
				assert.True(t, errors.Is(err, tt.expectedErr))
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.want, out)
			}
		})
	}
}
