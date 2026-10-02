package model

import (
	pkgerrs "ai-job-assistant/backend/pkg/errs"
	pkgutils "ai-job-assistant/backend/pkg/utils"
	"strings"
	"testing"
	"time"

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

func TestVacancySource_New(t *testing.T) {
	tests := []struct {
		name        string
		raw         string
		wantSource  VacancySource
		wantErr     bool
		expectedErr error
	}{
		{
			name:        "valid hh lowercase",
			raw:         "hh",
			wantSource:  SourceHH,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid telegram lowercase",
			raw:         "telegram",
			wantSource:  SourceTelegram,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid ozon lowercase",
			raw:         "ozon",
			wantSource:  SourceOzon,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid hh uppercase and spaced",
			raw:         "  HH  ",
			wantSource:  SourceHH,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid telegram mixed case",
			raw:         "TeleGram",
			wantSource:  SourceTelegram,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "empty raw",
			raw:         "",
			wantSource:  "",
			wantErr:     true,
			expectedErr: pkgerrs.NewValueRequiredError("source"),
		},
		{
			name:        "spaces only",
			raw:         "   ",
			wantSource:  "",
			wantErr:     true,
			expectedErr: pkgerrs.NewValueRequiredError("source"),
		},
		{
			name:        "invalid source",
			raw:         gofakeit.ProductName(),
			wantSource:  "",
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("source"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := NewVacancySource(tt.raw)
			if tt.wantErr {
				assert.Error(t, err)
				if tt.expectedErr != nil {
					assert.Equal(t, tt.expectedErr, err)
				}
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.wantSource, got)
				assert.Equal(t, string(tt.wantSource), got.String())
				assert.True(t, got.IsValid())
			}
		})
	}

	assert.False(t, VacancySource(gofakeit.ProductName()).IsValid())
}

func TestGrade_New(t *testing.T) {
	tests := []struct {
		name        string
		raw         string
		wantGrade   Grade
		wantErr     bool
		expectedErr error
	}{
		{
			name:        "valid intern",
			raw:         "intern",
			wantGrade:   GradeIntern,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid junior",
			raw:         "junior",
			wantGrade:   GradeJunior,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid middle uppercase with spaces",
			raw:         "  MIDDLE  ",
			wantGrade:   GradeMiddle,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid senior mixed case",
			raw:         "Senior",
			wantGrade:   GradeSenior,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid lead",
			raw:         "lead",
			wantGrade:   GradeLead,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "empty raw",
			raw:         "",
			wantGrade:   "",
			wantErr:     true,
			expectedErr: pkgerrs.NewValueRequiredError("grade"),
		},
		{
			name:        "spaces only",
			raw:         "   ",
			wantGrade:   "",
			wantErr:     true,
			expectedErr: pkgerrs.NewValueRequiredError("grade"),
		},
		{
			name:        "invalid grade",
			raw:         gofakeit.ProductName(),
			wantGrade:   "",
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("grade"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := NewGrade(tt.raw)
			if tt.wantErr {
				assert.Error(t, err)
				if tt.expectedErr != nil {
					assert.Equal(t, tt.expectedErr, err)
				}
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.wantGrade, got)
				assert.Equal(t, string(tt.wantGrade), got.String())
				assert.True(t, got.IsValid())
			}
		})
	}

	assert.False(t, Grade(gofakeit.ProductName()).IsValid())
}

func TestEmploymentType_New(t *testing.T) {
	tests := []struct {
		name        string
		raw         string
		wantType    EmploymentType
		wantErr     bool
		expectedErr error
	}{
		{
			name:        "valid remote",
			raw:         "remote",
			wantType:    EmploymentRemote,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid office uppercase with spaces",
			raw:         "  OFFICE  ",
			wantType:    EmploymentOffice,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid hybrid",
			raw:         "hybrid",
			wantType:    EmploymentHybrid,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid contract mixed case",
			raw:         "Contract",
			wantType:    EmploymentContract,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "empty raw",
			raw:         "",
			wantType:    "",
			wantErr:     true,
			expectedErr: pkgerrs.NewValueRequiredError("employment_type"),
		},
		{
			name:        "spaces only",
			raw:         "   ",
			wantType:    "",
			wantErr:     true,
			expectedErr: pkgerrs.NewValueRequiredError("employment_type"),
		},
		{
			name:        "invalid employment type",
			raw:         gofakeit.ProductName(),
			wantType:    "",
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("employment_type"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := NewEmploymentType(tt.raw)
			if tt.wantErr {
				assert.Error(t, err)
				if tt.expectedErr != nil {
					assert.Equal(t, tt.expectedErr, err)
				}
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.wantType, got)
				assert.Equal(t, string(tt.wantType), got.String())
				assert.True(t, got.IsValid())
			}
		})
	}

	assert.False(t, EmploymentType(gofakeit.ProductName()).IsValid())
}

