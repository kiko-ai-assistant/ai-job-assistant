package dto

import "time"

type ErrorResponse struct {
	Error string `json:"error"`
}

type SalaryDTO struct {
	Text     *string `json:"text"`
	From     *int    `json:"from"`
	To       *int    `json:"to"`
	Currency *string `json:"currency"`
}

type LocationDTO struct {
	Text    *string `json:"text"`
	Country *string `json:"country"`
	City    *string `json:"city"`
}

type VacancyRequest struct {
	ExternalID      string       `json:"external_id"`
	Source          string       `json:"source"`
	Title           string       `json:"title"`
	Company         *string      `json:"company"`
	Salary          *SalaryDTO   `json:"salary"`
	Grade           string       `json:"grade"`
	EmploymentTypes []string     `json:"employment_types"`
	Location        *LocationDTO `json:"location"`
	Description     string       `json:"description"`
	URL             string       `json:"url"`
	PublishedAt     time.Time    `json:"published_at"`
	ParsedAt        time.Time    `json:"parsed_at"`
}

type VacancyResponse struct {
	ID              string       `json:"id"`
	ExternalID      string       `json:"external_id"`
	Source          string       `json:"source"`
	Title           string       `json:"title"`
	Company         *string      `json:"company"`
	Salary          *SalaryDTO   `json:"salary"`
	Grade           string       `json:"grade"`
	EmploymentTypes []string     `json:"employment_types"`
	Location        *LocationDTO `json:"location"`
	Description     string       `json:"description"`
	URL             string       `json:"url"`
	PublishedAt     time.Time    `json:"published_at"`
	ParsedAt        time.Time    `json:"parsed_at"`
}
