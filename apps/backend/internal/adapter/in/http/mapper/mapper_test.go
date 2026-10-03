package mapper

import (
	"errors"
	"net/http"
	"testing"
	"time"

	httpdto "ai-job-assistant/backend/internal/adapter/in/http/dto"
	appdto "ai-job-assistant/backend/internal/app/dto"
	ucerrs "ai-job-assistant/backend/internal/app/errs"
	pkgerrs "ai-job-assistant/backend/pkg/errs"
	pkgutils "ai-job-assistant/backend/pkg/utils"

	"github.com/brianvoe/gofakeit/v7"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func TestMapRequestToCreateVacancy(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)

	validCompany := gofakeit.Company()
	validSalaryText := gofakeit.ProductName()
	validSalaryFrom := int(gofakeit.Uint32())
	validSalaryTo := validSalaryFrom + 50000
	validCurrency := gofakeit.CurrencyShort()
	validLocText := gofakeit.City()
	validCountry := gofakeit.Country()
	validCity := gofakeit.City()

	tests := []struct {
		name     string
		input    httpdto.CreateVacancyRequest
		expected appdto.CreateVacancyInput
	}{
		{
			name: "full request with salary and location",
			input: httpdto.CreateVacancyRequest{
				ExternalID: gofakeit.UUID(),
				Source:     gofakeit.ProductName(),
				Title:      gofakeit.ProductName(),
				Company:    pkgutils.VPtr(validCompany),
				Salary: &httpdto.SalaryDTO{
					Text:     pkgutils.VPtr(validSalaryText),
					From:     pkgutils.VPtr(validSalaryFrom),
					To:       pkgutils.VPtr(validSalaryTo),
					Currency: pkgutils.VPtr(validCurrency),
				},
				Grade:           gofakeit.ProductName(),
				EmploymentTypes: []string{gofakeit.ProductName(), gofakeit.ProductName()},
				Location: &httpdto.LocationDTO{
					Text:    pkgutils.VPtr(validLocText),
					Country: pkgutils.VPtr(validCountry),
					City:    pkgutils.VPtr(validCity),
				},
				Description: gofakeit.ProductDescription(),
				URL:         gofakeit.URL(),
				PublishedAt: pubAt,
				ParsedAt:    parsedAt,
			},
			expected: appdto.CreateVacancyInput{
				Company: pkgutils.VPtr(validCompany),
				Salary: &appdto.SalaryDTO{
					Text:     pkgutils.VPtr(validSalaryText),
					From:     pkgutils.VPtr(validSalaryFrom),
					To:       pkgutils.VPtr(validSalaryTo),
					Currency: pkgutils.VPtr(validCurrency),
				},
				Location: &appdto.LocationDTO{
					Text:    pkgutils.VPtr(validLocText),
					Country: pkgutils.VPtr(validCountry),
					City:    pkgutils.VPtr(validCity),
				},
				PublishedAt: pubAt,
				ParsedAt:    parsedAt,
			},
		},
		{
			name: "minimal request with nil salary, location, company",
			input: httpdto.CreateVacancyRequest{
				ExternalID:      gofakeit.UUID(),
				Source:          gofakeit.ProductName(),
				Title:           gofakeit.ProductName(),
				Company:         nil,
				Salary:          nil,
				Grade:           gofakeit.ProductName(),
				EmploymentTypes: []string{gofakeit.ProductName()},
				Location:        nil,
				Description:     gofakeit.ProductDescription(),
				URL:             gofakeit.URL(),
				PublishedAt:     pubAt,
				ParsedAt:        parsedAt,
			},
			expected: appdto.CreateVacancyInput{
				Company:     nil,
				Salary:      nil,
				Location:    nil,
				PublishedAt: pubAt,
				ParsedAt:    parsedAt,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			res := MapRequestToCreateVacancy(tt.input)

			assert.Equal(t, tt.input.ExternalID, res.ExternalID)
			assert.Equal(t, tt.input.Source, res.Source)
			assert.Equal(t, tt.input.Title, res.Title)
			assert.Equal(t, tt.expected.Company, res.Company)
			assert.Equal(t, tt.expected.Salary, res.Salary)
			assert.Equal(t, tt.input.Grade, res.Grade)
			assert.Equal(t, tt.input.EmploymentTypes, res.EmploymentTypes)
			assert.Equal(t, tt.expected.Location, res.Location)
			assert.Equal(t, tt.input.Description, res.Description)
			assert.Equal(t, tt.input.URL, res.URL)
			assert.Equal(t, tt.expected.PublishedAt, res.PublishedAt)
			assert.Equal(t, tt.expected.ParsedAt, res.ParsedAt)
		})
	}
}

