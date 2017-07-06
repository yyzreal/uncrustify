#!/bin/env python

import os
import sys
import argparse
import subprocess
import tempfile


def get_non_default_options(exe, config, input, output_cfg, lang):
    fd, unc_fn = tempfile.mkstemp(suffix='.unc')

    cmd = "%s -c %s -f %s -l %s -p %s" % (
        exe, config, input, lang, unc_fn
    )

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()

    if p.returncode != 0:
        raise Exception("uncrustify returned error code %s" % p.returncode)

    fp = os.fdopen(fd, 'r')
    lines = fp.read().splitlines()
    lines = [line for line in lines if not line[:1] == '#']

    with open(output_cfg, 'w') as out:
        out.write('\n'.join(lines))

    fp.close()
    os.unlink(unc_fn)


def main(argv):
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        '-x', '--exe', type=str, help="uncrustify executable", default="../build/Debug/uncrustify.exe"
    )
    arg_parser.add_argument(
        '-c', '--config', type=str, help="config file"
    )
    arg_parser.add_argument(
        '-i', '--input', type=str, help="input file"
    )
    arg_parser.add_argument(
        '-l', '--lang', type=str, help="language"
    )
    arg_parser.add_argument(
        '-o', '--output', type=str, help="output config file with all non-default options"
    )

    args = arg_parser.parse_args()

    get_non_default_options(args.exe, args.config, args.input, args.output, args.lang)



if __name__ == "__main__":
    sys.exit(main(sys.argv))
