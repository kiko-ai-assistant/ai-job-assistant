package mapper

import (
	"ai-job-assistant/backend/internal/adapter/out/postgres/sqlc"
	"ai-job-assistant/backend/internal/domain/model"
	pkgutils "ai-job-assistant/backend/pkg/utils"
	"strings"

	"github.com/jackc/pgx/v5/pgtype"
)

func ToSQLCCreate(vacancy *model.Vacancy) sqlc.CreateVacancyParams {
	if vacancy == nil {
		return sqlc.CreateVacancyParams{}
	}

	var (
		company, salary, currency, loc, country, city pgtype.Text
		salaryFrom, salaryTo                          pgtype.Int4
	)

	if vacancy.HasCompany() {
		company = pgtype.Text{String: *vacancy.Company(), Valid: true}
	}

	if vacancy.HasSalary() {
		if vacancy.Salary().HasText() {
			salary = pgtype.Text{String: *vacancy.Salary().Text(), Valid: true}
		}
		if vacancy.Salary().HasLeftBound() {
			salaryFrom = pgtype.Int4{
				Int32: int32(*vacancy.Salary().From()),
				Valid: true,
			}
		}
		if vacancy.Salary().HasRightBound() {
			salaryTo = pgtype.Int4{
				Int32: int32(*vacancy.Salary().To()),
				Valid: true,
			}
		}
		if vacancy.Salary().HasCurrency() {
			currency = pgtype.Text{
				String: *vacancy.Salary().Currency(),
				Valid:  true,
			}
		}
	}

	eTypes := make([]sqlc.EmploymentType, 0, len(vacancy.EmploymentTypes()))
	for _, rawEType := range vacancy.EmploymentTypes() {
		eType := sqlc.EmploymentType(rawEType)
		eTypes = append(eTypes, eType)
	}

	if vacancy.HasLocation() {
		if vacancy.Location().HasText() {
			loc = pgtype.Text{String: *vacancy.Location().Text(), Valid: true}
		}
		if vacancy.Location().HasCountry() {
			country = pgtype.Text{
				String: *vacancy.Location().Country(),
				Valid:  true,
			}
		}
		if vacancy.Location().HasCity() {
			city = pgtype.Text{
				String: *vacancy.Location().City(),
				Valid:  true,
			}
		}
	}

	return sqlc.CreateVacancyParams{
		ID:              vacancy.ID(),
		ExternalID:      vacancy.ExternalID(),
		Source:          vacancy.Source().String(),
		Title:           vacancy.Title(),
		Company:         company,
		SalaryText:      salary,
		SalaryFrom:      salaryFrom,
		SalaryTo:        salaryTo,
		Currency:        currency,
		Grade:           sqlc.Grade(vacancy.Grade()),
		EmploymentTypes: eTypes,
		LocationText:    loc,
		Country:         country,
		City:            city,
		Description:     vacancy.Description(),
		Url:             vacancy.URL(),
		PublishedAt:     vacancy.PublishedAt(),
		ParsedAt:        vacancy.ParsedAt(),
	}
}

func ToSQLCCreateMany(vacancies []*model.Vacancy) []sqlc.CreateManyVacanciesParams {
	if vacancies == nil {
		return nil
	}

	result := make([]sqlc.CreateManyVacanciesParams, 0, len(vacancies))
	for _, v := range vacancies {
		p := ToSQLCCreate(v)
		result = append(result, sqlc.CreateManyVacanciesParams{
			ID:              p.ID,
			ExternalID:      p.ExternalID,
			Source:          p.Source,
			Title:           p.Title,
			Company:         p.Company,
			SalaryText:      p.SalaryText,
			SalaryFrom:      p.SalaryFrom,
			SalaryTo:        p.SalaryTo,
			Currency:        p.Currency,
			Grade:           p.Grade,
			EmploymentTypes: p.EmploymentTypes,
			LocationText:    p.LocationText,
			Country:         p.Country,
			City:            p.City,
			Description:     p.Description,
			Url:             p.Url,
			PublishedAt:     p.PublishedAt,
			ParsedAt:        p.ParsedAt,
		})
	}

	return result
}

func ToDomainVacancy(raw sqlc.Vacancy) *model.Vacancy {
	var (
		company, salary, currency, loc, country, city *string
		salaryFrom, salaryTo                          *int
	)

	if raw.Company.Valid {
		company = &raw.Company.String
	}
	if raw.SalaryText.Valid {
		salary = &raw.SalaryText.String
	}
	if raw.SalaryFrom.Valid {
		salaryFrom = pkgutils.VPtr(int(raw.SalaryFrom.Int32))
	}
	if raw.SalaryTo.Valid {
		salaryTo = pkgutils.VPtr(int(raw.SalaryTo.Int32))
	}
	if raw.Currency.Valid {
		currency = &raw.Currency.String
	}

	eTypes := make([]model.EmploymentType, 0, len(raw.EmploymentTypes))
	for _, rawEType := range raw.EmploymentTypes {
		eType := model.EmploymentType(strings.ToLower(string(rawEType)))
		eTypes = append(eTypes, eType)
	}

	if raw.LocationText.Valid {
		loc = &raw.LocationText.String
	}
	if raw.Country.Valid {
		country = &raw.Country.String
	}
	if raw.City.Valid {
		city = &raw.City.String
	}

	return model.RestoreVacancy(
		raw.ID,
		raw.ExternalID,
		model.VacancySource(strings.ToLower(raw.Source)),
		raw.Title,
		company,
		model.RestoreSalary(salary, salaryFrom, salaryTo, currency),
		model.Grade(strings.ToLower(string(raw.Grade))),
		eTypes,
		model.RestoreLocation(loc, country, city),
		raw.Description,
		raw.Url,
		raw.PublishedAt,
		raw.ParsedAt,
	)
}

func ToDomainVacancies(rawList []sqlc.Vacancy) []*model.Vacancy {
	if rawList == nil {
		return nil
	}

	result := make([]*model.Vacancy, 0, len(rawList))
	for _, raw := range rawList {
		result = append(result, ToDomainVacancy(raw))
	}

	return result
}
