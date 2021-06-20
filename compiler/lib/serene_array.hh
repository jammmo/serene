#include <iostream>
#include <vector>

template<typename Data>
class SN_Array {
private:
    std::vector<Data> items;
public:
    int sn_length;
    SN_Array(std::vector<Data>&& data) {
        sn_length = data.size();
        items = data;
    }

    Data& operator[] (unsigned int index) {
        return items.at(index);
    }

    template<typename X>
    friend std::ostream& operator<<(std::ostream& os, const SN_Array<X>& obj);
};

template<typename Data>
std::ostream& operator<<(std::ostream& os, const SN_Array<Data>& obj) {
    os << "[";
    for (int i = 0; i < obj.sn_length - 1; i++) {
        os << obj.items[i] << ", ";
    }
    os << obj.items[obj.sn_length - 1] << "]";
    return os;
}
