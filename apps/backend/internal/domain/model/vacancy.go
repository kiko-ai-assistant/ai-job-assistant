package model

import (
	pkgerrs "ai-job-assistant/backend/pkg/errs"
	pkgutils "ai-job-assistant/backend/pkg/utils"
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

	ErrCityWithoutCountry = errors.New("city cannot be specified without country")
)

// ================ Vacancy source value object ================

type VacancySource string

const (
	SourceHH       VacancySource = "hh"
	SourceTelegram VacancySource = "telegram"
	SourceOzon     VacancySource = "ozon"
)

func NewVacancySource(raw string) (VacancySource, error) {
	trimmed := strings.TrimSpace(raw)
	if len(trimmed) == 0 {
		return "", pkgerrs.NewValueRequiredError("source")
	}

	source := VacancySource(strings.ToLower(trimmed))
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
	trimmed := strings.TrimSpace(raw)
	if len(trimmed) == 0 {
		return "", pkgerrs.NewValueRequiredError("grade")
	}

	grade := Grade(strings.ToLower(trimmed))
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
	trimmed := strings.TrimSpace(raw)
	if len(trimmed) == 0 {
		return "", pkgerrs.NewValueRequiredError("employment_type")
	}

	eType := EmploymentType(strings.ToLower(trimmed))
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

	if text != nil && !pkgutils.StrWithinRange(*text, minSalaryLen, maxSalaryLen, true) {
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

	if currency != nil && !pkgutils.StrWithinRange(*currency, minCurrencyLen, maxCurrencyLen, false) {
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

// ==================== Read-Only ====================

func (s *Salary) Text() *string     { return s.text }
func (s *Salary) From() *int        { return s.from }
func (s *Salary) To() *int          { return s.to }
func (s *Salary) Currency() *string { return s.currency }

// ================ Business Logic ================

func (s *Salary) HasBounds() bool {
	return s != nil && (s.from != nil || s.to != nil)
}

func (s *Salary) IsNegotiable() bool {
	return s != nil && s.from == nil && s.to == nil && s.text != nil
}

func (s *Salary) Match(salary int, currency string) (bool, error) {
	if salary < minSalaryVal || salary > maxSalaryVal {
		return false, pkgerrs.NewValueInvalidError("salary")
	}
	if !pkgutils.StrWithinRange(currency, minCurrencyLen, maxCurrencyLen, false) {
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

// ================ Location value object ================

type Location struct {
	text    *string
	country *string
	city    *string
}

func NewLocation(text, country, city *string) (*Location, error) {
	if text == nil && country == nil && city == nil {
		return nil, nil
	}

	if text != nil && !pkgutils.StrWithinRange(*text, minLocTextLen, maxLocTextLen, true) {
		return nil, pkgerrs.NewValueInvalidError("location_text")
	}
	if country != nil && !pkgutils.StrWithinRange(*country, minLocCountryLen, maxLocCountryLen, true) {
		return nil, pkgerrs.NewValueInvalidError("location_country")
	}
	if city != nil && !pkgutils.StrWithinRange(*city, minLocCityLen, maxLocCityLen, true) {
		return nil, pkgerrs.NewValueInvalidError("location_city")
	}

	if country == nil && city != nil {
		return nil, ErrCityWithoutCountry
	}

	return &Location{
		text:    text,
		country: country,
		city:    city,
	}, nil
}

func RestoreLocation(text, country, city *string) *Location {
	if text == nil && country == nil && city == nil {
		return nil
	}
	return &Location{text: text, country: country, city: city}
}

// ==================== Read-Only ====================

func (l *Location) Text() *string    { return l.text }
func (l *Location) Country() *string { return l.country }
func (l *Location) City() *string    { return l.city }

// ================ Business Logic ================

func (l *Location) HasCountry() bool {
	return l != nil && l.country != nil
}

func (l *Location) HasCity() bool {
	return l != nil && l.city != nil
}

func (l *Location) Match(country string, city *string) (bool, error) {
	if !pkgutils.StrWithinRange(country, minLocCountryLen, maxLocCountryLen, true) {
		return false, pkgerrs.NewValueInvalidError("country")
	}
	if city != nil && !pkgutils.StrWithinRange(*city, minLocCityLen, maxLocCityLen, true) {
		return false, pkgerrs.NewValueInvalidError("city")
	}

	if l == nil || (l.country == nil && l.city == nil) { // vacancy has no location filters - true
		return true, nil
	}

	if l.country != nil && !strings.EqualFold(*l.country, country) { // countries discrepancy
		return false, nil
	}

	if city != nil {
		if l.city != nil {
			return strings.EqualFold(*l.city, *city), nil // match by cities
		}
		return false, nil // vacancy has no city but user requested specific city
	}

	if l.country != nil { // countries are matched
		return true, nil
	}

	return false, nil
}

// ================ Rich model of Vacancy ================

const (
	minTitleLen, maxTitleLen             = 3, 100
	minCompanyLen, maxCompanyLen         = 2, 100
	minSalaryLen, maxSalaryLen           = 2, 150
	minSalaryVal, maxSalaryVal           = 0, 100000000 // 10^8 (e.g. 100 million)
	minCurrencyLen, maxCurrencyLen       = 3, 3
	minLocTextLen, maxLocTextLen         = 2, 80
	minLocCountryLen, maxLocCountryLen   = 2, 40
	minLocCityLen, maxLocCityLen         = 2, 50
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

	grade           Grade
	employmentTypes []EmploymentType

	location    *Location
	description string
	url         string
	publishedAt time.Time
	parsedAt    time.Time
}

func NewVacancy(
	externalID, rawSource, title string,
	company *string,
	salary *Salary,
	rawGrade string,
	rawEmploymentTypes []string,
	location *Location,
	description, url string,
	publishedAt, parsedAt time.Time,
) (*Vacancy, error) {
	if len(strings.TrimSpace(externalID)) == 0 {
		return nil, pkgerrs.NewValueRequiredError("external_id")
	}

	source, err := NewVacancySource(rawSource)
	if err != nil {
		return nil, err
	}

	if len(strings.TrimSpace(title)) == 0 {
		return nil, pkgerrs.NewValueRequiredError("title")
	}
	if !pkgutils.StrWithinRange(title, minTitleLen, maxTitleLen, true) {
		return nil, pkgerrs.NewValueInvalidError("title")
	}

	if company != nil && !pkgutils.StrWithinRange(*company, minCompanyLen, maxCompanyLen, true) {
		return nil, pkgerrs.NewValueInvalidError("company")
	}

	grade, err := NewGrade(rawGrade)
	if err != nil {
		return nil, err
	}

	if len(rawEmploymentTypes) == 0 {
		return nil, pkgerrs.NewValueRequiredError("employment_types")
	}

	seenETypes := make(map[EmploymentType]struct{}, len(rawEmploymentTypes))
	eTypes := make([]EmploymentType, 0, len(rawEmploymentTypes))
	for _, raw := range rawEmploymentTypes {
		employmentType, err := NewEmploymentType(raw)
		if err != nil {
			return nil, err
		}
		if _, exists := seenETypes[employmentType]; !exists {
			seenETypes[employmentType] = struct{}{}
			eTypes = append(eTypes, employmentType)
		}
	}

	if len(strings.TrimSpace(description)) == 0 {
		return nil, pkgerrs.NewValueRequiredError("description")
	}
	if !pkgutils.StrWithinRange(description, minDescriptionLen, maxDescriptionLen, true) {
		return nil, pkgerrs.NewValueInvalidError("description")
	}

	if len(strings.TrimSpace(url)) == 0 {
		return nil, pkgerrs.NewValueRequiredError("url")
	}
	if !pkgutils.StrWithinRange(url, minURLLen, maxURLLen, true) {
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
		id:              uuid.New(),
		externalID:      externalID,
		source:          source,
		title:           title,
		company:         company,
		salary:          salary,
		grade:           grade,
		employmentTypes: eTypes,
		location:        location,
		description:     description,
		url:             url,
		publishedAt:     publishedAt,
		parsedAt:        parsedAt,
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
	employmentTypes []EmploymentType,
	location *Location,
	description, url string,
	publishedAt, parsedAt time.Time,
) *Vacancy {
	var eTypes []EmploymentType
	if employmentTypes != nil {
		eTypes = make([]EmploymentType, len(employmentTypes))
		copy(eTypes, employmentTypes)
	}

	return &Vacancy{
		id:              id,
		externalID:      externalID,
		source:          source,
		title:           title,
		company:         company,
		salary:          salary,
		grade:           grade,
		employmentTypes: eTypes,
		location:        location,
		description:     description,
		url:             url,
		publishedAt:     publishedAt,
		parsedAt:        parsedAt,
	}
}

// ======================== Read-Only ========================

func (v *Vacancy) ID() uuid.UUID         { return v.id }
func (v *Vacancy) ExternalID() string    { return v.externalID }
func (v *Vacancy) Source() VacancySource { return v.source }
func (v *Vacancy) Title() string         { return v.title }
func (v *Vacancy) Company() *string      { return v.company }
func (v *Vacancy) Salary() *Salary       { return v.salary }
func (v *Vacancy) Grade() Grade          { return v.grade }
func (v *Vacancy) EmploymentTypes() []EmploymentType {
	if v.employmentTypes == nil {
		return nil
	}
	res := make([]EmploymentType, len(v.employmentTypes))
	copy(res, v.employmentTypes)
	return res
}
func (v *Vacancy) Location() *Location    { return v.location }
func (v *Vacancy) Description() string    { return v.description }
func (v *Vacancy) URL() string            { return v.url }
func (v *Vacancy) PublishedAt() time.Time { return v.publishedAt }
func (v *Vacancy) ParsedAt() time.Time    { return v.parsedAt }

// ================ Business Logic ================

func (v *Vacancy) FromHH() bool       { return v.source == SourceHH }
func (v *Vacancy) FromTelegram() bool { return v.source == SourceTelegram }
func (v *Vacancy) FromOzon() bool     { return v.source == SourceOzon }

func (v *Vacancy) IsExpired() bool {
	return time.Since(v.publishedAt) > vacancyValidUpTo
}
func (v *Vacancy) IsPublishedAfter(after time.Time) bool {
	return v.publishedAt.After(after)
}

func (v *Vacancy) MatchBySalary(salary *int, currency *string) (bool, error) {
	if salary == nil {
		if currency == nil { // filter isn't specified -> true
			return true, nil
		}
		return false, ErrCurrencyWithoutSalary // domain error
	}

	if *salary < minSalaryVal || *salary > maxSalaryVal {
		return false, pkgerrs.NewValueInvalidError("salary")
	}

	if currency == nil { // domain error
		return false, ErrSalaryRequiresCurrency
	}

	if !pkgutils.StrWithinRange(*currency, minCurrencyLen, maxCurrencyLen, false) {
		return false, pkgerrs.NewValueInvalidError("currency")
	}

	if v.salary == nil {
		return true, nil
	}

	return v.salary.Match(*salary, *currency)
}

func (v *Vacancy) MatchByGrade(grade Grade) bool {
	return v.grade == grade
}

func (v *Vacancy) MatchByEmploymentTypes(eTypes []EmploymentType) bool {
	if len(eTypes) == 0 {
		return true
	}
	for _, eType := range eTypes {
		for _, vacancyEType := range v.employmentTypes {
			if eType == vacancyEType {
				return true
			}
		}
	}
	return false
}

func (v *Vacancy) MatchByLocation(country, city *string) (bool, error) {
	if country == nil && city == nil { // nothing is specified - true
		return true, nil
	}

	if country == nil { // domain error: city cannot be specified without country
		return false, ErrCityWithoutCountry
	}

	if !pkgutils.StrWithinRange(*country, minLocCountryLen, maxLocCountryLen, true) {
		return false, pkgerrs.NewValueInvalidError("country")
	}

	if city != nil && !pkgutils.StrWithinRange(*city, minLocCityLen, maxLocCityLen, true) {
		return false, pkgerrs.NewValueInvalidError("city")
	}

	if v.location == nil { // vacancy has no location filters - true
		return true, nil
	}

	return v.location.Match(*country, city)
}
