#!/usr/bin/env python3
# Copyright (c) 2016-2017, henry232323
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

async def _(ctx, translation):
    #currency = ":spankme:"
    #if ctx.guild is not None:
    #    #gd = await self.config.guild(ctx.guild)
    #    lang = "en"
    #    if lang != "en":
    #        try:
    #            currency = ":spankme:"
    #        except:
    #            pass

    return translation#.replace("dollars", currency)

def format_table(lines, separate_head=True):
    """Prints a formatted table given a 2 dimensional array"""
    # Count the column width
    print(lines)
    widths = []
    for line in lines:
        print(line)
        for i, size in enumerate([len(x) for x in line]):
            while i >= len(widths):
                widths.append(0)
            if size > widths[i]:
                widths[i] = size

    # Generate the format string to pad the columns
    print_string = ""
    for i, width in enumerate(widths):
        print_string += "{" + str(i) + ":" + str(width) + "} | "
    if not len(print_string):
        return
    print_string = print_string[:-3]

    # Print the actual data
    fin = []
    for i, line in enumerate(lines):
        fin.append(print_string.format(*line))
        if i == 0 and separate_head:
            fin.append("-" * (sum(widths) + 3 * (len(widths) - 3)))

    return "\n".join(fin)