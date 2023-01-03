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
import argparse
import os
import re
import textwrap
from collections import namedtuple
from xml.etree import ElementTree as ET

mit_license_text = '''MIT License

Copyright (c) 2023 Jan Möller

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
generated_file_warning_text = '''This is a generated file. Do not edit!'''

cpp_license_header = textwrap.indent('\n' + mit_license_text, '// ', predicate=lambda l: True)
cpp_generated_file_warning_header = textwrap.indent(generated_file_warning_text, '// ', predicate=lambda l: True)

cmake_license_header = textwrap.indent('\n' + mit_license_text, '# ', predicate=lambda l: True)
cmake_generated_file_warning_header = textwrap.indent(generated_file_warning_text, '# ', predicate=lambda l: True)

info_header_template = '''
#include "mock_manager.hpp"
#include <vulkan/vulkan.h>
{additional_includes}

namespace simulakrum
{{
    auto {name}_default({params}) -> {return_type};
    
    template<>
    constexpr vk_function_info<{name}> mock_manager::info<{name}> = {{
        .name = "{name}",
        .default_impl = {name}_default,
    }};
}} // namespace simulakrum
'''

function_impl_template = '''
#include "mock_manager.hpp"
#include <vulkan/vulkan.h>
{additional_includes}

extern "C"
{{
    VKAPI_ATTR {return_type} VKAPI_CALL {name}({params})
    {{
        return ::simulakrum::mock_manager::call<{name}>({args});
    }}
}}
'''

stub_template = '''
#include <vulkan/vulkan.h>
{additional_includes}