func TestSalary_New(t *testing.T) {
	validFrom := gofakeit.Number(50000, 100000)
	validTo := validFrom + gofakeit.Number(10000, 50000)
	validCurr := "RUB"
	validText := gofakeit.ProductName()

	shortText := "a"
	longText := strings.Repeat("a", 151)
	invalidLowSalary := -1
	invalidHighSalary := 100000001
	invalidShortCurr := "RU"
	invalidLongCurr := "RUBLE"

	tests := []struct {
		name        string
		text        *string
		from        *int
		to          *int
		currency    *string
		wantErr     bool
		expectedErr error
	}{
		{
			name:        "all nil",
			text:        nil,
			from:        nil,
			to:          nil,
			currency:    nil,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid text only",
			text:        pkgutils.VPtr(validText),
			from:        nil,
			to:          nil,
			currency:    nil,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid full salary",
			text:        pkgutils.VPtr(validText),
			from:        pkgutils.VPtr(validFrom),
			to:          pkgutils.VPtr(validTo),
			currency:    pkgutils.VPtr(validCurr),
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid from only with currency",
			text:        nil,
			from:        pkgutils.VPtr(validFrom),
			to:          nil,
			currency:    pkgutils.VPtr(validCurr),
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid to only with currency",
			text:        nil,
			from:        nil,
			to:          pkgutils.VPtr(validTo),
			currency:    pkgutils.VPtr(validCurr),
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid boundary values",
			text:        nil,
			from:        pkgutils.VPtr(0),
			to:          pkgutils.VPtr(100000000),
			currency:    pkgutils.VPtr("USD"),
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid equal from and to",
			text:        nil,
			from:        pkgutils.VPtr(validFrom),
			to:          pkgutils.VPtr(validFrom),
			currency:    pkgutils.VPtr(validCurr),
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "invalid text short",
			text:        pkgutils.VPtr(shortText),
			from:        nil,
			to:          nil,
			currency:    nil,
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("salary_text"),
		},
		{
			name:        "invalid text long",
			text:        pkgutils.VPtr(longText),
			from:        nil,
			to:          nil,
			currency:    nil,
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("salary_text"),
		},
		{
			name:        "invalid from below min",
			text:        nil,
			from:        pkgutils.VPtr(invalidLowSalary),
			to:          pkgutils.VPtr(validTo),
			currency:    pkgutils.VPtr(validCurr),
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("salary_from"),
		},
		{
			name:        "invalid from above max",
			text:        nil,
			from:        pkgutils.VPtr(invalidHighSalary),
			to:          nil,
			currency:    pkgutils.VPtr(validCurr),
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("salary_from"),
		},
		{
			name:        "invalid to below min",
			text:        nil,
			from:        nil,
			to:          pkgutils.VPtr(invalidLowSalary),
			currency:    pkgutils.VPtr(validCurr),
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("salary_to"),
		},
		{
			name:        "invalid to above max",
			text:        nil,
			from:        nil,
			to:          pkgutils.VPtr(invalidHighSalary),
			currency:    pkgutils.VPtr(validCurr),
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("salary_to"),
		},
		{
			name:        "invalid range from greater than to",
			text:        nil,
			from:        pkgutils.VPtr(validTo),
			to:          pkgutils.VPtr(validFrom),
			currency:    pkgutils.VPtr(validCurr),
			wantErr:     true,
			expectedErr: ErrInvalidSalaryRange,
		},
		{
			name:        "bounds without currency",
			text:        nil,
			from:        pkgutils.VPtr(validFrom),
			to:          pkgutils.VPtr(validTo),
			currency:    nil,
			wantErr:     true,
			expectedErr: ErrSalaryRequiresCurrency,
		},
		{
			name:        "currency without bounds",
			text:        pkgutils.VPtr(validText),
			from:        nil,
			to:          nil,
			currency:    pkgutils.VPtr(validCurr),
			wantErr:     true,
			expectedErr: ErrCurrencyWithoutSalary,
		},
		{
			name:        "invalid short currency",
			text:        nil,
			from:        pkgutils.VPtr(validFrom),
			to:          nil,
			currency:    pkgutils.VPtr(invalidShortCurr),
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("currency"),
		},
		{
			name:        "invalid long currency",
			text:        nil,
			from:        nil,
			to:          pkgutils.VPtr(validTo),
			currency:    pkgutils.VPtr(invalidLongCurr),
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("currency"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := NewSalary(tt.text, tt.from, tt.to, tt.currency)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Nil(t, got)
				if tt.expectedErr != nil {
					assert.Equal(t, tt.expectedErr, err)
				}
			} else {
				assert.NoError(t, err)
				if tt.text == nil && tt.from == nil && tt.to == nil && tt.currency == nil {
					assert.Nil(t, got)
				} else {
					assert.NotNil(t, got)
					assert.Equal(t, tt.text, got.Text())
					assert.Equal(t, tt.from, got.From())
					assert.Equal(t, tt.to, got.To())
					assert.Equal(t, tt.currency, got.Currency())
				}
			}
		})
	}
}

