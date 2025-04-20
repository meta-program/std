#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "../../src/hash/RabinKarp.h"
namespace py = pybind11;
using namespace std;

double length_coefficient(int length, int count)
{
    // in the range of [0, 1]
    return (1 + tanh(0.4 * length - 14 + count)) / 2;
}

bool isMarkdownSpecial(const string &str)
{
    for (char c : str)
    {
        switch (c)
        {
        case '\n':
        case ' ':
        case '-':
        case '*':
            break;
        default:
            return false;
        }
    }
    return true;
}

py::dict repetition_penalty(py::str py_str)
{
    // Convert Python str to UTF-8 encoded string
    string text = py_str.cast<string>();
    // Detect redundant patterns in the text
    int score = 0;
    py::list list;
    for (auto &[scan_length, hashCode, indices] : RabinKarp(text).redundancy_detect())
    {
        auto error = text.substr(indices[0], scan_length);
        if (isMarkdownSpecial(error)) 
            continue;
        int count = indices.size();
        error = strip_malformed_utf8(error);
        int length = error.size();
        int peanlty = length_coefficient(length, count) * (max(length - 64, 0) + (pow(count - 2, 2)));
        if (peanlty) {
            py::dict obj;
            obj["error"] = error;
            obj["count"] = count;
            score += peanlty;
            list.append(obj);
        }
    }
    py::dict obj;
    obj["score"] = -min(score, 1024);
    obj["list"] = list;
    return obj;
}

// Binding the function to Python
PYBIND11_MODULE(rabin_karp, m)
{
    m.def("repetition_penalty", &repetition_penalty);
}