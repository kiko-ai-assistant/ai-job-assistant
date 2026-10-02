package model

import (
	pkgutils "ai-job-assistant/backend/pkg/utils"
	"testing"
	"time"

	"github.com/google/uuid"
)

func TestLocation_Match(t *testing.T) {
	locRussiaMoscow, err := NewLocation(pkgutils.VPtr("Russia, Moscow office"), pkgutils.VPtr("Russia"), pkgutils.VPtr("Moscow"))
	if err != nil {
		t.Fatalf("failed to create location: %v", err)
	}

	locRussiaKazan, err := NewLocation(pkgutils.VPtr("Russia, Kazan office"), pkgutils.VPtr("Russia"), pkgutils.VPtr("Kazan"))
	if err != nil {
		t.Fatalf("failed to create location: %v", err)
	}

	locUSASaintPetersburg, err := NewLocation(pkgutils.VPtr("USA, Florida office"), pkgutils.VPtr("USA"), pkgutils.VPtr("Saint Petersburg"))
	if err != nil {
		t.Fatalf("failed to create location: %v", err)
	}

	locRussiaNoCity, err := NewLocation(pkgutils.VPtr("Remote in Russia"), pkgutils.VPtr("Russia"), nil)
	if err != nil {
		t.Fatalf("failed to create location: %v", err)
	}

	tests := []struct {
		name        string
		loc         *Location
		country     string
		city        *string
		wantMatch   bool
		wantErr     bool
		expectedErr error
	}{
		{
			name:      "nil location receiver -> matches any country/city",
			loc:       nil,
			country:   "Russia",
			city:      pkgutils.VPtr("Moscow"),
			wantMatch: true,
			wantErr:   false,
		},
		{
			name:      "same country and same city -> match",
			loc:       locRussiaMoscow,
			country:   "Russia",
			city:      pkgutils.VPtr("Moscow"),
			wantMatch: true,
			wantErr:   false,
		},
		{
			name:      "case insensitive match -> match",
			loc:       locRussiaMoscow,
			country:   "russia",
			city:      pkgutils.VPtr("moscow"),
			wantMatch: true,
			wantErr:   false,
		},
		{
			name:      "same city name but different country -> no match",
			loc:       locUSASaintPetersburg,
			country:   "Russia",
			city:      pkgutils.VPtr("Saint Petersburg"),
			wantMatch: false,
			wantErr:   false,
		},
		{
			name:      "same country but different city -> no match",
			loc:       locRussiaKazan,
			country:   "Russia",
			city:      pkgutils.VPtr("Moscow"),
			wantMatch: false,
			wantErr:   false,
		},
		{
			name:      "country matches and city is nil -> match",
			loc:       locRussiaKazan,
			country:   "Russia",
			city:      nil,
			wantMatch: true,
			wantErr:   false,
		},
		{
			name:      "country does not match -> no match",
			loc:       locRussiaKazan,
			country:   "Germany",
			city:      nil,
			wantMatch: false,
			wantErr:   false,
		},
		{
			name:      "city requested but vacancy has no city -> no match",
			loc:       locRussiaNoCity,
			country:   "Russia",
			city:      pkgutils.VPtr("Moscow"),
			wantMatch: false,
			wantErr:   false,
		},
		{
			name:        "invalid country length -> error",
			loc:         locRussiaMoscow,
			country:     "R",
			city:        nil,
			wantMatch:   false,
			wantErr:     true,
			expectedErr: nil,
		},
		{
			name:        "invalid city length -> error",
			loc:         locRussiaMoscow,
			country:     "Russia",
			city:        pkgutils.VPtr("M"),
			wantMatch:   false,
			wantErr:     true,
			expectedErr: nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotMatch, err := tt.loc.Match(tt.country, tt.city)
			if (err != nil) != tt.wantErr {
				t.Errorf("Location.Match() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if tt.expectedErr != nil && err != tt.expectedErr {
				t.Errorf("Location.Match() error = %v, want %v", err, tt.expectedErr)
			}
			if gotMatch != tt.wantMatch {
				t.Errorf("Location.Match() gotMatch = %v, wantMatch %v", gotMatch, tt.wantMatch)
			}
		})
	}
}

func TestVacancy_MatchByLocation(t *testing.T) {
	loc, err := NewLocation(pkgutils.VPtr("Russia, Moscow office"), pkgutils.VPtr("Russia"), pkgutils.VPtr("Moscow"))
	if err != nil {
		t.Fatalf("failed to create location: %v", err)
	}

	vacWithLoc := RestoreVacancy(
		uuid.New(), "ext1", SourceHH, "Go Developer", nil, nil,
		GradeMiddle, EmploymentRemote, loc, "Description text description text description...",
		"https://example.com/vac", time.Now(), time.Now(),
	)

	vacWithoutLoc := RestoreVacancy(
		uuid.New(), "ext2", SourceHH, "Go Developer", nil, nil,
		GradeMiddle, EmploymentRemote, nil, "Description text description text description...",
		"https://example.com/vac", time.Now(), time.Now(),
	)

	tests := []struct {
		name        string
		vac         *Vacancy
		userCountry *string
		userCity    *string
		wantMatch   bool
		wantErr     bool
		expectedErr error
	}{
		{
			name:        "nil location on vacancy -> matches any location filter",
			vac:         vacWithoutLoc,
			userCountry: pkgutils.VPtr("Russia"),
			userCity:    pkgutils.VPtr("Moscow"),
			wantMatch:   true,
			wantErr:     false,
		},
		{
			name:        "nil user filter on vacancy with location -> matches",
			vac:         vacWithLoc,
			userCountry: nil,
			userCity:    nil,
			wantMatch:   true,
			wantErr:     false,
		},
		{
			name:        "matching country and city -> match",
			vac:         vacWithLoc,
			userCountry: pkgutils.VPtr("Russia"),
			userCity:    pkgutils.VPtr("Moscow"),
			wantMatch:   true,
			wantErr:     false,
		},
		{
			name:        "different city -> no match",
			vac:         vacWithLoc,
			userCountry: pkgutils.VPtr("Russia"),
			userCity:    pkgutils.VPtr("Kazan"),
			wantMatch:   false,
			wantErr:     false,
		},
		{
			name:        "city without country -> error ErrCityWithoutCountry",
			vac:         vacWithLoc,
			userCountry: nil,
			userCity:    pkgutils.VPtr("Moscow"),
			wantMatch:   false,
			wantErr:     true,
			expectedErr: ErrCityWithoutCountry,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotMatch, err := tt.vac.MatchByLocation(tt.userCountry, tt.userCity)
			if (err != nil) != tt.wantErr {
				t.Errorf("Vacancy.MatchByLocation() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if tt.expectedErr != nil && err != tt.expectedErr {
				t.Errorf("Vacancy.MatchByLocation() error = %v, want %v", err, tt.expectedErr)
			}
			if gotMatch != tt.wantMatch {
				t.Errorf("Vacancy.MatchByLocation() gotMatch = %v, wantMatch %v", gotMatch, tt.wantMatch)
			}
		})
	}
}
