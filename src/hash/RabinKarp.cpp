#include <string.h>
#include <cmath>
#include <algorithm>
#include <iostream>
#include "RabinKarp.h"
using namespace std;

RabinKarp::RabinKarp(const string &text, int scan_length) : text(text),
                                                            scan_length(scan_length),
                                                            // in theory, hashCode.size() = text.size() - scan_length + 1, but to prevent out of bound error, I delibrately set it to be text.size() - scan_length + 2
                                                            hashCode(max((int)text.size() - scan_length + 2, 0))
{
}

void RabinKarp::rolling_hash(HashCode &window_hash, const HashCode &h, int i) const
{
    if (i + scan_length < text.size())
        window_hash = HashCode(window_hash - (h * text[i]), text[i + scan_length]);
}

bool RabinKarp::matches(int i, int j, int scan_length) const
{
    return !strncmp(&text[i], &text[j], scan_length);
}

vector<Matches> RabinKarp::initial_detect()
{
    int n = text.size();
    if (n < scan_length)
        return {};

    unordered_map<hash_t, vector<vector<int>>> hashDict;
    // Compute the hash of the pattern and the first window in the text
    HashCode window_hash(text, scan_length);
    auto h = HashCode().shl(scan_length - 1);

    // Slide the window over the text
    for (int i = 0; i <= n - scan_length; ++i)
    {
        hash_t hash = window_hash.hash;
        // cache the hash code for later processing
        hashCode[i] = window_hash;
        if (hashDict.find(hash) == hashDict.end())
            hashDict.insert({hash, {{i}}});
        else
        {
            auto &lists = hashDict[hash];
            bool notfound = true;
            for (auto &list : lists)
            {
                // check the 0th element of the list only, because the rest of the elements are the same
                if (matches(list[0], i, scan_length))
                {
                    list.push_back(i);
                    notfound = false;
                    break;
                }
            }
            if (notfound)
                // hash collision, the probability of a hash collision in 1787897414 times is about 0.5, solved from e ^ (-n ^ 2 / (2 * (2 ^ 61 - 1))) = 0.5
                // https://en.wikipedia.org/wiki/Birthday_problem
                // create a new list representing a new group of repeating patterns
                lists.push_back({i});
        }

        rolling_hash(window_hash, h, i);
    }

    vector<Matches> matches;
    for (auto &pair : hashDict)
    {
        for (auto &list : pair.second)
        {
            if (list.size() > 1)
                matches.push_back({scan_length, pair.first, list});
        }
    }
    return matches;
}

int RabinKarp::find_initial_next_matching_point(const Matches &match, int i, int &prev_start, int &prev_end) const
{
    int size = match.indices.size();
    int scan_length = match.scan_length;
    for (; i < size; ++i)
    {
        prev_start = match.indices[i];
        prev_end = prev_start + scan_length;
        if (hashDict.find(prev_end) != hashDict.end())
            return i + 1;
    }
    return -1;
}

Matches RabinKarp::find_optimal_expansion(const Matches &match) const
{
    int prev_start, prev_end;
    int i = find_initial_next_matching_point(match, 0, prev_start, prev_end);
    if (i < 0)
        return {};

    auto scan_length = match.scan_length;
    auto prev_hash = hashDict.at(prev_end);
    Matches newMatch = {scan_length, prev_hash, {prev_start}};
    Matches optimalExpansion = {scan_length, prev_hash, {prev_start}};
    int size = match.indices.size();
    for (; i < size; ++i)
    {
        int start = match.indices[i];
        int end = start + scan_length;
        if (hashDict.find(end) != hashDict.end())
        {
            auto hash = hashDict.at(end);
            if (!(newMatch.hashCode == hash && matches(prev_end, end, scan_length)))
            {
                if (newMatch.indices.size() > optimalExpansion.indices.size())
                    optimalExpansion = newMatch;
                newMatch.indices.clear();
            }
            newMatch.indices.push_back(start);
            newMatch.hashCode = hash;
            prev_start = start;
            prev_end = prev_start + scan_length;
        }
    }
    if (newMatch.indices.size() > optimalExpansion.indices.size())
        optimalExpansion = newMatch;
    optimalExpansion.scan_length <<= 1;
    optimalExpansion.hashCode += match.hashCode.shl(scan_length);
    return optimalExpansion;
}

