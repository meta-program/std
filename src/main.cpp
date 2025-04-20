#include <iostream>
#include "hash/RabinKarp.h"

using namespace std;
int main() {
    // Raw String Literal
    string text = R"(这是一篇陈词滥调的文章[1]。This is a clichéd article [2]. C’est un article plein de clichés [3].
这是一篇陈词滥调的文章[4]。C’est un article plein de clichés [6]. This is a clichéd article [5].
C’est un article plein de clichés [9]. 这是一篇陈词滥调的文章[7]。This is a clichéd article [8].
C’est un article plein de clichés [9]. This is a clichéd article [8]. 这是一篇陈词滥调的文章[7]。
This is a clichéd article [8]. C’est un article plein de clichés [9]. 这是一篇陈词滥调的文章[7]。
This is a clichéd article [8]. 这是一篇陈词滥调的文章[7]。C’est un article plein de clichés [9].
)";
    // Detect redundant patterns in the text
    for (auto &[scan_length, hashCode, indices]: RabinKarp(text).redundancy_detect()) {
        int start = indices[0];
        auto error = text.substr(indices[0], scan_length);
        vector<string> slices;
        for (int start : indices) {
            auto end = start + scan_length;
            slices.push_back("text[" + to_string(start) + ":" + to_string(end) + "]");
        }
        print(
            "length =", scan_length, 
            "count =", indices.size(), 
            join(" = ", slices), "=",
            json_encode(error)
        );
    }

    return 0;
}