#include <iostream>
#include <vector>

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
        sn_length = data.size();
        items = data;
    }
    
    int sn_length() {
        return length;
    }

    auto sn_append(Data item) {
        items.push_back(item);
        length = items.size();
    }
    auto sn_delete(unsigned int index) {
        items.erase(items.begin() + index);
        length = items.size();
    }

    Data& operator[] (unsigned int index) {
        return items.at(index);
    }

    auto begin() {
        return items.begin();
    }

    auto end() {
        return items.end();
    }

    template<typename X>
    friend std::ostream& operator<<(std::ostream& os, const SN_Vector<X>& obj);
};

template<typename Data>
std::ostream& operator<<(std::ostream& os, const SN_Vector<Data>& obj) {
    os << "[";
    for (int i = 0; i < obj.length - 1; i++) {
        os << obj.items[i] << ", ";
    }
    os << obj.items[obj.length - 1] << "]";
    return os;
}
