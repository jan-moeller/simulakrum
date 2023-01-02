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
from xml.etree import ElementTree as ET

cpp_file_header = '''//
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
'''
cpp_generated_warning = '''

// This is a generated file. Do not edit!

'''
cpp_scaffolding_includes = ['"simulakrum.hpp"', '<vulkan/vulkan.h>']
cpp_default_impl_stub_includes = ['<vulkan/vulkan.h>']


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input', default='vk.xml',
                        help='Specify the input vulkan registry file')
    parser.add_argument('-o', '--output', default='gen/',
                        help='Specify the directory to generate the function scaffolding in')
    parser.add_argument('--default-stub-dir', default='src/default',
                        help='Specify the directory to generate the default stubs in, if not already there')
    parser.add_argument('--enable-extension', action='append', dest='enabled_extensions', default=[],
                        help='Enable generation of scaffolding and stubs for an extension')
    parser.add_argument('-v', "--verbose", action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()

    if args.verbose:
        print(f"Vulkan registry file: {args.input}")
        print(f"Generating scaffolding to: {args.output}")
        print(f"Generating default implementation stubs to: {args.default_stub_dir}")

    tree = ET.parse(args.input)
    root = tree.getroot()

    function_blacklist = compile_blacklist(args, root)

    commands = root.find('commands')
    for c in commands:
        proto = c.find('proto')
        if proto is None:
            continue

        name = proto.find('name').text

        if name in function_blacklist:
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
            params.append((param_name, decl))

        generate_scaffolding(args, name, return_type, params)
        generate_default_impl(args, name, return_type, params)


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


def generate_scaffolding(args, name, return_type, params):
    filename = f'{name}.cpp'
    file_path = os.path.join(args.output, filename)

    if args.verbose:
        print(f'Generating scaffolding for {name} in: {file_path}')

    with open(file_path, 'w') as out:
        out.write(cpp_file_header)
        out.write(cpp_generated_warning)
        for i in cpp_scaffolding_includes:
            out.write(f'#include {i}\n\n')

        param_strings = [param[1] for param in params]
        params_string = ' '.join(', '.join(param_strings).split())
        arg_strings = [param[0] for param in params]
        args_string = ", ".join(arg_strings)

        out.write('extern "C" {\n')
        out.write(f'    VKAPI_ATTR {return_type} VKAPI_CALL {name}({params_string});\n')
        out.write('}\n')

        out.write('namespace simulakrum {\n')

        out.write(f'{return_type} {name}_default({params_string});\n\n')
        out.write(
            f'template<>\nvk_fn_info<{name}> info<{name}> = {{.name = "{name}", .default_impl = {name}_default}};\n')

        out.write('} // namespace simulakrum\n\n')

        out.write(f'VKAPI_ATTR {return_type} VKAPI_CALL {name}({params_string}) {{\n')
        out.write(f'    return ::simulakrum::call<{name}>({args_string});\n')
        out.write('}\n')


def generate_default_impl(args, name, return_type, params):
    filename = f'{name}_default.cpp'
    file_path = os.path.join(args.default_stub_dir, filename)

    if os.path.isfile(file_path):
        if args.verbose:
            print(f'Skipping generation of stub for {name} in: {file_path}')
        return

    if args.verbose:
        print(f'Generating default implementation stub for {name} in: {file_path}')

    with open(file_path, 'w') as out:
        out.write(cpp_file_header)
        for i in cpp_default_impl_stub_includes:
            out.write(f'#include {i}\n')
        out.write('\nnamespace simulakrum\n{\n')

        param_strings = [param[1] for param in params]
        params_string = ' '.join(', '.join(param_strings).split())
        out.write(f'auto {name}_default({params_string}) -> {return_type}\n{{\n')
        out.write('    // TODO: Implement me\n')
        if return_type == 'VkResult':
            out.write('    return VK_SUCCESS;\n')
        elif return_type != 'void':
            out.write(f'    return {return_type}{{}};\n')
        out.write('}\n')
        out.write('} // namespace simulakrum\n\n')


if __name__ == '__main__':
    main()
