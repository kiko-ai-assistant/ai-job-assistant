package model

import (
	"time"

	pkgerrs "ai-job-assistant/backend/pkg/errs"

	"github.com/google/uuid"
)

// ================ Rich model of CV ================

type CV struct {
	id        uuid.UUID
	userID    uuid.UUID
	fileID    string
	path      string
	createdAt time.Time
	updatedAt time.Time
}

func NewCV(userID uuid.UUID, fileID, path string) (*CV, error) {
	if userID == uuid.Nil {
		return nil, pkgerrs.NewValueRequiredError("user_id")
	}
	if fileID == "" {
		return nil, pkgerrs.NewValueRequiredError("file_id")
	}
	if path == "" {
		return nil, pkgerrs.NewValueRequiredError("path")
	}

	now := time.Now().UTC()

	return &CV{
		id:        uuid.New(),
		userID:    userID,
		fileID:    fileID,
		path:      path,
		createdAt: now,
		updatedAt: now,
	}, nil
}

func RestoreCV(
	id, userID uuid.UUID,
	fileID, path string,
	createdAt, updatedAt time.Time,
) *CV {
	return &CV{
		id:        id,
		userID:    userID,
		fileID:    fileID,
		path:      path,
		createdAt: createdAt,
		updatedAt: updatedAt,
	}
}

// ================ Read-Only ================

func (cv *CV) ID() uuid.UUID        { return cv.id }
func (cv *CV) UserID() uuid.UUID    { return cv.userID }
func (cv *CV) FileID() string       { return cv.fileID }
func (cv *CV) Path() string         { return cv.path }
func (cv *CV) CreatedAt() time.Time { return cv.createdAt }
func (cv *CV) UpdatedAt() time.Time { return cv.updatedAt }

// ================ Mutation ================

func (cv *CV) Update(fileID, path string) error {
	if fileID == "" {
		return pkgerrs.NewValueRequiredError("file_id")
	}
	if path == "" {
		return pkgerrs.NewValueRequiredError("path")
	}

	cv.fileID = fileID
	cv.path = path
	cv.updatedAt = time.Now().UTC()

	return nil
}
