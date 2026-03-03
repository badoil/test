#pragma once
#include <string>
#include <vector>

// Simple whitespace tokenizer
//
// Purpose:
//   Lightweight tokenizer that splits an input string on ASCII whitespace
//   (spaces, tabs, newlines). This implementation is intentionally small to
//   teach string handling and I/O in C++.
//
// API:
//   std::vector<std::string> tokenize(const std::string& s);
//
// Inputs:
//   - s: input string (UTF-8 encoded bytes are accepted; this tokenizer
//        treats the byte sequence and splits on ASCII whitespace only.)
//
// Output:
//   - vector of token strings (in insertion order). Consecutive whitespace is
//     collapsed and does not produce empty tokens. Leading/trailing whitespace
//     is ignored.
//
// Complexity:
//   - Time: O(n) where n is the length of the input string (single pass)
//   - Space: O(t + n) where t is total token count overhead + copied substrings
//
// Example:
//   auto v = tokenize("  hello  world\nthis is\ta test  ");
//   // v == {"hello","world","this","is","a","test"}
//
// Notes / Learning points:
//   - This tokenizer is UTF-8 "byte-safe" but not Unicode-aware: multi-byte
//     codepoints will be preserved inside tokens but punctuation and script
//     boundaries are not treated specially.
//   - Later exercises will extend this to handle punctuation, Unicode
//     normalization, and custom tokenization rules.

std::vector<std::string> tokenize(const std::string& s);
