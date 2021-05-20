cmake_minimum_required(VERSION 3.1)
project(MyCompiler)

add_subdirectory(include/yaml-cpp-master) # This is one way of referencing another
                                          # CMake project

add_executable(
    my_compiler
    compile_serene.cc
)

target_link_libraries(
    my_compiler
    PRIVATE
    yaml-cpp  # This is the "target" exposed by 
              # yaml-cpp's CMakeLists.txt file
)