func TestMapOutputToCreateVacancy(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)
	vacUUID := uuid.New()

	validCompany := gofakeit.Company()
	validSalaryText := gofakeit.ProductName()
	validSalaryFrom := int(gofakeit.Uint32())
	validSalaryTo := validSalaryFrom + 50000
	validCurrency := gofakeit.CurrencyShort()
	validLocText := gofakeit.City()
	validCountry := gofakeit.Country()
	validCity := gofakeit.City()

	tests := []struct {
		name     string
		input    *appdto.CreateVacancyOutput
		expected httpdto.CreateVacancyResponse
	}{
		{
			name:     "nil output returns zero response",
			input:    nil,
			expected: httpdto.CreateVacancyResponse{},
		},
		{
			name: "full output with salary and location",
			input: &appdto.CreateVacancyOutput{
				ID:         vacUUID,
				ExternalID: gofakeit.UUID(),
				Source:     gofakeit.ProductName(),
				Title:      gofakeit.ProductName(),
				Company:    pkgutils.VPtr(validCompany),
				Salary: &appdto.SalaryDTO{
					Text:     pkgutils.VPtr(validSalaryText),
					From:     pkgutils.VPtr(validSalaryFrom),
					To:       pkgutils.VPtr(validSalaryTo),
					Currency: pkgutils.VPtr(validCurrency),
				},
				Grade:           gofakeit.ProductName(),
				EmploymentTypes: []string{gofakeit.ProductName()},
				Location: &appdto.LocationDTO{
					Text:    pkgutils.VPtr(validLocText),
					Country: pkgutils.VPtr(validCountry),
					City:    pkgutils.VPtr(validCity),
				},
				Description: gofakeit.ProductDescription(),
				URL:         gofakeit.URL(),
				PublishedAt: pubAt,
				ParsedAt:    parsedAt,
			},
			expected: httpdto.CreateVacancyResponse{
				ID:      vacUUID.String(),
				Company: pkgutils.VPtr(validCompany),
				Salary: &httpdto.SalaryDTO{
					Text:     pkgutils.VPtr(validSalaryText),
					From:     pkgutils.VPtr(validSalaryFrom),
					To:       pkgutils.VPtr(validSalaryTo),
					Currency: pkgutils.VPtr(validCurrency),
				},
				Location: &httpdto.LocationDTO{
					Text:    pkgutils.VPtr(validLocText),
					Country: pkgutils.VPtr(validCountry),
					City:    pkgutils.VPtr(validCity),
				},
				PublishedAt: pubAt,
				ParsedAt:    parsedAt,
			},
		},
		{
			name: "minimal output with nil salary, location, company",
			input: &appdto.CreateVacancyOutput{
				ID:              vacUUID,
				ExternalID:      gofakeit.UUID(),
				Source:          gofakeit.ProductName(),
				Title:           gofakeit.ProductName(),
				Company:         nil,
				Salary:          nil,
				Grade:           gofakeit.ProductName(),
				EmploymentTypes: []string{gofakeit.ProductName()},
				Location:        nil,
				Description:     gofakeit.ProductDescription(),
				URL:             gofakeit.URL(),
				PublishedAt:     pubAt,
				ParsedAt:        parsedAt,
			},
			expected: httpdto.CreateVacancyResponse{
				ID:          vacUUID.String(),
				Company:     nil,
				Salary:      nil,
				Location:    nil,
				PublishedAt: pubAt,
				ParsedAt:    parsedAt,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			res := MapOutputToCreateVacancy(tt.input)

			if tt.input == nil {
				assert.Equal(t, tt.expected, res)
				return
			}

			assert.Equal(t, tt.expected.ID, res.ID)
			assert.Equal(t, tt.input.ExternalID, res.ExternalID)
			assert.Equal(t, tt.input.Source, res.Source)
			assert.Equal(t, tt.input.Title, res.Title)
			assert.Equal(t, tt.expected.Company, res.Company)
			assert.Equal(t, tt.expected.Salary, res.Salary)
			assert.Equal(t, tt.input.Grade, res.Grade)
			assert.Equal(t, tt.input.EmploymentTypes, res.EmploymentTypes)
			assert.Equal(t, tt.expected.Location, res.Location)
			assert.Equal(t, tt.input.Description, res.Description)
			assert.Equal(t, tt.input.URL, res.URL)
			assert.Equal(t, tt.expected.PublishedAt, res.PublishedAt)
			assert.Equal(t, tt.expected.ParsedAt, res.ParsedAt)
		})
	}
}