namespace simulakrum
{{
    auto {name}_default({params}) -> {return_type}
    {{
        // TODO: Implement me
        {return_statement};
    }}
}} // namespace simulakrum
'''

Parameter = namedtuple('Parameter', ['name', 'type', 'isarraytype'])
Function = namedtuple('Function', ['name', 'returntype', 'args'])


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--registry', default='vk.xml',
                        help='Specify the input vulkan registry file')
    parser.add_argument('--header-dir', default='gen/include/',
                        help='Specify the directory to write generated headers to')
    parser.add_argument('--source-dir', default='gen/src/',
                        help='Specify the directory to write generated source files to')
    parser.add_argument('--cmake-dir', default='gen/cmake/',
                        help='Specify the directory to write generated cmake files to')
    parser.add_argument('--stub-dir', default='src/default',
                        help="Specify the directory to generate the stubs in (won't be overwritten if already there)")
    parser.add_argument('--enable-extension', action='append', dest='enabled_extensions', default=[],
                        help='Enable generation of scaffolding and stubs for an extension')
    parser.add_argument('-v', "--verbose", action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()

    if args.verbose:
        print(f"Vulkan registry file: {args.registry}")
        print(f"Generating headers in: {args.header_dir}")
        print(f"Generating source in: {args.source_dir}")
        print(f"Generating cmake in: {args.cmake_dir}")
        print(f"Generating stubs in: {args.stub_dir}")
        print(f"Enabled extensions: {args.enabled_extensions}")

    tree = ET.parse(args.registry)
    root = tree.getroot()

    function_blacklist = compile_blacklist(args, root)
    functions = compile_function_list(args, root, function_blacklist)

    for fn in functions:
        generate_info_header(args, fn)
        generate_function_impl(args, fn)
        generate_stub(args, fn)

    generate_combined_info_header(args, functions)
    generate_cmake(args, functions)


def fix_variable_type_and_name(param):
    match = re.match(r'(.*)\[(\d)\]$', param.name)
    if match:
        return Parameter(name=match.group(1), type=f'::simulakrum::c_array<{param.type}, {match.group(2)}>',
                         isarraytype=True)
    return param


def compile_blacklist(args, root):
    blacklist = []

    extensions = root.find('extensions')
    for e in extensions:
        name = e.attrib['name']
        if name in args.enabled_extensions:
            continue

        requires = e.findall('require')
        for r in requires:
            for c in r.iter(tag='command'):
                blacklist.append(c.attrib['name'])

    return blacklist


def compile_function_list(args, root, blacklist):
    functions = []

    commands = root.find('commands')
    for c in commands:
        proto = c.find('proto')
        if proto is None:
            continue

        name = proto.find('name').text

        if name in blacklist:
            if args.verbose:
                print(f"Skipping {name} due to it being blacklisted")
            continue

        return_type = proto.find('type').text
        params = []
        for p in c:
            if p.tag != 'param':
                continue
            param_name = p.find('name').text
            decl = ''.join(p.itertext())
            type, param_name = decl.rsplit(' ', 1)
            param = fix_variable_type_and_name(Parameter(param_name, type, False))
            params.append(param)

        functions.append(Function(name, return_type, params))

    return functions


def generate_info_header(args, fn):
    name = fn.name
    return_type = fn.returntype
    params = fn.args

    filename = f'{name}_info.hpp'
    file_path = os.path.join(args.header_dir, filename)

    if args.verbose:
        print(f'Generating info header for {name} in: {file_path}')

    param_strings = [f'{param.type} {param.name}' for param in params]
    params_string = ' '.join(', '.join(param_strings).split())

    additional_includes = ''
    uses_array_type = any([param.isarraytype for param in params])
    if uses_array_type:
        additional_includes = '#include "c_array.hpp"\n'

    with open(file_path, 'w') as out:
        out.write(cpp_license_header)
        out.write('\n')
        out.write(cpp_generated_file_warning_header)
        out.write('\n')

        out.write(info_header_template.format(name=name, return_type=return_type, params=params_string,
                                              additional_includes=additional_includes))


def generate_function_impl(args, fn):
    name = fn.name
    return_type = fn.returntype
    params = fn.args

    filename = f'{name}.cpp'
    file_path = os.path.join(args.source_dir, filename)

    if args.verbose:
        print(f'Generating implementation for {name} in: {file_path}')

    param_strings = [f'{param.type} {param.name}' for param in params]
    params_string = ' '.join(', '.join(param_strings).split())
    arg_strings = [param.name for param in params]
    args_string = ', '.join(arg_strings)

    additional_includes = ''
    uses_array_type = any([param.isarraytype for param in params])
    if uses_array_type:
        additional_includes = '#include "c_array.hpp"\n'

    with open(file_path, 'w') as out:
        out.write(cpp_license_header)
        out.write('\n')
        out.write(cpp_generated_file_warning_header)
        out.write('\n')

        out.write(
            function_impl_template.format(name=name, return_type=return_type, params=params_string, args=args_string,
                                          additional_includes=additional_includes))


def generate_stub(args, fn):
    name = fn.name
    return_type = fn.returntype
    params = fn.args

    filename = f'{name}_default.cpp'
    file_path = os.path.join(args.stub_dir, filename)

    if os.path.isfile(file_path):
        if args.verbose:
            print(f'Skipping generation of stub for {name}_default in: {file_path}')
        return

    if args.verbose:
        print(f'Generating stub for {name}_default in: {file_path}')

    param_strings = [f'{param.type} {param.name}' for param in params]
    params_string = ' '.join(', '.join(param_strings).split())
    arg_strings = [param.name for param in params]
    args_string = ', '.join(arg_strings)

    additional_includes = ''
    uses_array_type = any([param.isarraytype for param in params])
    if uses_array_type:
        additional_includes = '#include "c_array.hpp"\n'

    with open(file_path, 'w') as out:
        out.write(cpp_license_header)

        return_statement = 'return'
        if return_type == 'VkResult':
            return_statement += ' VK_SUCCESS'
        elif return_type != 'void':
            return_statement += f' {return_type}{{}}'

        out.write(
            stub_template.format(name=name, return_type=return_type, params=params_string, args=args_string,
                                 return_statement=return_statement, additional_includes=additional_includes))


def generate_combined_info_header(args, functions):
    filename = 'combined_info.hpp'
    file_path = os.path.join(args.header_dir, filename)

    if args.verbose:
        print(f'Generating combined info header in: {file_path}')

    with open(file_path, 'w') as out:
        out.write(cpp_license_header)
        out.write('\n')
        out.write(cpp_generated_file_warning_header)
        out.write('\n\n')

        for fn in functions:
            out.write(f'#include "{fn.name}_info.hpp"\n')


def generate_cmake(args, functions):
    filename = 'simulakrum_generated.cmake'
    file_path = os.path.join(args.cmake_dir, filename)

    if args.verbose:
        print(f'Generating cmake in: {file_path}')

    with open(file_path, 'w') as out:
        out.write(cmake_license_header)
        out.write('\n')
        out.write(cmake_generated_file_warning_header)
        out.write('\n\n')

        out.write('set(simlakrum_generated_INCLUDE\n')
        for fn in functions:
            out.write(f'    {args.header_dir}/{fn.name}_info.hpp\n')
        out.write(')\n')

        out.write('set(simlakrum_generated_SRC\n')
        for fn in functions:
            out.write(f'    {args.source_dir}/{fn.name}.cpp\n')
        out.write(')\n')

        out.write('set(simlakrum_default_SRC\n')
        for fn in functions:
            out.write(f'    {args.stub_dir}/{fn.name}_default.cpp\n')
        out.write(')\n')


if __name__ == '__main__':
    main()