func TestSalary_RestoreAndMethods(t *testing.T) {
	assert.Nil(t, RestoreSalary(nil, nil, nil, nil))

	text := pkgutils.VPtr(gofakeit.ProductName())
	from := pkgutils.VPtr(gofakeit.Number(10000, 50000))
	to := pkgutils.VPtr(*from + gofakeit.Number(5000, 20000))
	currency := pkgutils.VPtr("USD")

	s := RestoreSalary(text, from, to, currency)
	assert.NotNil(t, s)
	assert.Equal(t, text, s.Text())
	assert.Equal(t, from, s.From())
	assert.Equal(t, to, s.To())
	assert.Equal(t, currency, s.Currency())
	assert.True(t, s.HasBounds())
	assert.False(t, s.IsNegotiable())

	negotiable := RestoreSalary(text, nil, nil, nil)
	assert.NotNil(t, negotiable)
	assert.False(t, negotiable.HasBounds())
	assert.True(t, negotiable.IsNegotiable())

	var nilSalary *Salary
	assert.False(t, nilSalary.HasBounds())
	assert.False(t, nilSalary.IsNegotiable())
}

func TestSalary_Match(t *testing.T) {
	fromVal := 100000
	toVal := 150000
	curr := "RUB"

	salaryWithBounds, err := NewSalary(nil, pkgutils.VPtr(fromVal), pkgutils.VPtr(toVal), pkgutils.VPtr(curr))
	assert.NoError(t, err)

	salaryFromOnly, err := NewSalary(nil, pkgutils.VPtr(fromVal), nil, pkgutils.VPtr(curr))
	assert.NoError(t, err)

	salaryToOnly, err := NewSalary(nil, nil, pkgutils.VPtr(toVal), pkgutils.VPtr(curr))
	assert.NoError(t, err)

	salaryTextOnly, err := NewSalary(pkgutils.VPtr(gofakeit.ProductName()), nil, nil, nil)
	assert.NoError(t, err)

	tests := []struct {
		name        string
		salaryObj   *Salary
		candSalary  int
		currency    string
		wantMatch   bool
		wantErr     bool
		expectedErr error
	}{
		{
			name:        "nil salary receiver matches valid inputs",
			salaryObj:   nil,
			candSalary:  120000,
			currency:    "RUB",
			wantMatch:   true,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "text only salary matches valid inputs",
			salaryObj:   salaryTextOnly,
			candSalary:  120000,
			currency:    "RUB",
			wantMatch:   true,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "invalid candidate salary below min",
			salaryObj:   salaryWithBounds,
			candSalary:  -1,
			currency:    "RUB",
			wantMatch:   false,
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("salary"),
		},
		{
			name:        "invalid candidate salary above max",
			salaryObj:   salaryWithBounds,
			candSalary:  100000001,
			currency:    "RUB",
			wantMatch:   false,
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("salary"),
		},
		{
			name:        "invalid currency length",
			salaryObj:   salaryWithBounds,
			candSalary:  120000,
			currency:    "RU",
			wantMatch:   false,
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("currency"),
		},
		{
			name:        "currency mismatch",
			salaryObj:   salaryWithBounds,
			candSalary:  120000,
			currency:    "USD",
			wantMatch:   false,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "currency case insensitive match",
			salaryObj:   salaryWithBounds,
			candSalary:  120000,
			currency:    "rub",
			wantMatch:   true,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "bounds match within range",
			salaryObj:   salaryWithBounds,
			candSalary:  120000,
			currency:    "RUB",
			wantMatch:   true,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "bounds match at upper limit",
			salaryObj:   salaryWithBounds,
			candSalary:  150000,
			currency:    "RUB",
			wantMatch:   true,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "bounds exceed upper limit",
			salaryObj:   salaryWithBounds,
			candSalary:  160000,
			currency:    "RUB",
			wantMatch:   false,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "from only candidate below from",
			salaryObj:   salaryFromOnly,
			candSalary:  80000,
			currency:    "RUB",
			wantMatch:   true,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "from only candidate equal from",
			salaryObj:   salaryFromOnly,
			candSalary:  100000,
			currency:    "RUB",
			wantMatch:   true,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "from only candidate above from",
			salaryObj:   salaryFromOnly,
			candSalary:  120000,
			currency:    "RUB",
			wantMatch:   false,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "to only candidate below to",
			salaryObj:   salaryToOnly,
			candSalary:  120000,
			currency:    "RUB",
			wantMatch:   true,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "to only candidate equal to",
			salaryObj:   salaryToOnly,
			candSalary:  150000,
			currency:    "RUB",
			wantMatch:   true,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "to only candidate above to",
			salaryObj:   salaryToOnly,
			candSalary:  160000,
			currency:    "RUB",
			wantMatch:   false,
			wantErr:     false,
			expectedErr: nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := tt.salaryObj.Match(tt.candSalary, tt.currency)
			if tt.wantErr {
				assert.Error(t, err)
				assert.False(t, got)
				if tt.expectedErr != nil {
					assert.Equal(t, tt.expectedErr, err)
				}
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.wantMatch, got)
			}
		})
	}
}