func TestMapRequestToInsertVacancies(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)

	validCompany := gofakeit.Company()
	validSalaryText := gofakeit.ProductName()
	validSalaryFrom := int(gofakeit.Uint32())
	validSalaryTo := validSalaryFrom + 50000
	validCurrency := gofakeit.CurrencyShort()
	validLocText := gofakeit.City()
	validCountry := gofakeit.Country()
	validCity := gofakeit.City()

	item1 := httpdto.VacancyRequest{
		ExternalID: gofakeit.UUID(),
		Source:     gofakeit.ProductName(),
		Title:      gofakeit.ProductName(),
		Company:    pkgutils.VPtr(validCompany),
		Salary: &httpdto.SalaryDTO{
			Text:     pkgutils.VPtr(validSalaryText),
			From:     pkgutils.VPtr(validSalaryFrom),
			To:       pkgutils.VPtr(validSalaryTo),
			Currency: pkgutils.VPtr(validCurrency),
		},
		Grade:           gofakeit.ProductName(),
		EmploymentTypes: []string{gofakeit.ProductName()},
		Location: &httpdto.LocationDTO{
			Text:    pkgutils.VPtr(validLocText),
			Country: pkgutils.VPtr(validCountry),
			City:    pkgutils.VPtr(validCity),
		},
		Description: gofakeit.ProductDescription(),
		URL:         gofakeit.URL(),
		PublishedAt: pubAt,
		ParsedAt:    parsedAt,
	}

	item2 := httpdto.VacancyRequest{
		ExternalID:      gofakeit.UUID(),
		Source:          gofakeit.ProductName(),
		Title:           gofakeit.ProductName(),
		Company:         nil,
		Salary:          nil,
		Grade:           gofakeit.ProductName(),
		EmploymentTypes: nil,
		Location:        nil,
		Description:     gofakeit.ProductDescription(),
		URL:             gofakeit.URL(),
		PublishedAt:     pubAt,
		ParsedAt:        parsedAt,
	}

	tests := []struct {
		name    string
		input   httpdto.InsertVacanciesRequest
		wantLen int
	}{
		{
			name: "nil vacancies returns empty input",
			input: httpdto.InsertVacanciesRequest{
				Vacancies: nil,
			},
			wantLen: 0,
		},
		{
			name: "empty vacancies returns empty input",
			input: httpdto.InsertVacanciesRequest{
				Vacancies: []httpdto.VacancyRequest{},
			},
			wantLen: 0,
		},
		{
			name: "multiple vacancies mapped properly",
			input: httpdto.InsertVacanciesRequest{
				Vacancies: []httpdto.VacancyRequest{item1, item2},
			},
			wantLen: 2,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			res := MapRequestToInsertVacancies(tt.input)
			assert.Len(t, res.Vacancies, tt.wantLen)

			if tt.wantLen > 0 {
				assert.Equal(t, tt.input.Vacancies[0].ExternalID, res.Vacancies[0].ExternalID)
				assert.Equal(t, tt.input.Vacancies[0].Source, res.Vacancies[0].Source)
				assert.Equal(t, tt.input.Vacancies[0].Title, res.Vacancies[0].Title)
				assert.Equal(t, tt.input.Vacancies[0].Company, res.Vacancies[0].Company)
				assert.NotNil(t, res.Vacancies[0].Salary)
				assert.Equal(t, tt.input.Vacancies[0].Salary.Text, res.Vacancies[0].Salary.Text)
				assert.Equal(t, tt.input.Vacancies[0].Salary.From, res.Vacancies[0].Salary.From)
				assert.Equal(t, tt.input.Vacancies[0].Salary.To, res.Vacancies[0].Salary.To)
				assert.Equal(t, tt.input.Vacancies[0].Salary.Currency, res.Vacancies[0].Salary.Currency)
				assert.NotNil(t, res.Vacancies[0].Location)
				assert.Equal(t, tt.input.Vacancies[0].Location.Text, res.Vacancies[0].Location.Text)
				assert.Equal(t, tt.input.Vacancies[0].Location.Country, res.Vacancies[0].Location.Country)
				assert.Equal(t, tt.input.Vacancies[0].Location.City, res.Vacancies[0].Location.City)

				assert.Equal(t, tt.input.Vacancies[1].ExternalID, res.Vacancies[1].ExternalID)
				assert.Nil(t, res.Vacancies[1].Company)
				assert.Nil(t, res.Vacancies[1].Salary)
				assert.Nil(t, res.Vacancies[1].Location)
			}
		})
	}
}