vector<Matches> RabinKarp::expand(vector<Matches> &oldMatches) const
{
    vector<Matches> newMatches;
    vector<int> indicesToDelete;
    for (auto args : enumerate(oldMatches))
    {
        int index = args.index;
        auto &match = args.value;
        // if (match.indices[0] == 0)
            // print("match:", info(match));
        auto optimalExpansion = find_optimal_expansion(match);
        // if (match.indices[0] == 0)
            // print("optimalExpansion:", info(optimalExpansion));
        if (optimalExpansion.indices.size() < match.indices.size())
        {
            auto optimalExtension = extend_bytes(match);
            if (optimalExtension.empty())
                optimalExtension = match;
            optimalExtension = extend_byte(optimalExtension);
            if (optimalExtension - match > 0)
                match = optimalExtension;

            auto optimalFilter = filter(match);
            if (!optimalExpansion.empty())
                newMatches.push_back(optimalExpansion);
            if (optimalFilter.empty())
                indicesToDelete.push_back(index);
            else
                match = optimalFilter;
        }
        else
        {
            newMatches.push_back(optimalExpansion);
            indicesToDelete.push_back(index);
        }
    }

    del(oldMatches, indicesToDelete);
    return newMatches;
}

Matches RabinKarp::filter(const Matches &match) const
{
    int scan_length = match.scan_length;
    int prev_start = match.indices[0];
    Matches oldMatch = {scan_length, match.hashCode, {prev_start}};
    Matches optimalFilter = {scan_length, match.hashCode, {prev_start}};
    int size = match.indices.size();
    for (int i = 1; i < size; ++i)
    {
        int start = match.indices[i];
        // constraint of StartIndexᵢ₊₁ - StartIndexᵢ
        if (start - prev_start > scan_length * pow(2, min(scan_length, 1024) / 14.3) / 1.7 - 3.25)
        {
            if (oldMatch.indices.size() > optimalFilter.indices.size())
                optimalFilter = oldMatch;
            oldMatch.indices.clear();
        }
        oldMatch.indices.push_back(start);
        prev_start = start;
    }
    if (oldMatch.indices.size() > optimalFilter.indices.size())
        optimalFilter = oldMatch;

    return optimalFilter;
}

Matches RabinKarp::extend_bytes(Matches oldMatch) const
{
    int scan_length = oldMatch.scan_length;
    int scan_length_max = scan_length << 1;
    while (scan_length + this->scan_length < scan_length_max)
    {
        int prev_start = oldMatch.indices[0];
        int prev_end = prev_start + scan_length;
        // scan_length might be different from this->scan_length!
        auto prev_hash = hashCode[prev_end];
        Matches newMatch = {scan_length, prev_hash, {prev_start}};
        Matches optimalExtension = {scan_length, prev_hash, {prev_start}};
        int size = oldMatch.indices.size();
        for (int i = 1; i < size; ++i)
        {
            int prev_end = prev_start + scan_length;
            int start = oldMatch.indices[i];
            int end = start + scan_length;
            auto hash = hashCode[end];

            if (!(newMatch.hashCode == hash && matches(prev_end, end, this->scan_length)))
            {
                if (newMatch.indices.size() > optimalExtension.indices.size())
                    optimalExtension = newMatch;
                newMatch.indices.clear();
            }
            newMatch.indices.push_back(start);
            newMatch.hashCode = hash;
            prev_start = start;
        }
        if (newMatch.indices.size() > optimalExtension.indices.size())
            optimalExtension = newMatch;
        if (optimalExtension.empty())
            break;
        scan_length += this->scan_length;
        optimalExtension.scan_length = scan_length;
        optimalExtension.hashCode += oldMatch.hashCode.shl(this->scan_length);
        oldMatch = optimalExtension;
    }
    return oldMatch;
}