func TestLocation_New(t *testing.T) {
	validText := gofakeit.ProductName()
	validCountry := "Russia"
	validCity := "Moscow"

	shortText := "a"
	longText := strings.Repeat("a", 81)
	shortCountry := "R"
	longCountry := strings.Repeat("R", 41)
	shortCity := "M"
	longCity := strings.Repeat("M", 51)

	tests := []struct {
		name        string
		text        *string
		country     *string
		city        *string
		wantErr     bool
		expectedErr error
	}{
		{
			name:        "all nil",
			text:        nil,
			country:     nil,
			city:        nil,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid full location",
			text:        pkgutils.VPtr(validText),
			country:     pkgutils.VPtr(validCountry),
			city:        pkgutils.VPtr(validCity),
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid country only",
			text:        nil,
			country:     pkgutils.VPtr(validCountry),
			city:        nil,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid text only",
			text:        pkgutils.VPtr(validText),
			country:     nil,
			city:        nil,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "invalid text short",
			text:        pkgutils.VPtr(shortText),
			country:     pkgutils.VPtr(validCountry),
			city:        nil,
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("location_text"),
		},
		{
			name:        "invalid text long",
			text:        pkgutils.VPtr(longText),
			country:     pkgutils.VPtr(validCountry),
			city:        nil,
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("location_text"),
		},
		{
			name:        "invalid country short",
			text:        nil,
			country:     pkgutils.VPtr(shortCountry),
			city:        nil,
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("location_country"),
		},
		{
			name:        "invalid country long",
			text:        nil,
			country:     pkgutils.VPtr(longCountry),
			city:        nil,
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("location_country"),
		},
		{
			name:        "invalid city short",
			text:        nil,
			country:     pkgutils.VPtr(validCountry),
			city:        pkgutils.VPtr(shortCity),
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("location_city"),
		},
		{
			name:        "invalid city long",
			text:        nil,
			country:     pkgutils.VPtr(validCountry),
			city:        pkgutils.VPtr(longCity),
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("location_city"),
		},
		{
			name:        "city without country",
			text:        nil,
			country:     nil,
			city:        pkgutils.VPtr(validCity),
			wantErr:     true,
			expectedErr: ErrCityWithoutCountry,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := NewLocation(tt.text, tt.country, tt.city)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Nil(t, got)
				if tt.expectedErr != nil {
					assert.Equal(t, tt.expectedErr, err)
				}
			} else {
				assert.NoError(t, err)
				if tt.text == nil && tt.country == nil && tt.city == nil {
					assert.Nil(t, got)
				} else {
					assert.NotNil(t, got)
					assert.Equal(t, tt.text, got.Text())
					assert.Equal(t, tt.country, got.Country())
					assert.Equal(t, tt.city, got.City())
				}
			}
		})
	}
}

func TestLocation_RestoreAndMethods(t *testing.T) {
	assert.Nil(t, RestoreLocation(nil, nil, nil))

	text := pkgutils.VPtr(gofakeit.ProductName())
	country := pkgutils.VPtr("Germany")
	city := pkgutils.VPtr("Berlin")

	loc := RestoreLocation(text, country, city)
	assert.NotNil(t, loc)
	assert.Equal(t, text, loc.Text())
	assert.Equal(t, country, loc.Country())
	assert.Equal(t, city, loc.City())
	assert.True(t, loc.HasCountry())
	assert.True(t, loc.HasCity())

	locNoCity := RestoreLocation(text, country, nil)
	assert.NotNil(t, locNoCity)
	assert.True(t, locNoCity.HasCountry())
	assert.False(t, locNoCity.HasCity())

	var nilLoc *Location
	assert.False(t, nilLoc.HasCountry())
	assert.False(t, nilLoc.HasCity())
}

