package errs

import (
	"errors"
	"testing"

	"github.com/brianvoe/gofakeit/v7"
	"github.com/stretchr/testify/assert"
)

func TestWrappedError(t *testing.T) {
	tests := []struct {
		name       string
		publicErr  error
		reasonErr  error
		wantError  string
		wantUnwrap error
	}{
		{
			name:       "wrap public and reason errors",
			publicErr:  errors.New(gofakeit.ProductName()),
			reasonErr:  errors.New(gofakeit.ProductName()),
			wantError:  "",
			wantUnwrap: nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			w := Wrap(tt.publicErr, tt.reasonErr)
			assert.NotNil(t, w)
			assert.Equal(t, tt.publicErr.Error(), w.Error())

			var wrapped *WrappedError
			assert.True(t, errors.As(w, &wrapped))
			assert.Equal(t, tt.publicErr, wrapped.Unwrap())
			assert.Equal(t, tt.reasonErr, wrapped.Reason)
		})
	}
}
