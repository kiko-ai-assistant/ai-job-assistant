package errs

import (
	"errors"
)

var (
	ErrInvalidInput         = errors.New("invalid input")
	ErrCreateVacancyDB      = errors.New("failed to create vacancy using db")
	ErrVacancyAlreadyExists = errors.New("vacancy with given external id already exists")
)