func TestVacancy_New_HappyPath(t *testing.T) {
	extID := gofakeit.UUID()
	title := fakeValidTitle()
	company := fakeValidCompany()
	desc := fakeValidDescription()
	url := fakeValidURL()
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)

	salary, err := NewSalary(nil, pkgutils.VPtr(100000), pkgutils.VPtr(150000), pkgutils.VPtr("RUB"))
	assert.NoError(t, err)

	loc, err := NewLocation(pkgutils.VPtr(fakeValidTitle()), pkgutils.VPtr("Russia"), pkgutils.VPtr("Moscow"))
	assert.NoError(t, err)

	v, err := NewVacancy(
		extID, "hh", title, pkgutils.VPtr(company), salary,
		"middle", []string{"remote", "office", "remote"}, loc,
		desc, url, pubAt, parsedAt,
	)

	assert.NoError(t, err)
	assert.NotNil(t, v)
	assert.NotEqual(t, uuid.Nil, v.ID())
	assert.Equal(t, extID, v.ExternalID())
	assert.Equal(t, SourceHH, v.Source())
	assert.Equal(t, title, v.Title())
	assert.Equal(t, pkgutils.VPtr(company), v.Company())
	assert.Equal(t, salary, v.Salary())
	assert.Equal(t, GradeMiddle, v.Grade())
	assert.Equal(t, []EmploymentType{EmploymentRemote, EmploymentOffice}, v.EmploymentTypes())
	assert.Equal(t, loc, v.Location())
	assert.Equal(t, desc, v.Description())
	assert.Equal(t, url, v.URL())
	assert.Equal(t, pubAt, v.PublishedAt())
	assert.Equal(t, parsedAt, v.ParsedAt())

	assert.Equal(t, 100000, *v.SalaryFrom())
	assert.Equal(t, 150000, *v.SalaryTo())
	assert.Equal(t, "RUB", *v.SalaryCurrency())
	assert.Nil(t, v.SalaryText())
	assert.Equal(t, "Russia", *v.LocationCountry())
	assert.Equal(t, "Moscow", *v.LocationCity())
	assert.True(t, v.HasSalary())
	assert.True(t, v.HasLocation())
	assert.True(t, v.HasCompany())
	assert.True(t, v.HasEmploymentType(EmploymentRemote))
	assert.True(t, v.HasEmploymentType(EmploymentOffice))
	assert.False(t, v.HasEmploymentType(EmploymentHybrid))
	assert.True(t, v.FromHH())
	assert.False(t, v.FromTelegram())
	assert.False(t, v.FromOzon())
	assert.True(t, v.IsFrom(SourceHH))
}

func TestVacancy_New_Minimal(t *testing.T) {
	extID := gofakeit.UUID()
	title := fakeValidTitle()
	desc := fakeValidDescription()
	url := fakeValidURL()
	now := time.Now()
	pubAt := now.Add(-10 * time.Minute)
	parsedAt := now.Add(-5 * time.Minute)

	v, err := NewVacancy(
		extID, "telegram", title, nil, nil,
		"senior", []string{"hybrid"}, nil,
		desc, url, pubAt, parsedAt,
	)

	assert.NoError(t, err)
	assert.NotNil(t, v)
	assert.Nil(t, v.Company())
	assert.Nil(t, v.Salary())
	assert.Nil(t, v.Location())
	assert.Nil(t, v.SalaryFrom())
	assert.Nil(t, v.SalaryTo())
	assert.Nil(t, v.SalaryCurrency())
	assert.Nil(t, v.SalaryText())
	assert.Nil(t, v.LocationCountry())
	assert.Nil(t, v.LocationCity())
	assert.False(t, v.HasSalary())
	assert.False(t, v.HasLocation())
	assert.False(t, v.HasCompany())
	assert.True(t, v.FromTelegram())
}

func TestVacancy_New_ValidationErrors(t *testing.T) {
	validExtID := gofakeit.UUID()
	validTitle := fakeValidTitle()
	validCompany := fakeValidCompany()
	validDesc := fakeValidDescription()
	validURL := fakeValidURL()
	now := time.Now()
	validPubAt := now.Add(-1 * time.Hour)
	validParsedAt := now.Add(-30 * time.Minute)

	tests := []struct {
		name        string
		extID       string
		source      string
		title       string
		company     *string
		grade       string
		eTypes      []string
		desc        string
		url         string
		pubAt       time.Time
		parsedAt    time.Time
		expectedErr error
	}{
		{
			name:        "empty external_id",
			extID:       "",
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueRequiredError("external_id"),
		},
		{
			name:        "whitespace external_id",
			extID:       "   ",
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueRequiredError("external_id"),
		},
		{
			name:        "empty source",
			extID:       validExtID,
			source:      "",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueRequiredError("source"),
		},
		{
			name:        "invalid source",
			extID:       validExtID,
			source:      gofakeit.ProductName(),
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueInvalidError("source"),
		},
		{
			name:        "empty title",
			extID:       validExtID,
			source:      "hh",
			title:       "",
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueRequiredError("title"),
		},
		{
			name:        "invalid title short",
			extID:       validExtID,
			source:      "hh",
			title:       "Go",
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueInvalidError("title"),
		},
		{
			name:        "invalid title long",
			extID:       validExtID,
			source:      "hh",
			title:       strings.Repeat("a", 101),
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueInvalidError("title"),
		},
		{
			name:        "invalid company short",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr("A"),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueInvalidError("company"),
		},
		{
			name:        "invalid company long",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(strings.Repeat("A", 101)),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueInvalidError("company"),
		},
		{
			name:        "empty grade",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueRequiredError("grade"),
		},
		{
			name:        "invalid grade",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       gofakeit.ProductName(),
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueInvalidError("grade"),
		},
		{
			name:        "empty employment types",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueRequiredError("employment_types"),
		},
		{
			name:        "invalid employment type in list",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote", gofakeit.ProductName()},
			desc:        validDesc,
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueInvalidError("employment_type"),
		},
		{
			name:        "empty description",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        "",
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueRequiredError("description"),
		},
		{
			name:        "invalid description short",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        strings.Repeat("a", 299),
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueInvalidError("description"),
		},
		{
			name:        "invalid description long",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        strings.Repeat("a", 2501),
			url:         validURL,
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueInvalidError("description"),
		},
		{
			name:        "empty url",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         "",
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueRequiredError("url"),
		},
		{
			name:        "invalid url short",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         "http://a",
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueInvalidError("url"),
		},
		{
			name:        "invalid url long",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         "https://" + strings.Repeat("a", 1020),
			pubAt:       validPubAt,
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueInvalidError("url"),
		},
		{
			name:        "published_at older than 7 days",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       now.Add(-8 * 24 * time.Hour),
			parsedAt:    validParsedAt,
			expectedErr: pkgerrs.NewValueInvalidError("published_at"),
		},
		{
			name:        "published_at in future",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       now.Add(10 * time.Minute),
			parsedAt:    now.Add(15 * time.Minute),
			expectedErr: pkgerrs.NewValueInvalidError("published_at"),
		},
		{
			name:        "parsed_at before published_at",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       now.Add(-1 * time.Hour),
			parsedAt:    now.Add(-2 * time.Hour),
			expectedErr: pkgerrs.NewValueInvalidError("parsed_at"),
		},
		{
			name:        "parsed_at in future",
			extID:       validExtID,
			source:      "hh",
			title:       validTitle,
			company:     pkgutils.VPtr(validCompany),
			grade:       "junior",
			eTypes:      []string{"remote"},
			desc:        validDesc,
			url:         validURL,
			pubAt:       now.Add(-1 * time.Hour),
			parsedAt:    now.Add(10 * time.Minute),
			expectedErr: pkgerrs.NewValueInvalidError("parsed_at"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v, err := NewVacancy(
				tt.extID, tt.source, tt.title, tt.company, nil,
				tt.grade, tt.eTypes, nil,
				tt.desc, tt.url, tt.pubAt, tt.parsedAt,
			)
			assert.Error(t, err)
			assert.Nil(t, v)
			assert.Equal(t, tt.expectedErr, err)
		})
	}
}

