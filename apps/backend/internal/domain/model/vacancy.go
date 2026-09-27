package model

import (
	pkgerrs "ai-job-assistant/backend/pkg/errs"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/google/uuid"
)

type VacancySource string

const (
	SourceHH       VacancySource = "hh"
	SourceTelegram VacancySource = "telegram"
	SourceOzon     VacancySource = "ozon"
)

func (s VacancySource) String() string { return string(s) }

func (s VacancySource) IsValid() bool {
	return s == SourceHH || s == SourceTelegram || s == SourceOzon
}

type Grade string

const (
	GradeIntern Grade = "intern"
	GradeJunior Grade = "junior"
	GradeMiddle Grade = "middle"
	GradeSenior Grade = "senior"
	GradeLead   Grade = "lead"
)

func (g Grade) String() string { return string(g) }

func (g Grade) IsValid() bool {
	return g == GradeIntern || g == GradeJunior ||
		g == GradeMiddle || g == GradeSenior ||
		g == GradeLead
}

type EmploymentType string

const (
	EmploymentRemote   EmploymentType = "remote"
	EmploymentOffice   EmploymentType = "office"
	EmploymentHybrid   EmploymentType = "hybrid"
	EmploymentContract EmploymentType = "contract"
)

func (e EmploymentType) String() string { return string(e) }

func (e EmploymentType) IsValid() bool {
	return e == EmploymentRemote || e == EmploymentOffice ||
		e == EmploymentHybrid || e == EmploymentContract
}

// ================ Rich model for Vacancy ================

const (
	minTitleLen, maxTitleLen     = 3, 100
	minCompanyLen, maxCompanyLen = 2, 100
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

	grade          *Grade
	employmentType *EmploymentType

	location    *string
	description *string
	url         string
	publishedAt time.Time
	parsedAt    time.Time
}

func NewVacancy(
	externalID, rawSource, title string,
	company, salaryText,
	location, description *string,
	url string, publishedAt time.Time,
) (*Vacancy, error) {
	if len(externalID) == 0 {
		return nil, pkgerrs.NewValueRequiredError("external_id")
	}
	if len(rawSource) == 0 {
		return nil, pkgerrs.NewValueRequiredError("source")
	}

	source := VacancySource(strings.ToLower(rawSource))
	if !source.IsValid() {
		return nil, pkgerrs.NewValueInvalidError("source")
	}

	titleLen := utf8.RuneCountInString(title)
	if titleLen == 0 {
		return nil, pkgerrs.NewValueRequiredError("title")
	}
	if titleLen < minTitleLen || titleLen > maxTitleLen {
		return nil, pkgerrs.NewValueInvalidError("title")
	}

	if company != nil {
		companyLen := utf8.RuneCountInString(*company)
		if companyLen < minCompanyLen || companyLen > maxCompanyLen {
			return nil, pkgerrs.NewValueInvalidError("company")
		}
	}
}
