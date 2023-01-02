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

#ifndef SIMULAKRUM_SIMULAKRUM_HPP
#define SIMULAKRUM_SIMULAKRUM_HPP

#include <atomic>
#include <functional>
#include <string_view>
#include <vector>

#include <cstddef>

namespace simulakrum
{
template<auto vk_fn>
struct vk_fn_info
{
    std::string_view const       name;
    decltype(vk_fn) const        default_impl;
    std::vector<decltype(vk_fn)> overrides  = {};
    std::atomic_size_t           call_count = 0;
};

template<auto vk_fn>
vk_fn_info<vk_fn> info = {.name = "unknown function", .default_impl = nullptr};

template<auto vk_fn, typename... Args>
auto call(Args&&... args) -> decltype(auto)
{
    auto& fn_info = info<vk_fn>;
    ++fn_info.call_count;
    if (fn_info.overrides.empty())
        return std::invoke(fn_info.default_impl, std::forward<Args>(args)...);
    return std::invoke(fn_info.overrides.back(), std::forward<Args>(args)...);
}

} // namespace simulakrum

#endif // SIMULAKRUM_SIMULAKRUM_HPP
