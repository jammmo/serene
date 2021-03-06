#include <iostream>
#include <vector>

template<typename Data>
class SN_Array {
private:
    int length;
    std::vector<Data> items;
public:
    SN_Array(std::vector<Data>&& data) {
        length = data.size();
        items = data;
    }

    int sn_length() {
        return length;
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
    friend std::ostream& operator<<(std::ostream& os, const SN_Array<X>& obj);
};

template<typename Data>
std::ostream& operator<<(std::ostream& os, const SN_Array<Data>& obj) {
    os << "[";
    for (int i = 0; i < obj.length - 1; i++) {
        os << obj.items[i] << ", ";
    }
    os << obj.items[obj.length - 1] << "]";
    return os;
}
