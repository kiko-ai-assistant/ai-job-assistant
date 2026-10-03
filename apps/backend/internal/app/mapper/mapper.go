package mapper

import (
	"ai-job-assistant/backend/internal/app/dto"
	"ai-job-assistant/backend/internal/domain/model"
	"ai-job-assistant/backend/internal/domain/port"
)

func toSalaryDomain(d *dto.SalaryDTO) (*model.Salary, error) {
	if d == nil {
		return nil, nil
	}
	return model.NewSalary(d.Text, d.From, d.To, d.Currency)
}

func toSalaryDTO(s *model.Salary) dto.SalaryDTO {
	if s == nil {
		return dto.SalaryDTO{}
	}
	return dto.SalaryDTO{
		Text:     s.Text(),
		From:     s.From(),
		To:       s.To(),
		Currency: s.Currency(),
	}
}

func toLocationDomain(d *dto.LocationDTO) (*model.Location, error) {
	if d == nil {
		return nil, nil
	}
	return model.NewLocation(d.Text, d.Country, d.City)
}

func toLocationDTO(l *model.Location) dto.LocationDTO {
	if l == nil {
		return dto.LocationDTO{}
	}
	return dto.LocationDTO{
		Text:    l.Text(),
		Country: l.Country(),
		City:    l.City(),
	}
}

func toEmploymentTypesStrings(types []model.EmploymentType) []string {
	if types == nil {
		return nil
	}
	res := make([]string, len(types))
	for i, t := range types {
		res[i] = t.String()
	}
	return res
}

func ToVacancyDomain(in dto.CreateVacancyInput) (*model.Vacancy, error) {
	salary, err := toSalaryDomain(in.Salary)
	if err != nil {
		return nil, err
	}

	location, err := toLocationDomain(in.Location)
	if err != nil {
		return nil, err
	}

	return model.NewVacancy(
		in.ExternalID,
		in.Source,
		in.Title,
		in.Company,
		salary,
		in.Grade,
		in.EmploymentTypes,
		location,
		in.Description,
		in.URL,
		in.PublishedAt,
		in.ParsedAt,
	)
}

func VacancyDTOToDomain(d dto.VacancyDTO) (*model.Vacancy, error) {
	salary, err := toSalaryDomain(&d.Salary)
	if err != nil {
		return nil, err
	}

	location, err := toLocationDomain(&d.Location)
	if err != nil {
		return nil, err
	}

	return model.NewVacancy(
		d.ExternalID,
		d.Source,
		d.Title,
		d.Company,
		salary,
		d.Grade,
		d.EmploymentTypes,
		location,
		d.Description,
		d.URL,
		d.PublishedAt,
		d.ParsedAt,
	)
}

func ToVacanciesDomain(items []dto.VacancyDTO) ([]*model.Vacancy, error) {
	if items == nil {
		return nil, nil
	}
	vacancies := make([]*model.Vacancy, len(items))
	for i, item := range items {
		v, err := VacancyDTOToDomain(item)
		if err != nil {
			return nil, err
		}
		vacancies[i] = v
	}
	return vacancies, nil
}

func ToVacancyDTO(v *model.Vacancy) *dto.VacancyDTO {
	if v == nil {
		return nil
	}
	return &dto.VacancyDTO{
		ID:              v.ID(),
		ExternalID:      v.ExternalID(),
		Source:          v.Source().String(),
		Title:           v.Title(),
		Company:         v.Company(),
		Salary:          toSalaryDTO(v.Salary()),
		Grade:           v.Grade().String(),
		EmploymentTypes: toEmploymentTypesStrings(v.EmploymentTypes()),
		Location:        toLocationDTO(v.Location()),
		Description:     v.Description(),
		URL:             v.URL(),
		PublishedAt:     v.PublishedAt(),
		ParsedAt:        v.ParsedAt(),
	}
}

func ToCreateVacancyOutput(v *model.Vacancy) *dto.CreateVacancyOutput {
	if v == nil {
		return nil
	}
	res := dto.CreateVacancyOutput(*ToVacancyDTO(v))
	return &res
}

func ToInsertVacanciesOutput(res port.CreateManyResult) *dto.InsertVacanciesOutput {
	return &dto.InsertVacanciesOutput{
		Inserted: res.Inserted,
		Ignored:  res.Ignored,
	}
}

func ToGetVacancyOutput(v *model.Vacancy) *dto.GetVacancyOutput {
	if v == nil {
		return nil
	}
	res := dto.GetVacancyOutput(*ToVacancyDTO(v))
	return &res
}
