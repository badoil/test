#include "tokenizer.h"
#include <sstream>

std::vector<std::string> tokenize(const std::string& s){
    std::istringstream iss(s);
    std::vector<std::string> out;
    std::string tok;
    while(iss >> tok) out.push_back(tok);
    return out;
}
