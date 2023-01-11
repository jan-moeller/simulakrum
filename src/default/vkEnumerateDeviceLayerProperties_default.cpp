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

#include <vulkan/vulkan.h>

#include <algorithm>

#include <cstring>

namespace simulakrum
{
auto vkEnumerateDeviceLayerProperties_default(VkPhysicalDevice   physicalDevice,
                                              uint32_t*          pPropertyCount,
                                              VkLayerProperties* pProperties) -> VkResult
{
    static constexpr VkLayerProperties properties[] = {};

    if (pProperties == nullptr)
    {
        *pPropertyCount = sizeof(properties);
        return VK_SUCCESS;
    }

    auto const count = std::min(*pPropertyCount, static_cast<uint32_t>(sizeof(properties)));
    std::memcpy(pProperties, properties, count);

    return count != sizeof(properties) ? VK_INCOMPLETE : VK_SUCCESS;
}
} // namespace simulakrum