func TestVacancy_RestoreAndEncapsulation(t *testing.T) {
	id := uuid.New()
	extID := gofakeit.UUID()
	title := fakeValidTitle()
	company := fakeValidCompany()
	desc := fakeValidDescription()
	url := fakeValidURL()
	pubAt := time.Now().Add(-2 * time.Hour)
	parsedAt := time.Now().Add(-1 * time.Hour)

	salary := RestoreSalary(nil, pkgutils.VPtr(80000), pkgutils.VPtr(120000), pkgutils.VPtr("USD"))
	loc := RestoreLocation(pkgutils.VPtr(fakeValidTitle()), pkgutils.VPtr("USA"), pkgutils.VPtr("New York"))
	originalETypes := []EmploymentType{EmploymentRemote, EmploymentOffice}

	v := RestoreVacancy(
		id, extID, SourceOzon, title, pkgutils.VPtr(company), salary,
		GradeSenior, originalETypes, loc,
		desc, url, pubAt, parsedAt,
	)

	assert.NotNil(t, v)
	assert.Equal(t, id, v.ID())
	assert.Equal(t, extID, v.ExternalID())
	assert.Equal(t, SourceOzon, v.Source())
	assert.Equal(t, title, v.Title())
	assert.Equal(t, pkgutils.VPtr(company), v.Company())
	assert.Equal(t, salary, v.Salary())
	assert.Equal(t, GradeSenior, v.Grade())
	assert.Equal(t, originalETypes, v.EmploymentTypes())
	assert.Equal(t, loc, v.Location())
	assert.Equal(t, desc, v.Description())
	assert.Equal(t, url, v.URL())
	assert.Equal(t, pubAt, v.PublishedAt())
	assert.Equal(t, parsedAt, v.ParsedAt())
	assert.True(t, v.FromOzon())

	originalETypes[0] = EmploymentContract
	assert.Equal(t, EmploymentRemote, v.EmploymentTypes()[0])

	gotETypes := v.EmploymentTypes()
	gotETypes[0] = EmploymentContract
	assert.Equal(t, EmploymentRemote, v.EmploymentTypes()[0])

	assert.Nil(t, RestoreVacancy(id, extID, SourceOzon, title, nil, nil, GradeSenior, nil, nil, desc, url, pubAt, parsedAt).EmploymentTypes())
}

