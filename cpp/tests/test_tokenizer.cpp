#include "tokenizer.h"
#include <cassert>
#include <iostream>

int main(){
    auto v = tokenize("hello world  test");
    assert(v.size()==3);
    assert(v[0]=="hello");
    assert(v[1]=="world");
    assert(v[2]=="test");
    std::cout<<"tokenizer tests passed"<<std::endl;
    return 0;
}
