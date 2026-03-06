#define CATCH_CONFIG_MAIN
#include <catch2/catch.hpp>
#include "tokenizer.h"

TEST_CASE("basic tokenization", "[tokenize]"){
    auto v = tokenize("hello world  test");
    REQUIRE(v.size()==3);
    REQUIRE(v[0]=="hello");
    REQUIRE(v[1]=="world");
    REQUIRE(v[2]=="test");
}

TEST_CASE("lead and trail whitespace", "[tokenize]"){
    auto v = tokenize("  lead and trail  ");
    REQUIRE(v==std::vector<std::string>{"lead","and","trail"});
}

TEST_CASE("empty input", "[tokenize]"){
    auto v = tokenize("");
    REQUIRE(v.empty());
}

TEST_CASE("tabs and newlines", "[tokenize]"){
    auto v = tokenize("multiple\twhitespace\nseparators");
    REQUIRE(v==std::vector<std::string>{"multiple","whitespace","separators"});
}

TEST_CASE("punctuation preserved", "[tokenize]"){
    auto v = tokenize("hello,world! test.");
    REQUIRE(v==std::vector<std::string>{"hello,world!","test."});
}

TEST_CASE("unicode multibyte tokens", "[tokenize]"){
    auto v = tokenize("안녕 세계");
    REQUIRE(v==std::vector<std::string>{"안녕","세계"});
}