func TestVacancy_BusinessLogic(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-2 * time.Hour)
	parsedAt := now.Add(-1 * time.Hour)

	salary, err := NewSalary(nil, pkgutils.VPtr(100000), pkgutils.VPtr(150000), pkgutils.VPtr("RUB"))
	assert.NoError(t, err)

	v, err := NewVacancy(
		gofakeit.UUID(), "hh", fakeValidTitle(), nil, salary,
		"middle", []string{"remote", "hybrid"}, nil,
		fakeValidDescription(), fakeValidURL(), pubAt, parsedAt,
	)
	assert.NoError(t, err)

	assert.True(t, v.IsPublishedAfter(now.Add(-3*time.Hour)))
	assert.False(t, v.IsPublishedAfter(now.Add(-1*time.Hour)))

	assert.False(t, v.IsExpired())
	assert.False(t, v.IsExpiredAt(now))
	assert.True(t, v.IsExpiredAt(pubAt.Add(8*24*time.Hour)))

	matchGradeTests := []struct {
		name      string
		grade     Grade
		wantMatch bool
	}{
		{
			name:      "empty grade matches any",
			grade:     "",
			wantMatch: true,
		},
		{
			name:      "same grade matches",
			grade:     GradeMiddle,
			wantMatch: true,
		},
		{
			name:      "same grade uppercase matches",
			grade:     "MIDDLE",
			wantMatch: true,
		},
		{
			name:      "different grade does not match",
			grade:     GradeSenior,
			wantMatch: false,
		},
	}
	for _, tt := range matchGradeTests {
		t.Run(tt.name, func(t *testing.T) {
			assert.Equal(t, tt.wantMatch, v.MatchByGrade(tt.grade))
		})
	}

	matchEmploymentTests := []struct {
		name      string
		eTypes    []EmploymentType
		wantMatch bool
	}{
		{
			name:      "nil filter matches",
			eTypes:    nil,
			wantMatch: true,
		},
		{
			name:      "empty filter matches",
			eTypes:    []EmploymentType{},
			wantMatch: true,
		},
		{
			name:      "one matching type matches",
			eTypes:    []EmploymentType{EmploymentOffice, EmploymentRemote},
			wantMatch: true,
		},
		{
			name:      "uppercase matching type matches",
			eTypes:    []EmploymentType{"HYBRID"},
			wantMatch: true,
		},
		{
			name:      "no matching types",
			eTypes:    []EmploymentType{EmploymentOffice, EmploymentContract},
			wantMatch: false,
		},
	}
	for _, tt := range matchEmploymentTests {
		t.Run(tt.name, func(t *testing.T) {
			assert.Equal(t, tt.wantMatch, v.MatchByEmploymentTypes(tt.eTypes))
		})
	}

	matchSalaryTests := []struct {
		name        string
		salary      *int
		currency    *string
		wantMatch   bool
		wantErr     bool
		expectedErr error
	}{
		{
			name:        "nil salary and nil currency matches",
			salary:      nil,
			currency:    nil,
			wantMatch:   true,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "nil salary with currency returns ErrCurrencyWithoutSalary",
			salary:      nil,
			currency:    pkgutils.VPtr("RUB"),
			wantMatch:   false,
			wantErr:     true,
			expectedErr: ErrCurrencyWithoutSalary,
		},
		{
			name:        "salary without currency returns ErrSalaryRequiresCurrency",
			salary:      pkgutils.VPtr(120000),
			currency:    nil,
			wantMatch:   false,
			wantErr:     true,
			expectedErr: ErrSalaryRequiresCurrency,
		},
		{
			name:        "invalid salary range",
			salary:      pkgutils.VPtr(-10),
			currency:    pkgutils.VPtr("RUB"),
			wantMatch:   false,
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("salary"),
		},
		{
			name:        "invalid currency length",
			salary:      pkgutils.VPtr(120000),
			currency:    pkgutils.VPtr("RU"),
			wantMatch:   false,
			wantErr:     true,
			expectedErr: pkgerrs.NewValueInvalidError("currency"),
		},
		{
			name:        "valid match within bounds",
			salary:      pkgutils.VPtr(120000),
			currency:    pkgutils.VPtr("RUB"),
			wantMatch:   true,
			wantErr:     false,
			expectedErr: nil,
		},
		{
			name:        "valid match exceeding bounds",
			salary:      pkgutils.VPtr(160000),
			currency:    pkgutils.VPtr("RUB"),
			wantMatch:   false,
			wantErr:     false,
			expectedErr: nil,
		},
	}
	for _, tt := range matchSalaryTests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := v.MatchBySalary(tt.salary, tt.currency)
			if tt.wantErr {
				assert.Error(t, err)
				assert.False(t, got)
				assert.Equal(t, tt.expectedErr, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.wantMatch, got)
			}
		})
	}

	vacNoSalary, err := NewVacancy(
		gofakeit.UUID(), "hh", fakeValidTitle(), nil, nil,
		"lead", []string{"remote"}, nil,
		fakeValidDescription(), fakeValidURL(), pubAt, parsedAt,
	)
	assert.NoError(t, err)
	got, err := vacNoSalary.MatchBySalary(pkgutils.VPtr(200000), pkgutils.VPtr("USD"))
	assert.NoError(t, err)
	assert.True(t, got)
}

