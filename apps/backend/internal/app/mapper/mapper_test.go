package mapper

import (
	"testing"
	"time"

	"ai-job-assistant/backend/internal/app/dto"
	"ai-job-assistant/backend/internal/domain/model"
	"ai-job-assistant/backend/internal/domain/port"
	pkgerrs "ai-job-assistant/backend/pkg/errs"
	pkgutils "ai-job-assistant/backend/pkg/utils"

	"github.com/brianvoe/gofakeit/v7"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
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

func TestToVacancyDomain(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)

	validExtID := gofakeit.UUID()
	validTitle := fakeValidTitle()
	validCompany := fakeValidCompany()
	validDesc := fakeValidDescription()
	validURL := fakeValidURL()

	tests := []struct {
		name        string
		input       dto.CreateVacancyInput
		wantErr     bool
		expectedErr error
	}{
		{
			name: "full valid input with salary and location",
			input: dto.CreateVacancyInput{
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
			},
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name: "valid minimal input with nil optional fields",
			input: dto.CreateVacancyInput{
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
			},
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name: "invalid salary range returns error",
			input: dto.CreateVacancyInput{
				ExternalID: validExtID,
				Source:     "hh",
				Title:      validTitle,
				Company:    pkgutils.VPtr(validCompany),
				Salary: &dto.SalaryDTO{
					From:     pkgutils.VPtr(200000),
					To:       pkgutils.VPtr(100000),
					Currency: pkgutils.VPtr("RUB"),
				},
				Grade:           "middle",
				EmploymentTypes: []string{"remote"},
				Location:        nil,
				Description:     validDesc,
				URL:             validURL,
				PublishedAt:     pubAt,
				ParsedAt:        parsedAt,
			},
			wantErr:     true,
			expectedErr: model.ErrInvalidSalaryRange,
		},
		{
			name: "invalid location city without country returns error",
			input: dto.CreateVacancyInput{
				ExternalID: validExtID,
				Source:     "hh",
				Title:      validTitle,
				Company:    pkgutils.VPtr(validCompany),
				Salary:     nil,
				Grade:      "middle",
				EmploymentTypes: []string{
					"remote",
				},
				Location: &dto.LocationDTO{
					City: pkgutils.VPtr("Moscow"),
				},
				Description: validDesc,
				URL:         validURL,
				PublishedAt: pubAt,
				ParsedAt:    parsedAt,
			},
			wantErr:     true,
			expectedErr: model.ErrCityWithoutCountry,
		},
		{
			name: "invalid vacancy field empty title returns error",
			input: dto.CreateVacancyInput{
				ExternalID:      validExtID,
				Source:          "hh",
				Title:           "",
				Company:         pkgutils.VPtr(validCompany),
				Salary:          nil,
				Grade:           "middle",
				EmploymentTypes: []string{"remote"},
				Location:        nil,
				Description:     validDesc,
				URL:             validURL,
				PublishedAt:     pubAt,
				ParsedAt:        parsedAt,
			},
			wantErr:     true,
			expectedErr: pkgerrs.NewValueRequiredError("title"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			vac, err := ToVacancyDomain(tt.input)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Nil(t, vac)
				if tt.expectedErr != nil {
					assert.Equal(t, tt.expectedErr, err)
				}
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, vac)
				assert.Equal(t, tt.input.ExternalID, vac.ExternalID())
				assert.Equal(t, tt.input.Source, vac.Source().String())
				assert.Equal(t, tt.input.Title, vac.Title())
				assert.Equal(t, tt.input.Company, vac.Company())
				assert.Equal(t, tt.input.Grade, vac.Grade().String())
				assert.Equal(t, tt.input.Description, vac.Description())
				assert.Equal(t, tt.input.URL, vac.URL())
				assert.Equal(t, tt.input.PublishedAt, vac.PublishedAt())
				assert.Equal(t, tt.input.ParsedAt, vac.ParsedAt())

				if tt.input.Salary != nil {
					assert.NotNil(t, vac.Salary())
					assert.Equal(t, tt.input.Salary.Text, vac.Salary().Text())
					assert.Equal(t, tt.input.Salary.From, vac.Salary().From())
					assert.Equal(t, tt.input.Salary.To, vac.Salary().To())
					assert.Equal(t, tt.input.Salary.Currency, vac.Salary().Currency())
				} else {
					assert.Nil(t, vac.Salary())
				}

				if tt.input.Location != nil {
					assert.NotNil(t, vac.Location())
					assert.Equal(t, tt.input.Location.Text, vac.Location().Text())
					assert.Equal(t, tt.input.Location.Country, vac.Location().Country())
					assert.Equal(t, tt.input.Location.City, vac.Location().City())
				} else {
					assert.Nil(t, vac.Location())
				}
			}
		})
	}
}

