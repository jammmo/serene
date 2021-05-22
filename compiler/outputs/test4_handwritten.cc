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
    for (int i = 0; i < obj.items.size() - 1; i++) {
        os << obj.items[i] << ", ";
    }
    os << obj.items[obj.items.size() - 1] << "]";
    return os;
}

void sn_binarySearchAndDelete(SN_Vector<int>& sn_u, int sn_x) {
    auto sn_low = 0;
    auto sn_high = sn_u.sn_length;
    int sn_mid;
    while (sn_low < sn_high) {
        sn_mid = (sn_low + sn_high) / 2;
        if (sn_u[sn_mid] < sn_x) {
            sn_low = sn_mid + 1;
        } else {
            sn_high = sn_mid;
        }
    }
    if (sn_u[sn_low] == sn_x) {
        sn_u.sn_delete(sn_low);
    }
}

int main() {
    auto sn_u = SN_Vector<int>();
    std::cout << "Length of u: " << sn_u.sn_length << std::endl;
    for (int sn_i = 0; sn_i < 5; sn_i++) {
        sn_u.sn_append(sn_i * 2);
    }
    std::cout << "Length of u: " << sn_u.sn_length << std::endl;
    std::cout << sn_u << std::endl;
    sn_binarySearchAndDelete(sn_u, 6);
    std::cout << "Length of u: " << sn_u.sn_length << std::endl;
    std::cout << sn_u << std::endl;
    return 0;
}