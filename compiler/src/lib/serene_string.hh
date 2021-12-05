#pragma once

#include <iostream>
#include <vector>
#include <string>

class SN_String {
private:
    int length;
    std::vector<char> items;
public:
    SN_String() {
        length = 0;
    }

    SN_String(std::vector<char>&& data) {
        length = data.size();
        items = data;
    }

    SN_String(std::string&& data) {
        length = data.size();
        for (auto x : data) {
            items.push_back(x);
        }       
    }
    
    int sn_length() const {
        return length;
    }

    auto sn_append(char item) {
        items.push_back(item);
        length = items.size();
    }
    auto sn_delete(unsigned int index) {
        if (index >= length) {
            std::cout << "< Exception: Invalid index. Exiting with error code 1 >" << std::endl;
            exit(1);
        }
        items.erase(items.begin() + index);
        length = items.size();
    }
    auto sn_pop() {
        auto x = items.at(length - 1);
        sn_delete(length - 1);
        return x;
    }

    char const& operator[] (unsigned int index) const {
        return items.at(index);
    }

    char& operator[] (unsigned int index) {
        return items.at(index);
    }

    auto begin() const {
        return items.begin();
    }

    auto end() const {
        return items.end();
    }

    friend std::ostream& operator<<(std::ostream& os, const SN_String& obj);

    bool operator==(SN_String const& rhs) const {
        return items == rhs.items;
    }

    bool operator<(SN_String const& rhs) const {
        return items < rhs.items;
    }

    bool operator>(SN_String const& rhs) const {
        return items > rhs.items;
    }
};

std::ostream& operator<<(std::ostream& os, const SN_String& obj) {
    for (auto x : obj) {
        os << x;
    }
    return os;
}