func TestMapOutputToInsertVacancies(t *testing.T) {
	inserted := int(gofakeit.Uint32())
	ignored := int(gofakeit.Uint32())

	tests := []struct {
		name     string
		input    *appdto.InsertVacanciesOutput
		expected httpdto.InsertVacanciesResponse
	}{
		{
			name:     "nil output returns zero response",
			input:    nil,
			expected: httpdto.InsertVacanciesResponse{},
		},
		{
			name: "valid output mapped properly",
			input: &appdto.InsertVacanciesOutput{
				Inserted: inserted,
				Ignored:  ignored,
			},
			expected: httpdto.InsertVacanciesResponse{
				Inserted: inserted,
				Ignored:  ignored,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			res := MapOutputToInsertVacancies(tt.input)
			assert.Equal(t, tt.expected, res)
		})
	}
}

func TestMapRequestToGetVacancy(t *testing.T) {
	validUUID := uuid.New()

	tests := []struct {
		name     string
		input    httpdto.GetVacancyRequest
		expected appdto.GetVacancyInput
	}{
		{
			name: "valid uuid string mapped properly",
			input: httpdto.GetVacancyRequest{
				ID: validUUID.String(),
			},
			expected: appdto.GetVacancyInput{
				ID: validUUID,
			},
		},
		{
			name: "invalid uuid string maps to uuid.Nil",
			input: httpdto.GetVacancyRequest{
				ID: gofakeit.ProductName(),
			},
			expected: appdto.GetVacancyInput{
				ID: uuid.Nil,
			},
		},
		{
			name: "empty id maps to uuid.Nil",
			input: httpdto.GetVacancyRequest{
				ID: "",
			},
			expected: appdto.GetVacancyInput{
				ID: uuid.Nil,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			res := MapRequestToGetVacancy(tt.input)
			assert.Equal(t, tt.expected, res)
		})
	}
}

