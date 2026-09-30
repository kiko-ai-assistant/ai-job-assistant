package model

import (
	pkgerrs "ai-job-assistant/backend/pkg/errs"
	pkgtuils "ai-job-assistant/backend/pkg/utils"
	"errors"
	"strings"
	"time"

	"github.com/google/uuid"
)

// ================ Domain Errors ================

var (
	ErrSalaryRequiresCurrency = errors.New("currency is required when salary bounds are specified")
	ErrCurrencyWithoutSalary  = errors.New("currency cannot be specified without salary bounds")
	ErrInvalidSalaryRange     = errors.New("salary_from cannot be greater than salary_to")
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

// ================ Salary value object ================

type Salary struct {
	text     *string
	from     *int
	to       *int
	currency *string
}

func NewSalary(text *string, from, to *int, currency *string) (*Salary, error) {
	if text == nil && from == nil && to == nil && currency == nil {
		return nil, nil
	}

	if text != nil && !pkgtuils.StrWithinRange(*text, minSalaryLen, maxSalaryLen, true) {
		return nil, pkgerrs.NewValueInvalidError("salary_text")
	}

	if from != nil && (*from < minSalaryVal || *from > maxSalaryVal) {
		return nil, pkgerrs.NewValueInvalidError("salary_from")
	}
	if to != nil && (*to < minSalaryVal || *to > maxSalaryVal) {
		return nil, pkgerrs.NewValueInvalidError("salary_to")
	}
	if from != nil && to != nil && *from > *to {
		return nil, ErrInvalidSalaryRange
	}

	hasBounds := from != nil || to != nil
	hasCurrency := currency != nil && len(strings.TrimSpace(*currency)) > 0

	if hasBounds && !hasCurrency {
		return nil, ErrSalaryRequiresCurrency
	}
	if !hasBounds && hasCurrency {
		return nil, ErrCurrencyWithoutSalary
	}

	if currency != nil && !pkgtuils.StrWithinRange(*currency, minCurrencyLen, maxCurrencyLen, false) {
		return nil, pkgerrs.NewValueInvalidError("currency")
	}

	return &Salary{
		text:     text,
		from:     from,
		to:       to,
		currency: currency,
	}, nil
}

func RestoreSalary(text *string, from, to *int, currency *string) *Salary {
	if text == nil && from == nil && to == nil && currency == nil {
		return nil
	}
	return &Salary{
		text:     text,
		from:     from,
		to:       to,
		currency: currency,
	}
}

func (s *Salary) Text() *string     { return s.text }
func (s *Salary) From() *int        { return s.from }
func (s *Salary) To() *int          { return s.to }
func (s *Salary) Currency() *string { return s.currency }

func (s *Salary) Match(salary int, currency string) (bool, error) {
	if salary < minSalaryVal || salary > maxSalaryVal {
		return false, pkgerrs.NewValueInvalidError("salary")
	}
	if len(currency) < minCurrencyLen || len(currency) > maxCurrencyLen {
		return false, pkgerrs.NewValueInvalidError("currency")
	}

	if s == nil || (s.from == nil && s.to == nil) {
		return true, nil
	}

	if s.currency == nil || !strings.EqualFold(*s.currency, currency) {
		return false, nil
	}

	if s.to != nil {
		return *s.to >= salary, nil
	}

	if s.from != nil {
		return *s.from >= salary, nil
	}

	return true, nil
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

	salary *Salary

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
	company *string,
	salary *Salary,
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
		salary:         salary,
		grade:          grade,
		employmentType: employmentType,
		location:       location,
		description:    description,
		url:            url,
		publishedAt:    publishedAt,
		parsedAt:       parsedAt,
	}, nil
}

func RestoreVacancy(
	id uuid.UUID,
	externalID string,
	source VacancySource,
	title string,
	company *string,
	salary *Salary,
	grade Grade,
	employmentType EmploymentType,
	location *string,
	description, url string,
	publishedAt, parsedAt time.Time,
) *Vacancy {
	return &Vacancy{
		id:             id,
		externalID:     externalID,
		source:         source,
		title:          title,
		company:        company,
		salary:         salary,
		grade:          grade,
		employmentType: employmentType,
		location:       location,
		description:    description,
		url:            url,
		publishedAt:    publishedAt,
		parsedAt:       parsedAt,
	}
}

// ======================== Read-Only ========================

func (v *Vacancy) ID() uuid.UUID                  { return v.id }
func (v *Vacancy) ExternalID() string             { return v.externalID }
func (v *Vacancy) Source() VacancySource          { return v.source }
func (v *Vacancy) Title() string                  { return v.title }
func (v *Vacancy) Company() *string               { return v.company }
func (v *Vacancy) Salary() *Salary                { return v.salary }
func (v *Vacancy) SalaryText() *string {
	if v.salary == nil {
		return nil
	}
	return v.salary.Text()
}
func (v *Vacancy) SalaryFrom() *int {
	if v.salary == nil {
		return nil
	}
	return v.salary.From()
}
func (v *Vacancy) SalaryTo() *int {
	if v.salary == nil {
		return nil
	}
	return v.salary.To()
}
func (v *Vacancy) Currency() *string {
	if v.salary == nil {
		return nil
	}
	return v.salary.Currency()
}
func (v *Vacancy) Grade() Grade                   { return v.grade }
func (v *Vacancy) EmploymentType() EmploymentType { return v.employmentType }
func (v *Vacancy) Location() *string              { return v.location }
func (v *Vacancy) Description() string            { return v.description }
func (v *Vacancy) URL() string                    { return v.url }
func (v *Vacancy) PublishedAt() time.Time         { return v.publishedAt }
func (v *Vacancy) ParsedAt() time.Time            { return v.parsedAt }

// ================ Business Logic ================

func (v *Vacancy) FromHH() bool       { return v.source == SourceHH }
func (v *Vacancy) FromTelegram() bool { return v.source == SourceTelegram }
func (v *Vacancy) FromOzon() bool     { return v.source == SourceOzon }

func (v *Vacancy) MatchBySalary(salary int, currency string) (bool, error) {
	if salary < minSalaryVal || salary > maxSalaryVal {
		return false, pkgerrs.NewValueInvalidError("salary")
	}
	if len(currency) < minCurrencyLen || len(currency) > maxCurrencyLen {
		return false, pkgerrs.NewValueInvalidError("currency")
	}

	if v.salary == nil {
		return true, nil
	}

	return v.salary.Match(salary, currency)
}
