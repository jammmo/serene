#include "../lib/visit_struct.hpp"

template<typename T>
std::ostream& print_struct(std::ostream& os, const T& obj) {
    os << "{ ";
    bool first = true;
    visit_struct::for_each(obj, [&](const char* name, const auto& value) {
        if(first) {
            first = false;
        } else {
            os << ", ";
        }
        os << name << ": " << value;
    });
    os << " }";
    return os;
}