#pragma once

#include "../lib/visit_struct.hpp"

template<typename T>
std::ostream& print_struct(std::ostream& os, const T& obj) {
    os << visit_struct::get_name(obj) + 3;  // the "+ 3" removes the "SN_" prefix
    os << "(";
    bool first = true;
    visit_struct::for_each(obj, [&](const char* name, const auto& value) {
        if(first) {
            first = false;
        } else {
            os << ", ";
        }
        os << name + 3 << ": " << value;    // the "+ 3" removes the "sn_" prefix
    });
    os << ")";
    return os;
}