func TestVacancy_Mutations(t *testing.T) {
	now := time.Now()
	pubAt := now.Add(-3 * time.Hour)
	parsedAt := now.Add(-2 * time.Hour)

	v, err := NewVacancy(
		gofakeit.UUID(), "hh", fakeValidTitle(), nil, nil,
		"junior", []string{"remote"}, nil,
		fakeValidDescription(), fakeValidURL(), pubAt, parsedAt,
	)
	assert.NoError(t, err)

	newTitle := fakeValidTitle()
	newCompany := fakeValidCompany()
	newDesc := fakeValidDescription()
	newURL := fakeValidURL()
	newParsedAt := now.Add(-1 * time.Hour)
	newSalary, err := NewSalary(nil, pkgutils.VPtr(120000), pkgutils.VPtr(180000), pkgutils.VPtr("RUB"))
	assert.NoError(t, err)
	newLoc, err := NewLocation(nil, pkgutils.VPtr("Russia"), pkgutils.VPtr("Kazan"))
	assert.NoError(t, err)

	err = v.Update(
		newTitle, pkgutils.VPtr(newCompany), newSalary,
		"middle", []string{"office", "hybrid"}, newLoc,
		newDesc, newURL, newParsedAt,
	)
	assert.NoError(t, err)
	assert.Equal(t, newTitle, v.Title())
	assert.Equal(t, pkgutils.VPtr(newCompany), v.Company())
	assert.Equal(t, newSalary, v.Salary())
	assert.Equal(t, GradeMiddle, v.Grade())
	assert.Equal(t, []EmploymentType{EmploymentOffice, EmploymentHybrid}, v.EmploymentTypes())
	assert.Equal(t, newLoc, v.Location())
	assert.Equal(t, newDesc, v.Description())
	assert.Equal(t, newURL, v.URL())
	assert.Equal(t, newParsedAt, v.ParsedAt())

	err = v.Update(
		newTitle, nil, nil,
		"senior", []string{"remote"}, nil,
		newDesc, newURL, newParsedAt,
	)
	assert.NoError(t, err)
	assert.Nil(t, v.Company())
	assert.Nil(t, v.Salary())
	assert.Nil(t, v.Location())

	err = v.Update(
		"", pkgutils.VPtr(newCompany), newSalary,
		"middle", []string{"office"}, newLoc,
		newDesc, newURL, newParsedAt,
	)
	assert.Equal(t, pkgerrs.NewValueRequiredError("title"), err)

	err = v.Update(
		newTitle, pkgutils.VPtr("A"), newSalary,
		"middle", []string{"office"}, newLoc,
		newDesc, newURL, newParsedAt,
	)
	assert.Equal(t, pkgerrs.NewValueInvalidError("company"), err)

	err = v.Update(
		newTitle, pkgutils.VPtr(newCompany), newSalary,
		gofakeit.ProductName(), []string{"office"}, newLoc,
		newDesc, newURL, newParsedAt,
	)
	assert.Equal(t, pkgerrs.NewValueInvalidError("grade"), err)

	err = v.Update(
		newTitle, pkgutils.VPtr(newCompany), newSalary,
		"middle", []string{}, newLoc,
		newDesc, newURL, newParsedAt,
	)
	assert.Equal(t, pkgerrs.NewValueRequiredError("employment_types"), err)

	err = v.Update(
		newTitle, pkgutils.VPtr(newCompany), newSalary,
		"middle", []string{"office"}, newLoc,
		"", newURL, newParsedAt,
	)
	assert.Equal(t, pkgerrs.NewValueRequiredError("description"), err)

	err = v.Update(
		newTitle, pkgutils.VPtr(newCompany), newSalary,
		"middle", []string{"office"}, newLoc,
		newDesc, "", newParsedAt,
	)
	assert.Equal(t, pkgerrs.NewValueRequiredError("url"), err)

	err = v.Update(
		newTitle, pkgutils.VPtr(newCompany), newSalary,
		"middle", []string{"office"}, newLoc,
		newDesc, newURL, pubAt.Add(-10*time.Minute),
	)
	assert.Equal(t, pkgerrs.NewValueInvalidError("parsed_at"), err)

	newerParsedAt := now.Add(-30 * time.Minute)
	err = v.UpdateParsedAt(newerParsedAt)
	assert.NoError(t, err)
	assert.Equal(t, newerParsedAt, v.ParsedAt())

	err = v.UpdateParsedAt(pubAt.Add(-5 * time.Minute))
	assert.Equal(t, pkgerrs.NewValueInvalidError("parsed_at"), err)

	err = v.UpdateParsedAt(now.Add(10 * time.Minute))
	assert.Equal(t, pkgerrs.NewValueInvalidError("parsed_at"), err)

	anotherSalary, err := NewSalary(nil, pkgutils.VPtr(150000), nil, pkgutils.VPtr("USD"))
	assert.NoError(t, err)
	v.UpdateSalary(anotherSalary)
	assert.Equal(t, anotherSalary, v.Salary())

	anotherLoc, err := NewLocation(nil, pkgutils.VPtr("Germany"), pkgutils.VPtr("Munich"))
	assert.NoError(t, err)
	v.UpdateLocation(anotherLoc)
	assert.Equal(t, anotherLoc, v.Location())
}
