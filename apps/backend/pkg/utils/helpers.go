package utils

import (
	"crypto/sha256"
	"encoding/hex"
	"unicode/utf8"
)

func VPtr[T any](v T) *T {
	return &v
}

func ComparePtr[T comparable](s1, s2 *T) bool {
	var v1, v2 T
	if s1 != nil {
		v1 = *s1
	}
	if s2 != nil {
		v2 = *s2
	}

	return v1 == v2
}

func StrWithinRange(s string, left, right int, utf bool) bool {
	sLen := len(s)
	if utf {
		sLen = utf8.RuneCountInString(s)
	}
	return sLen >= left && sLen <= right
}

func IntWithinRange()

func HashToken(token string) string {
	hash := sha256.Sum256([]byte(token))
	return hex.EncodeToString(hash[:])
}
