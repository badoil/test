cmake_minimum_required(VERSION 3.16)

include(FetchContent)
FetchContent_Declare(
  catch2
  GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG v3.4.0
)
FetchContent_MakeAvailable(catch2)

add_executable(test_tokenizer test_tokenizer.cpp)
target_link_libraries(test_tokenizer PRIVATE javi_core Catch2::Catch2WithMain)
add_test(NAME tokenizer_test COMMAND test_tokenizer)
