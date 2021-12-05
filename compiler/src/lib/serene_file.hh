#pragma once

#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include "serene_string.hh"

class SN_File {
private:
    std::string path;
    std::ifstream filestream;
public:
    SN_File(SN_String&& sn_path) {
        std::string s;
        for (char c: sn_path) {
            s.push_back(c);
        }

        path = s;
        filestream.open(path.c_str());

        if (!filestream.is_open()) {
            std::cout << "< Exception: File \"" << path << "\" cannot be opened. Exiting with error code 1 >" << std::endl;
            exit(1);
        }
    }

    SN_String sn_to_string() const {
        std::stringstream buffer;
        buffer << filestream.rdbuf();
        return SN_String(buffer.str());
    }    

    friend std::ostream& operator<<(std::ostream& os, const SN_File& obj);
};

std::ostream& operator<<(std::ostream& os, const SN_File& obj) {
    os << obj.path;
    return os;
}