func TestToCreateVacancyOutput(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)

	salary, err := model.NewSalary(pkgutils.VPtr("100k"), pkgutils.VPtr(100000), pkgutils.VPtr(150000), pkgutils.VPtr("RUB"))
	assert.NoError(t, err)

	location, err := model.NewLocation(pkgutils.VPtr("Moscow"), pkgutils.VPtr("Russia"), pkgutils.VPtr("Moscow"))
	assert.NoError(t, err)

	fullVac, err := model.NewVacancy(
		gofakeit.UUID(), "hh", fakeValidTitle(), pkgutils.VPtr(fakeValidCompany()),
		salary, "middle", []string{"remote", "office"}, location,
		fakeValidDescription(), fakeValidURL(), pubAt, parsedAt,
	)
	assert.NoError(t, err)

	minVac, err := model.NewVacancy(
		gofakeit.UUID(), "mts", fakeValidTitle(), nil,
		nil, "senior", []string{"hybrid"}, nil,
		fakeValidDescription(), fakeValidURL(), pubAt, parsedAt,
	)
	assert.NoError(t, err)

	restoredNilETypesVac := model.RestoreVacancy(
		uuid.New(), gofakeit.UUID(), model.SourceHH, fakeValidTitle(), nil, nil,
		model.GradeMiddle, nil, nil, fakeValidDescription(), fakeValidURL(), pubAt, parsedAt,
	)

	tests := []struct {
		name    string
		vac     *model.Vacancy
		wantNil bool
	}{
		{
			name:    "nil vacancy returns nil",
			vac:     nil,
			wantNil: true,
		},
		{
			name:    "full vacancy mapped completely",
			vac:     fullVac,
			wantNil: false,
		},
		{
			name:    "minimal vacancy mapped with zero dto sub-objects",
			vac:     minVac,
			wantNil: false,
		},
		{
			name:    "vacancy with nil employment types maps to nil slice",
			vac:     restoredNilETypesVac,
			wantNil: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			out := ToCreateVacancyOutput(tt.vac)
			dtoVal := ToVacancyDTO(tt.vac)

			if tt.wantNil {
				assert.Nil(t, out)
				assert.Nil(t, dtoVal)
				return
			}

			assert.NotNil(t, out)
			assert.NotNil(t, dtoVal)
			assert.Equal(t, tt.vac.ID(), out.ID)
			assert.Equal(t, tt.vac.ExternalID(), out.ExternalID)
			assert.Equal(t, tt.vac.Source().String(), out.Source)
			assert.Equal(t, tt.vac.Title(), out.Title)
			assert.Equal(t, tt.vac.Company(), out.Company)
			assert.Equal(t, tt.vac.Grade().String(), out.Grade)
			assert.Equal(t, tt.vac.Description(), out.Description)
			assert.Equal(t, tt.vac.URL(), out.URL)
			assert.Equal(t, tt.vac.PublishedAt(), out.PublishedAt)
			assert.Equal(t, tt.vac.ParsedAt(), out.ParsedAt)

			if tt.vac.Salary() != nil {
				assert.NotNil(t, out.Salary)
				assert.Equal(t, tt.vac.Salary().Text(), out.Salary.Text)
				assert.Equal(t, tt.vac.Salary().From(), out.Salary.From)
				assert.Equal(t, tt.vac.Salary().To(), out.Salary.To)
				assert.Equal(t, tt.vac.Salary().Currency(), out.Salary.Currency)
			} else {
				assert.Nil(t, out.Salary)
			}

			if tt.vac.Location() != nil {
				assert.NotNil(t, out.Location)
				assert.Equal(t, tt.vac.Location().Text(), out.Location.Text)
				assert.Equal(t, tt.vac.Location().Country(), out.Location.Country)
				assert.Equal(t, tt.vac.Location().City(), out.Location.City)
			} else {
				assert.Nil(t, out.Location)
			}

			if tt.vac.EmploymentTypes() != nil {
				assert.Len(t, out.EmploymentTypes, len(tt.vac.EmploymentTypes()))
				for i, et := range tt.vac.EmploymentTypes() {
					assert.Equal(t, et.String(), out.EmploymentTypes[i])
				}
			} else {
				assert.Nil(t, out.EmploymentTypes)
			}
		})
	}
}

