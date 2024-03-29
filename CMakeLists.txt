#
# MIT License
#
# Copyright (c) 2023 Jan Möller
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

cmake_minimum_required(VERSION 3.24)
project(simulakrum
        VERSION 0.1.1
        LANGUAGES CXX
)

#############################################################################################################
# Prevent in-source builds
#############################################################################################################
if (PROJECT_SOURCE_DIR STREQUAL PROJECT_BINARY_DIR)
    message(
            FATAL_ERROR
            "In-source builds not allowed. Please make a new directory (called a build directory) and run CMake from there."
    )
endif ()

#############################################################################################################
# Dependencies
#############################################################################################################
include(cmake/CPM.cmake)

CPMAddPackage("gh:TheLartians/PackageProject.cmake@1.11.0")
CPMAddPackage("gh:KhronosGroup/Vulkan-Headers#v1.3.238")
if (${CPM_LAST_PACKAGE_NAME}_ADDED)
    message(STATUS ${CPM_LAST_PACKAGE_NAME})
    # Vulkan-Headers doesn't export its targets appropriately... so we do it for them
    packageProject(
            NAME Vulkan-Headers
            VERSION v1.3.238
            NAMESPACE Vulkan
            BINARY_DIR ${${CPM_LAST_PACKAGE_NAME}_BINARY_DIR}
            INCLUDE_DIR ${${CPM_LAST_PACKAGE_NAME}_SOURCE_DIR}/include
            INCLUDE_DESTINATION include/Vulkan-Headers-1.3.250
            COMPATIBILITY SameMajorVersion
            DEPENDENCIES ""
    )
endif ()

#############################################################################################################
# Build configuration
#############################################################################################################
option(SIMULAKRUM_BUILD_TESTS "Build the simulakrum tests" OFF)

message(STATUS "------------------------------------------------------------------------------")
message(STATUS "    ${PROJECT_NAME} (${PROJECT_VERSION})")
message(STATUS "------------------------------------------------------------------------------")
message(STATUS "Build type:                ${CMAKE_BUILD_TYPE}")
message(STATUS "SIMULAKRUM_BUILD_TESTS:    ${SIMULAKRUM_BUILD_TESTS}")

#############################################################################################################
# Code generation
#############################################################################################################
file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/gen/include/simulakrum)
file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/gen/src)
file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/gen/cmake)
execute_process(COMMAND python3 scripts/gen_from_xml.py
        --registry ${Vulkan-Headers_SOURCE_DIR}/registry/vk.xml
        --header-dir ${CMAKE_CURRENT_BINARY_DIR}/gen/include
        --source-dir ${CMAKE_CURRENT_BINARY_DIR}/gen/src
        --cmake-dir ${CMAKE_CURRENT_BINARY_DIR}/gen/cmake
        --stub-dir ${CMAKE_CURRENT_SOURCE_DIR}/src/default
        WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
)

include(${CMAKE_CURRENT_BINARY_DIR}/gen/cmake/simulakrum_generated.cmake)

#############################################################################################################
# Main library target
#############################################################################################################
add_library(simulakrum
        ${simlakrum_default_SRC}
        ${simlakrum_generated_INCLUDE}
        ${simlakrum_generated_SRC}
        include/simulakrum/c_array.hpp
        include/simulakrum/mock_manager.hpp
        include/simulakrum/simulakrum.hpp
        include/simulakrum/vk_function_impl.hpp
        include/simulakrum/vk_function_info.hpp
        include/simulakrum/vk_function_observer.hpp
)
target_include_directories(simulakrum PUBLIC include/ ${Vulkan-Headers_SOURCE_DIR}/include ${CMAKE_CURRENT_BINARY_DIR}/gen/include)
set_target_properties(simulakrum PROPERTIES LINKER_LANGUAGE CXX)
set_target_properties(simulakrum PROPERTIES
        CXX_STANDARD 20
        CXX_STANDARD_REQUIRED YES
        CXX_EXTENSIONS NO
)

if (${SIMULAKRUM_BUILD_TESTS})
    add_subdirectory(test)
endif ()