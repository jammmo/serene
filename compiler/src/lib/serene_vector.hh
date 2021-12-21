#pragma once

#include <iostream>
#include <vector>
#include <exception>

template<typename Data>
class SN_Vector {
private:
    int length;
    std::vector<Data> items;
public:
    SN_Vector() {
        length = 0;
    }

    SN_Vector(std::vector<Data>&& data) {
        length = data.size();
        items = data;
    }
    
    int sn_length() const {
        return length;
    }

    auto sn_append(Data item) {
        items.push_back(item);
        length = items.size();
    }
    auto sn_insert(unsigned int index, Data item) {
        if (index > length) {
            std::cout << "< Exception: Invalid index. Exiting with error code 1 >" << std::endl;
            exit(1);
        }
        items.insert(items.begin() + index, item);
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

    Data const& operator[] (unsigned int index) const {
        return items.at(index);
    }

    Data& operator[] (unsigned int index) {
        return items.at(index);
    }

    auto begin() const {
        return items.begin();
    }

    auto end() const {
        return items.end();
    }

    template<typename X>
    friend std::ostream& operator<<(std::ostream& os, const SN_Vector<X>& obj);
};

template<typename Data>
std::ostream& operator<<(std::ostream& os, const SN_Vector<Data>& obj) {
    os << "[";
    if (obj.length >= 1) {
        for (int i = 0; i < obj.length - 1; i++) {
            os << obj.items[i] << ", ";
        }
        os << obj.items[obj.length - 1];
    }
    os << "]";
    return os;
}

template<>
std::ostream& operator<<(std::ostream& os, const SN_Vector<int8_t>& obj) {
    os << "[";
    if (obj.length >= 1) {
        for (int i = 0; i < obj.length - 1; i++) {
            os << +obj.items[i] << ", ";
        }
        os << +obj.items[obj.length - 1];
    }
    os << "]";
    return os;
}

template<>
std::ostream& operator<<(std::ostream& os, const SN_Vector<uint8_t>& obj) {
    os << "[";
    if (obj.length >= 1) {
        for (int i = 0; i < obj.length - 1; i++) {
            os << +obj.items[i] << ", ";
        }
        os << +obj.items[obj.length - 1];
    }
    os << "]";
    return os;
}