func TestVacancyDTOToDomain(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)

	validExtID := gofakeit.UUID()
	validTitle := fakeValidTitle()
	validCompany := fakeValidCompany()
	validDesc := fakeValidDescription()
	validURL := fakeValidURL()

	tests := []struct {
		name        string
		input       dto.VacancyDTO
		wantErr     bool
		expectedErr error
	}{
		{
			name: "full valid VacancyDTO with salary and location",
			input: dto.VacancyDTO{
				ID:         uuid.New(),
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
			},
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name: "minimal valid VacancyDTO with empty salary and location",
			input: dto.VacancyDTO{
				ID:              uuid.New(),
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
			},
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name: "invalid salary range returns error",
			input: dto.VacancyDTO{
				ExternalID: validExtID,
				Source:     "hh",
				Title:      validTitle,
				Company:    pkgutils.VPtr(validCompany),
				Salary: &dto.SalaryDTO{
					From:     pkgutils.VPtr(200000),
					To:       pkgutils.VPtr(100000),
					Currency: pkgutils.VPtr("RUB"),
				},
				Grade:           "middle",
				EmploymentTypes: []string{"remote"},
				Description:     validDesc,
				URL:             validURL,
				PublishedAt:     pubAt,
				ParsedAt:        parsedAt,
			},
			wantErr:     true,
			expectedErr: model.ErrInvalidSalaryRange,
		},
		{
			name: "invalid location city without country returns error",
			input: dto.VacancyDTO{
				ExternalID: validExtID,
				Source:     "hh",
				Title:      validTitle,
				Company:    pkgutils.VPtr(validCompany),
				Salary:     nil,
				Grade:      "middle",
				EmploymentTypes: []string{
					"remote",
				},
				Location: &dto.LocationDTO{
					City: pkgutils.VPtr("Moscow"),
				},
				Description: validDesc,
				URL:         validURL,
				PublishedAt: pubAt,
				ParsedAt:    parsedAt,
			},
			wantErr:     true,
			expectedErr: model.ErrCityWithoutCountry,
		},
		{
			name: "invalid vacancy field empty title returns error",
			input: dto.VacancyDTO{
				ExternalID:      validExtID,
				Source:          "hh",
				Title:           "",
				Company:         pkgutils.VPtr(validCompany),
				Salary:          nil,
				Grade:           "middle",
				EmploymentTypes: []string{"remote"},
				Description:     validDesc,
				URL:             validURL,
				PublishedAt:     pubAt,
				ParsedAt:        parsedAt,
			},
			wantErr:     true,
			expectedErr: pkgerrs.NewValueRequiredError("title"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			vac, err := VacancyDTOToDomain(tt.input)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Nil(t, vac)
				if tt.expectedErr != nil {
					assert.Equal(t, tt.expectedErr, err)
				}
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, vac)
				assert.Equal(t, tt.input.ExternalID, vac.ExternalID())
				assert.Equal(t, tt.input.Source, vac.Source().String())
				assert.Equal(t, tt.input.Title, vac.Title())
				assert.Equal(t, tt.input.Company, vac.Company())
				assert.Equal(t, tt.input.Grade, vac.Grade().String())
				assert.Equal(t, tt.input.Description, vac.Description())
				assert.Equal(t, tt.input.URL, vac.URL())
				assert.Equal(t, tt.input.PublishedAt, vac.PublishedAt())
				assert.Equal(t, tt.input.ParsedAt, vac.ParsedAt())
			}
		})
	}
}