Matches RabinKarp::extend_byte(Matches oldMatch) const
{
    int scan_length = oldMatch.scan_length;
    int scan_length_max = scan_length + this->scan_length;
    while (scan_length + 1 < scan_length_max)
    {
        int prev_start = oldMatch.indices[0];
        int prev_end = prev_start + scan_length;
        hash_t prev_hash = (unsigned char)text[prev_end];
        Matches newMatch = {scan_length, prev_hash, {prev_start}};
        Matches optimalExtension = {scan_length, prev_hash, {prev_start}};
        int size = oldMatch.indices.size();
        for (int i = 1; i < size; ++i)
        {
            int start = oldMatch.indices[i];
            int end = start + scan_length;
            hash_t hash = (unsigned char)text[end];

            if (newMatch.hashCode.hash != hash)
            {
                if (newMatch.indices.size() > optimalExtension.indices.size())
                    optimalExtension = newMatch;
                newMatch.indices.clear();
                newMatch.hashCode.hash = hash;
            }
            newMatch.indices.push_back(start);
        }
        if (newMatch.indices.size() > optimalExtension.indices.size())
            optimalExtension = newMatch;
        if (optimalExtension.empty())
            break;
        ++scan_length;
        optimalExtension.scan_length = scan_length;
        optimalExtension.hashCode = HashCode(oldMatch.hashCode, optimalExtension.hashCode.hash);
        oldMatch = optimalExtension;
    }
    return oldMatch;
}

void RabinKarp::create_hash_table_for_double_hashing(const vector<Matches> &matches)
{
    hashDict.clear();
    for (auto &match : matches)
    {
        for (int start : match.indices)
        {
            hashDict[start] = match.hashCode;
        }
    }
}

void RabinKarp::debug(const vector<Matches> &matches) const
{
    int width = ceil(log10(text.size()));
    for (auto &match : sorted(matches, [](auto &lhs, auto &rhs)
                              { return lhs.indices[0] < rhs.indices[0]; }))
    {
        int scan_length = match.scan_length;
        auto duplicatePattern = text.substr(match.indices[0], scan_length);
        for (int start : match.indices)
        {
            auto end = start + scan_length;
            cout << "text[" << std::setw(width) << start << ":" << std::setw(width) << end << "] = ";
        }
        cout << json_encode(duplicatePattern) << " |>.hash = " << match.hashCode << endl;
    }
}

vector<Matches> RabinKarp::redundancy_detect()
{
    vector<Matches> result;
    vector<Matches> matches = initial_detect();
    int length = text.size();
    while (!matches.empty() && matches[0].scan_length << 1 <= length)
    {
        // print("\n\n\nmatches[0].scan_length =", matches[0].scan_length);
        create_hash_table_for_double_hashing(matches);
        // debug(matches);
        vector<Matches> newMatches = expand(matches);
        for (auto &match : matches)
        {
            // print("Curr:", info(match));
            vector<int> inferiors;
            bool has_superiors = false;
            for (const auto &[index, m] : enumerate(result))
            {
                if (m.overlap(match))
                {
                    int cmp = m - match;
                    if (cmp < 0)
                        inferiors.push_back(index);
                    else
                    {
                        has_superiors = true;
                        break;
                    }
                }
            }
            if (has_superiors)
                continue;

            if (!inferiors.empty())
                // delete all inferiors;
                del(result, inferiors);

            result.push_back(match);
        }
        matches = newMatches;
    }

    return result;
}

string RabinKarp::substr(const Matches &match) const
{
    if (match.indices.empty())
        return "";
    return text.substr(match.indices[0], match.scan_length);
}

string RabinKarp::info(const Matches &match) const
{
    return json_encode(substr(match)) + " * " + std::to_string(match.indices.size()) + ", with length = " + std::to_string(match.scan_length);
}