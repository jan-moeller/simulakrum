//
// MIT License
//
// Copyright (c) 2023 Jan Möller
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
//
#include "get_version.hpp"

#include <simulakrum/simulakrum.hpp>

#include <iostream>

auto main() -> int
{
    using namespace simulakrum;

    // register an observer that is scoped to the next block
    {
        [[maybe_unused]] auto const observer = mock_manager::register_observer<vkEnumerateInstanceVersion>(
            [](uint32_t*) { std::cout << "observer called\n"; });
        get_version();
    }

    // call default implementation
    uint32_t version = get_version();
    std::cout << "default impl: " << version << '\n';

    // override the mock implementation
    [[maybe_unused]] auto const override = mock_manager::override<vkEnumerateInstanceVersion>(
        [](uint32_t* out) -> VkResult
        {
            *out = 42;
            return VK_SUCCESS;
        });
    version = get_version();
    std::cout << "override: " << version << '\n';

    return 0;
}