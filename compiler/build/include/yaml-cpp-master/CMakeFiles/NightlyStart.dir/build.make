# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.20

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:

#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:

# Disable VCS-based implicit rules.
% : %,v

# Disable VCS-based implicit rules.
% : RCS/%

# Disable VCS-based implicit rules.
% : RCS/%,v

# Disable VCS-based implicit rules.
% : SCCS/s.%

# Disable VCS-based implicit rules.
% : s.%

.SUFFIXES: .hpux_make_needs_suffix_list

# Command-line flag to silence nested $(MAKE).
$(VERBOSE)MAKESILENT = -s

#Suppress display of executed commands.
$(VERBOSE).SILENT:

# A target that is always out of date.
cmake_force:
.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/bin/cmake.exe

# The command to remove a file.
RM = /usr/bin/cmake.exe -E rm -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /cygdrive/c/Users/mosch/Desktop/Serene/compiler

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /cygdrive/c/Users/mosch/Desktop/Serene/compiler/build

# Utility rule file for NightlyStart.

# Include any custom commands dependencies for this target.
include include/yaml-cpp-master/CMakeFiles/NightlyStart.dir/compiler_depend.make

# Include the progress variables for this target.
include include/yaml-cpp-master/CMakeFiles/NightlyStart.dir/progress.make

include/yaml-cpp-master/CMakeFiles/NightlyStart:
	cd /cygdrive/c/Users/mosch/Desktop/Serene/compiler/build/include/yaml-cpp-master && /usr/bin/ctest.exe -D NightlyStart

NightlyStart: include/yaml-cpp-master/CMakeFiles/NightlyStart
NightlyStart: include/yaml-cpp-master/CMakeFiles/NightlyStart.dir/build.make
.PHONY : NightlyStart

# Rule to build all files generated by this target.
include/yaml-cpp-master/CMakeFiles/NightlyStart.dir/build: NightlyStart
.PHONY : include/yaml-cpp-master/CMakeFiles/NightlyStart.dir/build

include/yaml-cpp-master/CMakeFiles/NightlyStart.dir/clean:
	cd /cygdrive/c/Users/mosch/Desktop/Serene/compiler/build/include/yaml-cpp-master && $(CMAKE_COMMAND) -P CMakeFiles/NightlyStart.dir/cmake_clean.cmake
.PHONY : include/yaml-cpp-master/CMakeFiles/NightlyStart.dir/clean

include/yaml-cpp-master/CMakeFiles/NightlyStart.dir/depend:
	cd /cygdrive/c/Users/mosch/Desktop/Serene/compiler/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /cygdrive/c/Users/mosch/Desktop/Serene/compiler /cygdrive/c/Users/mosch/Desktop/Serene/compiler/include/yaml-cpp-master /cygdrive/c/Users/mosch/Desktop/Serene/compiler/build /cygdrive/c/Users/mosch/Desktop/Serene/compiler/build/include/yaml-cpp-master /cygdrive/c/Users/mosch/Desktop/Serene/compiler/build/include/yaml-cpp-master/CMakeFiles/NightlyStart.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : include/yaml-cpp-master/CMakeFiles/NightlyStart.dir/depend

