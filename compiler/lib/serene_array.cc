#include <iostream>
#include <stdexcept>

template<typename Data>
class SN_Array {
private:
    Data* items;
public:
    int sn_length;
    SN_Array(int length) {
        sn_length = length;
        items = new Data [length];
    }

    ~SN_Array() {
        delete[] items;
    }

    Data& operator[] (unsigned int index) {
        if (index < sn_length) {
            return items[index];
        } else {
            throw;
        }
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

int main() {
    auto myarray = SN_Array<int>(7);
    for (int i = 0; i < 7; i++) {
        myarray[i] = i*2;
    }
    std::cout << myarray << std::endl;
    return 0;
}