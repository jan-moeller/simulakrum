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

#ifndef SIMULAKRUM_MOCK_MANAGER_HPP
#define SIMULAKRUM_MOCK_MANAGER_HPP

#include "vk_function_impl.hpp"
#include "vk_function_info.hpp"
#include "vk_function_observer.hpp"

#include <functional>
#include <list>
#include <string_view>
#include <utility>

namespace simulakrum
{
struct mock_manager
{
    ~mock_manager() noexcept                             = delete;
    mock_manager()                                       = delete;
    mock_manager(mock_manager const&)                    = delete;
    mock_manager(mock_manager&&)                         = delete;
    auto operator=(mock_manager const&) -> mock_manager& = delete;
    auto operator=(mock_manager&&) -> mock_manager&      = delete;

    template<auto vk_fn>
    static constexpr auto name() -> std::string_view
    {
        return info<vk_fn>.name;
    }

    template<auto vk_fn, typename... Args>
    static auto call(Args&&... args) -> decltype(auto)
    {
        constexpr auto const& fn_info      = info<vk_fn>;
        auto const&           fn_overrides = overrides<vk_fn>;
        auto const&           fn_observers = observers<vk_fn>;

        for (auto&& observer : fn_observers)
            std::invoke(observer, args...);

        if (fn_overrides.empty())
            return std::invoke(fn_info.default_impl, std::forward<Args>(args)...);
        return std::invoke(fn_overrides.back(), std::forward<Args>(args)...);
    }

    template<auto vk_fn>
    static auto register_observer(vk_function_observer<vk_fn> observer)
    {
        auto& fn_observers = observers<vk_fn>;
        fn_observers.emplace_back(std::move(observer));
        return observer_handle<vk_fn>{std::prev(fn_observers.end())};
    }

    template<auto vk_fn>
    static auto override(vk_function_impl<vk_fn> override)
    {
        auto& fn_overrides = overrides<vk_fn>;
        fn_overrides.emplace_back(std::move(override));
        return override_handle<vk_fn>{std::prev(fn_overrides.end())};
    }

  private:
    template<auto vk_fn>
    static constexpr vk_function_info<vk_fn> info = {.name = "unknown function", .default_impl = nullptr};

    template<auto vk_fn>
    static inline std::list<vk_function_impl<vk_fn>> overrides = {};

    template<auto vk_fn>
    static inline std::list<vk_function_observer<vk_fn>> observers = {};

    friend class observer_handle;

    template<typename Derived, typename iterator>
    class basic_handle
    {
      public:
        ~basic_handle() noexcept { static_cast<Derived*>(this)->reset(); }
        basic_handle()                    = default;
        basic_handle(basic_handle const&) = delete;
        basic_handle(basic_handle&& other) noexcept
            : m_iter(std::exchange(other.m_iter, iterator{}))
        {
        }

        auto operator=(basic_handle const&) = delete;
        auto operator=(basic_handle&& other) noexcept -> basic_handle&
        {
            if (this != &other)
            {
                static_cast<Derived*>(this)->reset();
                m_iter = std::exchange(other.m_iter, iterator{});
            }
            return *this;
        }

        auto get() const noexcept { return *std::as_const(m_iter); }
        auto get() noexcept { return *m_iter; }

      protected:
        iterator m_iter = {};

        explicit basic_handle(iterator iter) noexcept
            : m_iter(iter)
        {
        }

        friend class mock_manager;
    };

    template<auto vk_fn>
    struct override_handle : basic_handle<override_handle<vk_fn>, typename std::list<vk_function_impl<vk_fn>>::iterator>
    {
      private:
        using iterator = typename std::list<vk_function_impl<vk_fn>>::iterator;
        using base     = basic_handle<override_handle<vk_fn>, iterator>;

      public:
        void reset() noexcept
        {
            if (base::m_iter != iterator{})
                mock_manager::overrides<vk_fn>.erase(base::m_iter);
        }

        explicit override_handle(iterator iter)
            : base(iter)
        {
        }
    };

    template<auto vk_fn>
    struct observer_handle
        : basic_handle<observer_handle<vk_fn>, typename std::list<vk_function_observer<vk_fn>>::iterator>
    {
      private:
        using iterator = typename std::list<vk_function_observer<vk_fn>>::iterator;
        using base     = basic_handle<observer_handle<vk_fn>, iterator>;

      public:
        void reset() noexcept
        {
            if (base::m_iter != iterator{})
                mock_manager::observers<vk_fn>.erase(base::m_iter);
        }

        explicit observer_handle(iterator iter)
            : base(iter)
        {
        }
    };
};

} // namespace simulakrum

#include "simulakrum/combined_info.hpp"

#endif // SIMULAKRUM_MOCK_MANAGER_HPP
