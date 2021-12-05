#pragma once

#include <iostream>

class SereneLocale : public std::numpunct<char> {
protected:
    std::string do_truename()  const override { return "True";  }
    std::string do_falsename() const override { return "False"; }
};