func TestToVacanciesDomain(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)

	validDTO1 := dto.VacancyDTO{
		ExternalID:      gofakeit.UUID(),
		Source:          "hh",
		Title:           fakeValidTitle(),
		Grade:           "junior",
		EmploymentTypes: []string{"remote"},
		Description:     fakeValidDescription(),
		URL:             fakeValidURL(),
		PublishedAt:     pubAt,
		ParsedAt:        parsedAt,
	}

	validDTO2 := dto.VacancyDTO{
		ExternalID:      gofakeit.UUID(),
		Source:          "ozon",
		Title:           fakeValidTitle(),
		Grade:           "middle",
		EmploymentTypes: []string{"office"},
		Description:     fakeValidDescription(),
		URL:             fakeValidURL(),
		PublishedAt:     pubAt,
		ParsedAt:        parsedAt,
	}

	invalidDTO := dto.VacancyDTO{
		ExternalID:      "",
		Source:          "hh",
		Title:           fakeValidTitle(),
		Grade:           "junior",
		EmploymentTypes: []string{"remote"},
		Description:     fakeValidDescription(),
		URL:             fakeValidURL(),
		PublishedAt:     pubAt,
		ParsedAt:        parsedAt,
	}

	tests := []struct {
		name        string
		items       []dto.VacancyDTO
		wantNil     bool
		wantLen     int
		wantErr     bool
		expectedErr error
	}{
		{
			name:    "nil slice returns nil",
			items:   nil,
			wantNil: true,
			wantLen: 0,
			wantErr: false,
		},
		{
			name:    "empty slice returns empty slice",
			items:   []dto.VacancyDTO{},
			wantNil: false,
			wantLen: 0,
			wantErr: false,
		},
		{
			name:    "multiple valid items converted successfully",
			items:   []dto.VacancyDTO{validDTO1, validDTO2},
			wantNil: false,
			wantLen: 2,
			wantErr: false,
		},
		{
			name:        "one invalid item in slice returns error",
			items:       []dto.VacancyDTO{validDTO1, invalidDTO},
			wantNil:     true,
			wantLen:     0,
			wantErr:     true,
			expectedErr: pkgerrs.NewValueRequiredError("external_id"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			res, err := ToVacanciesDomain(tt.items)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Nil(t, res)
				if tt.expectedErr != nil {
					assert.Equal(t, tt.expectedErr, err)
				}
			} else {
				assert.NoError(t, err)
				if tt.wantNil {
					assert.Nil(t, res)
				} else {
					assert.NotNil(t, res)
					assert.Len(t, res, tt.wantLen)
				}
			}
		})
	}
}