func TestMapOutputToGetVacancy(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)
	vacUUID := uuid.New()

	validCompany := gofakeit.Company()
	validSalaryText := gofakeit.ProductName()
	validSalaryFrom := int(gofakeit.Uint32())
	validSalaryTo := validSalaryFrom + 50000
	validCurrency := gofakeit.CurrencyShort()
	validLocText := gofakeit.City()
	validCountry := gofakeit.Country()
	validCity := gofakeit.City()

	tests := []struct {
		name     string
		input    *appdto.GetVacancyOutput
		expected httpdto.GetVacancyResponse
	}{
		{
			name:     "nil output returns zero response",
			input:    nil,
			expected: httpdto.GetVacancyResponse{},
		},
		{
			name: "full output with salary and location",
			input: &appdto.GetVacancyOutput{
				ID:         vacUUID,
				ExternalID: gofakeit.UUID(),
				Source:     gofakeit.ProductName(),
				Title:      gofakeit.ProductName(),
				Company:    pkgutils.VPtr(validCompany),
				Salary: &appdto.SalaryDTO{
					Text:     pkgutils.VPtr(validSalaryText),
					From:     pkgutils.VPtr(validSalaryFrom),
					To:       pkgutils.VPtr(validSalaryTo),
					Currency: pkgutils.VPtr(validCurrency),
				},
				Grade:           gofakeit.ProductName(),
				EmploymentTypes: []string{gofakeit.ProductName()},
				Location: &appdto.LocationDTO{
					Text:    pkgutils.VPtr(validLocText),
					Country: pkgutils.VPtr(validCountry),
					City:    pkgutils.VPtr(validCity),
				},
				Description: gofakeit.ProductDescription(),
				URL:         gofakeit.URL(),
				PublishedAt: pubAt,
				ParsedAt:    parsedAt,
			},
			expected: httpdto.GetVacancyResponse{
				ID:      vacUUID.String(),
				Company: pkgutils.VPtr(validCompany),
				Salary: &httpdto.SalaryDTO{
					Text:     pkgutils.VPtr(validSalaryText),
					From:     pkgutils.VPtr(validSalaryFrom),
					To:       pkgutils.VPtr(validSalaryTo),
					Currency: pkgutils.VPtr(validCurrency),
				},
				Location: &httpdto.LocationDTO{
					Text:    pkgutils.VPtr(validLocText),
					Country: pkgutils.VPtr(validCountry),
					City:    pkgutils.VPtr(validCity),
				},
				PublishedAt: pubAt,
				ParsedAt:    parsedAt,
			},
		},
		{
			name: "minimal output with nil salary, location, company",
			input: &appdto.GetVacancyOutput{
				ID:              vacUUID,
				ExternalID:      gofakeit.UUID(),
				Source:          gofakeit.ProductName(),
				Title:           gofakeit.ProductName(),
				Company:         nil,
				Salary:          nil,
				Grade:           gofakeit.ProductName(),
				EmploymentTypes: []string{gofakeit.ProductName()},
				Location:        nil,
				Description:     gofakeit.ProductDescription(),
				URL:             gofakeit.URL(),
				PublishedAt:     pubAt,
				ParsedAt:        parsedAt,
			},
			expected: httpdto.GetVacancyResponse{
				ID:          vacUUID.String(),
				Company:     nil,
				Salary:      nil,
				Location:    nil,
				PublishedAt: pubAt,
				ParsedAt:    parsedAt,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			res := MapOutputToGetVacancy(tt.input)

			if tt.input == nil {
				assert.Equal(t, tt.expected, res)
				return
			}

			assert.Equal(t, tt.expected.ID, res.ID)
			assert.Equal(t, tt.input.ExternalID, res.ExternalID)
			assert.Equal(t, tt.input.Source, res.Source)
			assert.Equal(t, tt.input.Title, res.Title)
			assert.Equal(t, tt.expected.Company, res.Company)
			assert.Equal(t, tt.expected.Salary, res.Salary)
			assert.Equal(t, tt.input.Grade, res.Grade)
			assert.Equal(t, tt.input.EmploymentTypes, res.EmploymentTypes)
			assert.Equal(t, tt.expected.Location, res.Location)
			assert.Equal(t, tt.input.Description, res.Description)
			assert.Equal(t, tt.input.URL, res.URL)
			assert.Equal(t, tt.expected.PublishedAt, res.PublishedAt)
			assert.Equal(t, tt.expected.ParsedAt, res.ParsedAt)
		})
	}
}

