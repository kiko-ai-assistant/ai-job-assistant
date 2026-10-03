package usecase

import (
	"context"
	"errors"
	"testing"
	"time"

	"ai-job-assistant/backend/internal/app/dto"
	ucerrs "ai-job-assistant/backend/internal/app/errs"
	"ai-job-assistant/backend/internal/domain/model"
	"ai-job-assistant/backend/internal/domain/port/mocks"
	pkgerrs "ai-job-assistant/backend/pkg/errs"
	pkgutils "ai-job-assistant/backend/pkg/utils"

	"github.com/brianvoe/gofakeit/v7"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

func TestGetVacancyUC_Execute(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)

	fullID := uuid.New()
	fullExtID := gofakeit.UUID()
	fullTitle := fakeValidTitle()
	fullCompany := fakeValidCompany()
	fullSalary := model.RestoreSalary(
		pkgutils.VPtr("100k - 150k"),
		pkgutils.VPtr(100000),
		pkgutils.VPtr(150000),
		pkgutils.VPtr("RUB"),
	)
	fullLoc := model.RestoreLocation(
		pkgutils.VPtr("Moscow"),
		pkgutils.VPtr("Russia"),
		pkgutils.VPtr("Moscow"),
	)
	fullVacancy := model.RestoreVacancy(
		fullID,
		fullExtID,
		model.SourceHH,
		fullTitle,
		pkgutils.VPtr(fullCompany),
		fullSalary,
		model.GradeMiddle,
		[]model.EmploymentType{model.EmploymentRemote, model.EmploymentOffice},
		fullLoc,
		fakeValidDescription(),
		fakeValidURL(),
		pubAt,
		parsedAt,
	)

	minID := uuid.New()
	minExtID := gofakeit.UUID()
	minTitle := fakeValidTitle()
	minVacancy := model.RestoreVacancy(
		minID,
		minExtID,
		model.SourceTelegram,
		minTitle,
		nil,
		nil,
		model.GradeSenior,
		[]model.EmploymentType{model.EmploymentHybrid},
		nil,
		fakeValidDescription(),
		fakeValidURL(),
		pubAt,
		parsedAt,
	)

	notFoundID := uuid.New()
	dbErrID := uuid.New()
	dbErr := errors.New("db query failed")

	tests := []struct {
		name        string
		input       dto.GetVacancyInput
		mockSetup   func(m *mocks.MockVacancyRepository)
		want        *dto.GetVacancyOutput
		wantErr     bool
		expectedErr error
	}{
		{
			name:  "successful retrieval of full vacancy",
			input: dto.GetVacancyInput{ID: fullID},
			mockSetup: func(m *mocks.MockVacancyRepository) {
				m.EXPECT().Get(mock.Anything, fullID).Return(fullVacancy, nil).Once()
			},
			want: &dto.GetVacancyOutput{
				ID:         fullID,
				ExternalID: fullExtID,
				Source:     model.SourceHH.String(),
				Title:      fullTitle,
				Company:    pkgutils.VPtr(fullCompany),
				Salary: &dto.SalaryDTO{
					Text:     pkgutils.VPtr("100k - 150k"),
					From:     pkgutils.VPtr(100000),
					To:       pkgutils.VPtr(150000),
					Currency: pkgutils.VPtr("RUB"),
				},
				Grade:           model.GradeMiddle.String(),
				EmploymentTypes: []string{model.EmploymentRemote.String(), model.EmploymentOffice.String()},
				Location: &dto.LocationDTO{
					Text:    pkgutils.VPtr("Moscow"),
					Country: pkgutils.VPtr("Russia"),
					City:    pkgutils.VPtr("Moscow"),
				},
				Description: fullVacancy.Description(),
				URL:         fullVacancy.URL(),
				PublishedAt: pubAt,
				ParsedAt:    parsedAt,
			},
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:  "successful retrieval of minimal vacancy",
			input: dto.GetVacancyInput{ID: minID},
			mockSetup: func(m *mocks.MockVacancyRepository) {
				m.EXPECT().Get(mock.Anything, minID).Return(minVacancy, nil).Once()
			},
			want: &dto.GetVacancyOutput{
				ID:              minID,
				ExternalID:      minExtID,
				Source:          model.SourceTelegram.String(),
				Title:           minTitle,
				Company:         nil,
				Salary:          nil,
				Grade:           model.GradeSenior.String(),
				EmploymentTypes: []string{model.EmploymentHybrid.String()},
				Location:        nil,
				Description:     minVacancy.Description(),
				URL:             minVacancy.URL(),
				PublishedAt:     pubAt,
				ParsedAt:        parsedAt,
			},
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:      "empty id returns ErrInvalidInput without calling repo",
			input:     dto.GetVacancyInput{ID: uuid.Nil},
			mockSetup: func(m *mocks.MockVacancyRepository) {},
			want:      nil,
			wantErr:   true,
			expectedErr: ucerrs.ErrInvalidInput,
		},
		{
			name:  "vacancy not found returns ErrVacancyNotFound",
			input: dto.GetVacancyInput{ID: notFoundID},
			mockSetup: func(m *mocks.MockVacancyRepository) {
				m.EXPECT().Get(mock.Anything, notFoundID).Return(nil, pkgerrs.ErrObjectNotFound).Once()
			},
			want:        nil,
			wantErr:     true,
			expectedErr: ucerrs.ErrVacancyNotFound,
		},
		{
			name:  "database error returns ErrGetVacancyDB",
			input: dto.GetVacancyInput{ID: dbErrID},
			mockSetup: func(m *mocks.MockVacancyRepository) {
				m.EXPECT().Get(mock.Anything, dbErrID).Return(nil, dbErr).Once()
			},
			want:        nil,
			wantErr:     true,
			expectedErr: ucerrs.ErrGetVacancyDB,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			repo := mocks.NewMockVacancyRepository(t)
			tt.mockSetup(repo)

			uc := NewGetVacancyUC(repo)
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
