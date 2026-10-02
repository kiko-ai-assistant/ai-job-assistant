package errs

import (
	"errors"
)

/*
================ Invalidation & Conflicts ================
*/
var (
	ErrInvalidInput = errors.New("invalid input")
)

/*
================ Postgres failures ================
*/
var (
	ErrCreateMenuCategoryDB = errors.New("failed to create menu category using db")
	ErrGetMenuCategoryDB    = errors.New("failed to get menu category using db")
	ErrUpdateMenuCategoryDB = errors.New("failed to update menu category using db")
	ErrListMenuCategoriesDB = errors.New("failed to get a list of categories using db")

	ErrCreateVacancyDB       = errors.New("failed to create vacancy using db")
	ErrCreateManyVacanciesDB = errors.New("failed to create many vacancies using db")
	ErrGetVacancyDB          = errors.New("failed to get vacancy using db")
	ErrListVacanciesDB       = errors.New("failed to get a list of vacancies using db")

	ErrCreateOrderDB        = errors.New("failed to create order using db")
	ErrGetOrderDB           = errors.New("failed to get order using db")
	ErrUpdateOrderDB        = errors.New("failed to update order using db")
	ErrListOrdersByStatusDB = errors.New("failed to get a list of orders by status using db")

	ErrCreateOrderStatusHistoryDB  = errors.New("failed to create order status history using db")
	ErrMenuItemNotFound            = errors.New("menu item not found")
	ErrOrderNotFound               = errors.New("order not found")
	ErrRestaurantNotFound          = errors.New("restaurant not found")
	ErrGetRestaurantByApiKeyHashDB = errors.New("failed to get restaurant by api key hash using db")
	ErrCreateRestaurantDB          = errors.New("failed to create restaurant using db")
	ErrGenerateAPIKey              = errors.New("failed to generate api key")

	ErrVacancyAlreadyExists = errors.New("vacancy with given external id already exists")
)
