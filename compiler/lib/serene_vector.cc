#include <iostream>
#include <vector>

template<typename Data>
class SN_Vector {
private:
    std::vector<Data> items;
public:
    int sn_length;
    SN_Vector() {
        sn_length = 0;
    }

    SN_Vector(std::vector<Data>&& data) {
        sn_length = data.size();
        items = data;
    }

    auto sn_append(Data item) {
        items.push_back(item);
        sn_length = items.size();
    }
    auto sn_delete(unsigned int index) {
        items.erase(items.begin() + index);
        sn_length = items.size();
    }

    Data& operator[] (unsigned int index) {
        return items.at(index);
    }

    template<typename X>
    friend std::ostream& operator<<(std::ostream& os, const SN_Vector<X>& obj);
};

template<typename Data>
std::ostream& operator<<(std::ostream& os, const SN_Vector<Data>& obj) {
    os << "[";
    for (int i = 0; i < obj.sn_length - 1; i++) {
        os << obj.items[i] << ", ";
    }
    os << obj.items[obj.sn_length - 1] << "]";
    return os;
}
