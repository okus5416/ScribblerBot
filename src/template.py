#!/usr/bin/env python

# Copyright 2014 Mitchell Kember. Subject to the MIT License.

import os
import sys


PAGES = ['index', '404']
SRC_DIR = '../template/'
SRC_EXT = '.txt'
DEST_DIR = '../public/'
DEST_EXT = '.html'
TEMPLATE = SRC_DIR + 'page.html'


def build_dict(path):
    """Builds a dictionary for template keys given a text file containing the
    key-value associations."""
    d = {}
    key = None
    val = None
    in_value = False
    with open(path) as f:
        for line in f:
            if line[0] == '{' and line[-2] == '}':
                if in_value:
                    sys.exit("bad format in {}", path)
                else:
                    key = line[1:-2]
                    val = ""
                    in_value = True
            elif in_value and line[0] == '\n':
                d[key] = val
                in_value = False
            else:
                val += line
        # The last key won't get mapped unless the file ends with two blank
        # lines, so check for that now.
        if in_value:
            d[key] = val
    return d


def generate():
    """Fills the template with the generated dictionaries for each page and
    writes the HTML into the public folder."""
    with open(TEMPLATE) as template_file:
        template = template_file.read()
        for page in PAGES:
            src = SRC_DIR + page + SRC_EXT
            d = build_dict(src)
            filled = template.format(**d).strip()
            dest = DEST_DIR + page + DEST_EXT
            with open(dest, 'w') as dest_file:
                dest_file.write(filled)


if __name__ == '__main__':
    # Go to this directory to make the relative paths work.
    script_dir = os.path.dirname(sys.argv[0])
    if script_dir:
        os.chdir(script_dir)
    generate()
