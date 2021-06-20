#include <iostream>
#include <cstdint>
#include <string>
#include <stdexcept>
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

void sn_main() {
    SN_Array<int64_t> sn_a = SN_Array<int64_t>({1, 2, 3});
    SN_Array<int64_t> sn_b = sn_a;
    sn_a[2] = 100;
    sn_b[0] =  - 5;
    std::cout << sn_a << std::endl;
    std::cout << sn_b << std::endl;
}

int main() {
    sn_main();
    return 0;
}
