package model

import (
	pkgerrs "ai-job-assistant/backend/pkg/errs"
	pkgtuils "ai-job-assistant/backend/pkg/utils"
	"strings"
	"time"

	"github.com/google/uuid"
)

// ================ Vacancy source value object ================

type VacancySource string

const (
	SourceHH       VacancySource = "hh"
	SourceTelegram VacancySource = "telegram"
	SourceOzon     VacancySource = "ozon"
)

func NewVacancySource(raw string) (VacancySource, error) {
	if len(raw) == 0 {
		return "", pkgerrs.NewValueRequiredError("source")
	}

	source := VacancySource(strings.ToLower(raw))
	if !source.IsValid() {
		return "", pkgerrs.NewValueInvalidError("source")
	}

	return source, nil
}

func (s VacancySource) String() string { return string(s) }

func (s VacancySource) IsValid() bool {
	return s == SourceHH || s == SourceTelegram || s == SourceOzon
}

// ================ Grade value object ================

type Grade string

const (
	GradeIntern Grade = "intern"
	GradeJunior Grade = "junior"
	GradeMiddle Grade = "middle"
	GradeSenior Grade = "senior"
	GradeLead   Grade = "lead"
)

func NewGrade(raw string) (Grade, error) {
	if len(raw) == 0 {
		return "", pkgerrs.NewValueRequiredError("grade")
	}

	grade := Grade(raw)
	if !grade.IsValid() {
		return "", pkgerrs.NewValueInvalidError("grade")
	}

	return grade, nil
}

func (g Grade) String() string { return string(g) }

func (g Grade) IsValid() bool {
	return g == GradeIntern || g == GradeJunior ||
		g == GradeMiddle || g == GradeSenior ||
		g == GradeLead
}

// ================ Employment Type value object ================

type EmploymentType string

const (
	EmploymentRemote   EmploymentType = "remote"
	EmploymentOffice   EmploymentType = "office"
	EmploymentHybrid   EmploymentType = "hybrid"
	EmploymentContract EmploymentType = "contract"
)

func NewEmploymentType(raw string) (EmploymentType, error) {
	if len(raw) == 0 {
		return "", pkgerrs.NewValueRequiredError("employment_type")
	}

	eType := EmploymentType(raw)
	if !eType.IsValid() {
		return "", pkgerrs.NewValueInvalidError("employment_type")
	}

	return eType, nil
}

func (e EmploymentType) String() string { return string(e) }

func (e EmploymentType) IsValid() bool {
	return e == EmploymentRemote || e == EmploymentOffice ||
		e == EmploymentHybrid || e == EmploymentContract
}

// ================ Rich model of Vacancy ================

const (
	minTitleLen, maxTitleLen             = 3, 100
	minCompanyLen, maxCompanyLen         = 2, 100
	minSalaryLen, maxSalaryLen           = 2, 150
	minSalaryVal, maxSalaryVal           = 0, 100000000 // 10^8 (e.g. a billion)
	minCurrencyLen, maxCurrencyLen       = 3, 3
	minLocationLen, maxLocationLen       = 2, 80
	minDescriptionLen, maxDescriptionLen = 300, 2500
	minURLLen, maxURLLen                 = 10, 1024

	vacancyValidUpTo  = 24 * time.Hour * 7
	maxFutureTimeSkew = 5 * time.Minute
)

type Vacancy struct {
	id         uuid.UUID
	externalID string

	source  VacancySource
	title   string
	company *string

	salaryText *string
	salaryFrom *int
	salaryTo   *int
	currency   *string

	grade          Grade
	employmentType EmploymentType

	location    *string
	description string
	url         string
	publishedAt time.Time
	parsedAt    time.Time
}

func NewVacancy(
	externalID, rawSource, title string,
	company, salaryText *string,
	salaryFrom, salaryTo *int,
	currency *string,
	rawGrade, rawEmploymentType string,
	location *string,
	description, url string,
	publishedAt, parsedAt time.Time,
) (*Vacancy, error) {
	if len(externalID) == 0 {
		return nil, pkgerrs.NewValueRequiredError("external_id")
	}

	source, err := NewVacancySource(rawSource)
	if err != nil {
		return nil, err
	}

	if len(title) == 0 {
		return nil, pkgerrs.NewValueRequiredError("title")
	}
	if !pkgtuils.StrWithinRange(title, minTitleLen, maxTitleLen, true) {
		return nil, pkgerrs.NewValueInvalidError("title")
	}

	if company != nil && !pkgtuils.StrWithinRange(*company, minCompanyLen, maxCompanyLen, true) {
		return nil, pkgerrs.NewValueInvalidError("company")
	}

	if salaryText != nil && !pkgtuils.StrWithinRange(*salaryText, minSalaryLen, maxSalaryLen, true) {
		return nil, pkgerrs.NewValueInvalidError("salary_text")
	}

	if salaryFrom != nil && (*salaryFrom < minSalaryVal || *salaryFrom > maxSalaryVal) {
		return nil, pkgerrs.NewValueInvalidError("salary_from")
	}
	if salaryTo != nil && (*salaryTo < minSalaryVal || *salaryTo > maxSalaryVal) {
		return nil, pkgerrs.NewValueInvalidError("salary_to")
	}
	if salaryFrom != nil && salaryTo != nil && *salaryFrom > *salaryTo {
		return nil, pkgerrs.NewValueInvalidError("price_range")
	}
	if currency != nil && !pkgtuils.StrWithinRange(*currency, minCurrencyLen, maxCurrencyLen, false) {
		return nil, pkgerrs.NewValueInvalidError("currency")
	}

	grade, err := NewGrade(rawGrade)
	if err != nil {
		return nil, err
	}

	employmentType, err := NewEmploymentType(rawEmploymentType)
	if err != nil {
		return nil, err
	}

	if location != nil && !pkgtuils.StrWithinRange(*location, minLocationLen, maxLocationLen, true) {
		return nil, pkgerrs.NewValueInvalidError("location")
	}

	if len(description) == 0 {
		return nil, pkgerrs.NewValueRequiredError("description")
	}
	if !pkgtuils.StrWithinRange(description, minDescriptionLen, maxDescriptionLen, true) {
		return nil, pkgerrs.NewValueInvalidError("description")
	}

	if len(url) == 0 {
		return nil, pkgerrs.NewValueRequiredError("url")
	}
	if !pkgtuils.StrWithinRange(url, minURLLen, maxURLLen, true) {
		return nil, pkgerrs.NewValueInvalidError("url")
	}

	now := time.Now()
	if publishedAt.Before(now.Add(-1*vacancyValidUpTo)) || publishedAt.After(now.Add(maxFutureTimeSkew)) {
		return nil, pkgerrs.NewValueInvalidError("published_at")
	}
	if parsedAt.Before(publishedAt) || parsedAt.After(now.Add(maxFutureTimeSkew)) {
		return nil, pkgerrs.NewValueInvalidError("parsed_at")
	}

	return &Vacancy{
		id:             uuid.New(),
		externalID:     externalID,
		source:         source,
		title:          title,
		company:        company,
		salaryText:     salaryText,
		salaryFrom:     salaryFrom,
		salaryTo:       salaryTo,
		currency:       currency,
		grade:          grade,
		employmentType: employmentType,
		location:       location,
		description:    description,
		url:            url,
		publishedAt:    publishedAt,
		parsedAt:       parsedAt,
	}, nil
}