func TestToInsertVacanciesOutput(t *testing.T) {
	tests := []struct {
		name         string
		res          port.CreateManyResult
		wantInserted int
		wantIgnored  int
	}{
		{
			name: "all inserted zero ignored",
			res: port.CreateManyResult{
				Inserted: 10,
				Ignored:  0,
			},
			wantInserted: 10,
			wantIgnored:  0,
		},
		{
			name: "some inserted some ignored",
			res: port.CreateManyResult{
				Inserted: 7,
				Ignored:  3,
			},
			wantInserted: 7,
			wantIgnored:  3,
		},
		{
			name: "zero inserted all ignored",
			res: port.CreateManyResult{
				Inserted: 0,
				Ignored:  5,
			},
			wantInserted: 0,
			wantIgnored:  5,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			out := ToInsertVacanciesOutput(tt.res)
			assert.NotNil(t, out)
			assert.Equal(t, tt.wantInserted, out.Inserted)
			assert.Equal(t, tt.wantIgnored, out.Ignored)
		})
	}
}

func TestToGetVacancyOutput(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)

	salary, err := model.NewSalary(pkgutils.VPtr("100k"), pkgutils.VPtr(100000), pkgutils.VPtr(150000), pkgutils.VPtr("RUB"))
	assert.NoError(t, err)

	location, err := model.NewLocation(pkgutils.VPtr("Moscow"), pkgutils.VPtr("Russia"), pkgutils.VPtr("Moscow"))
	assert.NoError(t, err)

	fullVac, err := model.NewVacancy(
		gofakeit.UUID(), "hh", fakeValidTitle(), pkgutils.VPtr(fakeValidCompany()),
		salary, "middle", []string{"remote", "office"}, location,
		fakeValidDescription(), fakeValidURL(), pubAt, parsedAt,
	)
	assert.NoError(t, err)

	minVac, err := model.NewVacancy(
		gofakeit.UUID(), "mts", fakeValidTitle(), nil,
		nil, "senior", []string{"hybrid"}, nil,
		fakeValidDescription(), fakeValidURL(), pubAt, parsedAt,
	)
	assert.NoError(t, err)

	tests := []struct {
		name    string
		vac     *model.Vacancy
		wantNil bool
	}{
		{
			name:    "nil vacancy returns nil",
			vac:     nil,
			wantNil: true,
		},
		{
			name:    "full vacancy mapped to get vacancy output",
			vac:     fullVac,
			wantNil: false,
		},
		{
			name:    "minimal vacancy mapped to get vacancy output",
			vac:     minVac,
			wantNil: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			out := ToGetVacancyOutput(tt.vac)
			if tt.wantNil {
				assert.Nil(t, out)
				return
			}

			assert.NotNil(t, out)
			assert.Equal(t, tt.vac.ID(), out.ID)
			assert.Equal(t, tt.vac.ExternalID(), out.ExternalID)
			assert.Equal(t, tt.vac.Source().String(), out.Source)
			assert.Equal(t, tt.vac.Title(), out.Title)
			assert.Equal(t, tt.vac.Company(), out.Company)
			assert.Equal(t, tt.vac.Grade().String(), out.Grade)
			assert.Equal(t, tt.vac.Description(), out.Description)
			assert.Equal(t, tt.vac.URL(), out.URL)
			assert.Equal(t, tt.vac.PublishedAt(), out.PublishedAt)
			assert.Equal(t, tt.vac.ParsedAt(), out.ParsedAt)

			if tt.vac.Salary() != nil {
				assert.NotNil(t, out.Salary)
				assert.Equal(t, tt.vac.Salary().Text(), out.Salary.Text)
				assert.Equal(t, tt.vac.Salary().From(), out.Salary.From)
				assert.Equal(t, tt.vac.Salary().To(), out.Salary.To)
				assert.Equal(t, tt.vac.Salary().Currency(), out.Salary.Currency)
			} else {
				assert.Nil(t, out.Salary)
			}

			if tt.vac.Location() != nil {
				assert.NotNil(t, out.Location)
				assert.Equal(t, tt.vac.Location().Text(), out.Location.Text)
				assert.Equal(t, tt.vac.Location().Country(), out.Location.Country)
				assert.Equal(t, tt.vac.Location().City(), out.Location.City)
			} else {
				assert.Nil(t, out.Location)
			}
		})
	}
}


