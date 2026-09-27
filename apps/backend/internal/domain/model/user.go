package model

import (
	pkgerrs "ai-job-assistant/backend/pkg/errs"
	"time"

	"github.com/google/uuid"
)

type InterfaceLang string

const (
	LanguageEnglish = "EN"
	LanguageChinese = "CN"
	LanguageRussian = "RU"

	LanguageDefault = LanguageEnglish
)

func (l InterfaceLang) String() string { return string(l) }

func (l InterfaceLang) IsValid() bool {
	if l == LanguageEnglish || l == LanguageChinese ||
		l == LanguageRussian {
		return true
	}
	return false
}

// ================ Rich model for User ================

type User struct {
	id         uuid.UUID
	telegramID int64
	username   *string
	firstName  *string
	lastName   *string
	language   InterfaceLang
	cv         *CV
	createdAt  time.Time
	updatedAt  time.Time
}

func NewUser(
	telegramID int64,
	username, fName, lName, language *string,
	cv *CV,
) (*User, error) {
	if telegramID < 0 {
		return nil, pkgerrs.NewValueInvalidError("telegram_id")
	}

	if username != nil && len(*username) == 0 {
		return nil, pkgerrs.NewValueInvalidError("username")
	}
	if fName != nil && len(*fName) == 0 {
		return nil, pkgerrs.NewValueInvalidError("first_name")
	}
	if lName != nil && len(*lName) == 0 {
		return nil, pkgerrs.NewValueInvalidError("last_name")
	}

	var lang InterfaceLang = LanguageDefault
	if language != nil {
		lang = InterfaceLang(*language)
		if !lang.IsValid() {
			return nil, pkgerrs.NewValueInvalidError("language")
		}
	}

	now := time.Now().UTC()

	return &User{
		id:         uuid.New(),
		telegramID: telegramID,
		username:   username,
		firstName:  fName,
		lastName:   lName,
		language:   lang,
		cv:         cv,
		createdAt:  now,
		updatedAt:  now,
	}, nil
}

func RestoreUser(
	id uuid.UUID, telegramID int64,
	username, firstName, lastName *string,
	language InterfaceLang,
	cv *CV,
	createdAt, updatedAt time.Time,
) *User {
	return &User{
		id:         id,
		telegramID: telegramID,
		username:   username,
		firstName:  firstName,
		lastName:   lastName,
		language:   language,
		cv:         cv,
		createdAt:  createdAt,
		updatedAt:  updatedAt,
	}
}