func TestHttpError(t *testing.T) {
	field := gofakeit.ProductName()

	tests := []struct {
		name        string
		err         error
		wantNil     bool
		wantCode    int
		wantMessage string
	}{
		{
			name:    "nil error returns nil",
			err:     nil,
			wantNil: true,
		},
		{
			name:        "invalid json returns 400",
			err:         pkgerrs.ErrInvalidJSON,
			wantNil:     false,
			wantCode:    http.StatusBadRequest,
			wantMessage: "invalid json",
		},
		{
			name:        "invalid identifier returns 400",
			err:         pkgerrs.ErrInvalidIdentifier,
			wantNil:     false,
			wantCode:    http.StatusBadRequest,
			wantMessage: "invalid identifier format",
		},
		{
			name:        "uc invalid input returns 400",
			err:         ucerrs.ErrInvalidInput,
			wantNil:     false,
			wantCode:    http.StatusBadRequest,
			wantMessage: "invalid input",
		},
		{
			name:        "value required error returns 400",
			err:         pkgerrs.NewValueRequiredError(field),
			wantNil:     false,
			wantCode:    http.StatusBadRequest,
			wantMessage: "value is required: " + field,
		},
		{
			name:        "value invalid error returns 400",
			err:         pkgerrs.NewValueInvalidError(field),
			wantNil:     false,
			wantCode:    http.StatusBadRequest,
			wantMessage: "value is invalid: " + field,
		},
		{
			name:        "uc vacancy not found returns 404",
			err:         ucerrs.ErrVacancyNotFound,
			wantNil:     false,
			wantCode:    http.StatusNotFound,
			wantMessage: "vacancy not found",
		},
		{
			name:        "object not found returns 404",
			err:         pkgerrs.NewObjectNotFoundError("vacancy", "id-123"),
			wantNil:     false,
			wantCode:    http.StatusNotFound,
			wantMessage: "object not found: id-123",
		},
		{
			name:        "uc vacancy already exists returns 409",
			err:         ucerrs.ErrVacancyAlreadyExists,
			wantNil:     false,
			wantCode:    http.StatusConflict,
			wantMessage: "vacancy with given external id already exists",
		},
		{
			name:        "object already exists returns 409",
			err:         pkgerrs.NewObjectAlreadyExistsError("vacancy"),
			wantNil:     false,
			wantCode:    http.StatusConflict,
			wantMessage: "object already exists: vacancy",
		},
		{
			name:        "unauthenticated error returns 401",
			err:         pkgerrs.NewNotAuthenticatedErrorWithReason(errors.New("bad token")),
			wantNil:     false,
			wantCode:    http.StatusUnauthorized,
			wantMessage: pkgerrs.ErrNotAuthenticated.Error() + " (reason: bad token)",
		},
		{
			name:        "wrapped uc error unwraps and matches code",
			err:         ucerrs.Wrap(ucerrs.ErrInvalidInput, pkgerrs.NewValueRequiredError("id")),
			wantNil:     false,
			wantCode:    http.StatusBadRequest,
			wantMessage: "invalid input",
		},
		{
			name:        "unknown internal error returns 500",
			err:         errors.New(gofakeit.ProductDescription()),
			wantNil:     false,
			wantCode:    http.StatusInternalServerError,
			wantMessage: "internal server error",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			out := HttpError(tt.err)

			if tt.wantNil {
				assert.Nil(t, out)
				return
			}

			assert.NotNil(t, out)
			assert.Equal(t, tt.wantCode, out.Code)
			assert.Equal(t, tt.wantMessage, out.Message)
			assert.Equal(t, tt.err, out.Reason)
		})
	}
}

func TestMapErrorToResponse(t *testing.T) {
	msg1 := gofakeit.ProductName()
	msg2 := gofakeit.ProductDescription()

	tests := []struct {
		name     string
		msg      string
		expected httpdto.ErrorResponse
	}{
		{
			name: "message 1 mapped properly",
			msg:  msg1,
			expected: httpdto.ErrorResponse{
				Error: msg1,
			},
		},
		{
			name: "message 2 mapped properly",
			msg:  msg2,
			expected: httpdto.ErrorResponse{
				Error: msg2,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			res := MapErrorToResponse(tt.msg)
			assert.Equal(t, tt.expected, res)
		})
	}
}
