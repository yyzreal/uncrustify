#!/usr/bin/env python

"""
test_cli_options.py

Tests output generated by Uncrustifys commandline options
(excluding actual source code formatting)

:author:  Daniel Chumak
:license: GPL v2+
"""

from __future__ import print_function
from sys import stderr, argv, exit as sys_exit, version
from os import mkdir, remove, name as os_name
from os.path import dirname, relpath, isdir, isfile, join as path_join, split as path_split
from shutil import rmtree
from subprocess import Popen, PIPE, STDOUT
from io import open
import re
import difflib
import argparse
import pprint 

if os_name == 'nt':
    EX_OK = 0
    EX_USAGE = 64
    EX_SOFTWARE = 70
    NULL_DEVICE = 'nul'
else:
    from os import EX_OK, EX_USAGE, EX_SOFTWARE
    NULL_DEVICE = '/dev/null'


def eprint(*args, **kwargs):
    """
        print() wraper that sets file=stderr
    """
    print(*args, file=stderr, **kwargs)


def proc(bin_path, args_arr=()):
    """
    simple Popen wrapper to return std out/err utf8 strings


    Parameters
    ----------------------------------------------------------------------------
    :param bin_path: string
        path to the binary that is going to be called

    args_arr : list/tuple
        all needed arguments


    :return: string, string
    ----------------------------------------------------------------------------
        generated output of both stdout and stderr

    >>> proc("echo", "test")
    'test'
    """
    if not isfile(bin_path):
        eprint("bin is not a file: %s" % bin_path)
        return False

    # call uncrustify, hold output in memory
    call_arr = [bin_path]
    call_arr.extend(args_arr)
    proc = Popen(call_arr, stdout=PIPE, stderr=PIPE, universal_newlines=True)

    out_txt, err_txt = proc.communicate()

    return out_txt, err_txt

def write_to_output_path(output_path, result_str):
    """
    writes the contents of result_str to the output path
    """
    print("Auto appending differences to: " + output_path)
    
    #newline = None: this outputs  \r\n
    #newline = "\r": this outputs  \r
    #newline = "\n": this outputs  \n
    #newline = ""  : this outputs  \n    
    #For the sake of consistency, all newlines are now being written out as \n
    #However, if the result_str itself contains \r\n, then \r\n will be output
    #as this code doesn't post process the data being written out
    with open(output_path, 'w', encoding="utf-8", newline="\n") as f:
        f.write(unicode(result_str))

def get_file_content(fp):
    """
    returns file content as an utf8 string or None if fp is not a file


    Parameters
    ----------------------------------------------------------------------------
    :param fp: string
        path of the file that will be read


    :return: string or None
    ----------------------------------------------------------------------------
    the file content

    """
    out = None

    if isfile(fp):
        with open(fp, encoding="utf-8", newline="\n") as f:
            out = f.read()
    else:
        eprint("is not a file: %s" % fp)

    return out


def check_generated_output(gen_expected_path, gen_result_path, result_manip=None, program_args=None):
    """
    compares the content of two files,

    is intended to compare a file that was generated during a call of Uncrustify
    with a file that has the expected content


    Parameters
    ----------------------------------------------------------------------------
    :param gen_expected_path: string
        path to a file that will be compared with the generated file

    :param gen_result_path: string
        path to the file that will be generated by Uncrustify

    :param result_manip: lambda OR list or tuple of lambdas
        optional lambda function(s) that will be applied (before the comparison)
        on the content of the generated file,
        the lambda function(s) should accept one string parameter

    :param program_args: tuple of options
        a collection of multiple options used to add extra functionality to the script 
        (i.e. auto apply changes or show diffs on command line)

    :return: bool
    ----------------------------------------------------------------------------
    True or False depending on whether both files have the same content

    >>> check_generated_output("/dev/null", "/dev/null")
    True
    """

    gen_exp_txt = get_file_content(gen_expected_path)
    if gen_exp_txt is None:
        return False

    gen_res_txt = get_file_content(gen_result_path)
    if gen_res_txt is None:
        return False

    if result_manip is not None:
        if type(result_manip) is list or type(result_manip) is tuple:
            for m in result_manip:
                gen_res_txt = m(gen_res_txt)
        else:
            gen_res_txt = result_manip(gen_res_txt)

    if gen_res_txt != gen_exp_txt:

        with open(gen_result_path, 'w', encoding="utf-8", newline="") as f:
                f.write(unicode(gen_res_txt))
    
        if program_args.apply and program_args.auto_output_path:
                write_to_output_path(program_args.auto_output_path, gen_res_txt)
                return True
        elif program_args.diff:
            print("\n************************************")
            print("Problem with %s" % gen_result_path)
            print("************************************")

            fileDiff = difflib.ndiff(gen_res_txt.splitlines(True), gen_exp_txt.splitlines(True))

            for line in fileDiff:
                pprint.PrettyPrinter(indent=4).pprint(line)
            
            return False
        else:
                print("\nProblem with %s" % gen_result_path)
                print("use: '--diff' to find out why %s %s are different" % (gen_result_path,
                                                                            gen_expected_path))
                return False

    remove(gen_result_path)

    return True


def check_std_output(expected_path, result_path, result_str, result_manip=None, program_args=None):
    """
    compares output generated by Uncrustify (std out/err) with a the content of
    a file

    Parameters
    ----------------------------------------------------------------------------
    :param expected_path: string
        path of the file that will be compared with the output of Uncrustify

    :param result_path: string
        path to which the Uncrustifys output will be saved in case of a mismatch

    :param result_str: string (utf8)
        the output string generated by Uncrustify

    :param result_manip: lambda OR list or tuple of lambdas
        see result_manip for check_generated_output

    :param program_args: tuple of options
        a collection of multiple options used to add extra functionality to the script
        (i.e. auto apply changes or show diffs on command line)

    :return: bool
    ----------------------------------------------------------------------------
    True or False depending on whether both files have the same content

    """
    exp_txt = get_file_content(expected_path)
    if exp_txt is None:
        return False

    
    if result_manip is not None:
        if type(result_manip) is list or type(result_manip) is tuple:
            for m in result_manip:
                result_str = m(result_str)
        else:
            result_str = result_manip(result_str)

    if program_args.input_file is not "":
        with open(program_args.input_file, encoding="utf-8", newline="\n") as f:
           inputFile = f.read()

        print("Input file is:\n")
        pprint.PrettyPrinter(indent=4).pprint(inputFile)

    if result_str != exp_txt:
        with open(result_path, 'w', encoding="utf-8", newline="\n") as f:
            f.write(unicode(result_str))
       
        if program_args.apply and program_args.auto_output_path:
            write_to_output_path(program_args.auto_output_path, result_str)
            return True 
            
        if program_args.diff:
            print("\n************************************")
            print("Problem with %s" % result_path)
            print("************************************")

            fileDiff = difflib.ndiff(result_str.splitlines(True), exp_txt.splitlines(True))

            for line in fileDiff:
                pprint.PrettyPrinter(indent=4).pprint(line)
        else:
            print("\nProblem with %s" % result_path)
            print("use: '--diff' to find out why %s %s are different" % (result_path, expected_path))
        return False

    return True


def check_output(
        uncr_bin,
        program_args,
        args_arr=(),
        out_expected_path=None, out_result_manip=None, out_result_path=None,
        err_expected_path=None, err_result_manip=None, err_result_path=None,
        gen_expected_path=None, gen_result_path=None, gen_result_manip=None):
    """
    compares outputs generated by Uncrustify with files

    Paramerters
    ----------------------------------------------------------------------------
    :param uncr_bin: string
        path to the Uncrustify binary

    :param args_arr: list/tuple
        Uncrustify commandline arguments

    :param out_expected_path: string
        file that will be compared with Uncrustifys stdout output

    :param out_result_manip: string
        lambda function that will be applied to Uncrustifys stdout output
        (before the comparison with out_expected_path),
        the lambda function should accept one string parameter

    :param out_result_path: string
        path where Uncrustifys stdout output will be saved to in case of a
        mismatch

    :param err_expected_path: string
        path to a file that will be compared with Uncrustifys stderr output

    :param err_result_manip: string
        see out_result_manip (is applied to Uncrustifys stderr instead)

    :param err_result_path: string
        see out_result_path (is applied to Uncrustifys stderr instead)

    :param gen_expected_path: string
        path to a file that will be compared with a file generated by Uncrustify

    :param gen_result_path: string
        path to a file that will be generated by Uncrustify

    :param gen_result_manip:
        see out_result_path (is applied, in memory, to the file content of the
        file generated by Uncrustify instead)


    :return: bool
    ----------------------------------------------------------------------------
    True if all specified files match up, False otherwise
    """
    # check param sanity
    if not out_expected_path and not err_expected_path and not gen_expected_path:
        eprint("No expected comparison file provided")
        return False

    if bool(gen_expected_path) != bool(gen_result_path):
        eprint("'gen_expected_path' and 'gen_result_path' must be used in "
               "combination")
        return False

    if gen_result_manip and not gen_result_path:
        eprint("Set up 'gen_result_path' if 'gen_result_manip' is used")

    out_res_txt, err_res_txt = proc(uncr_bin, args_arr)

    ret_flag = True


    if program_args.apply:
        valid_path = [out_expected_path, err_expected_path, gen_expected_path]
        program_args.auto_output_path = next(item for item in valid_path if item is not None)

    if out_expected_path and not check_std_output(
            out_expected_path, out_result_path, out_res_txt,
            result_manip=out_result_manip,
            program_args=program_args):
        ret_flag = False

    if program_args.apply:
        valid_path = [err_expected_path, out_expected_path, gen_expected_path]
        program_args.auto_output_path = next(item for item in valid_path if item is not None)

    if err_expected_path and not check_std_output(
            err_expected_path, err_result_path, err_res_txt,
            result_manip=err_result_manip,
            program_args=program_args):
        ret_flag = False

    if gen_expected_path and not check_generated_output(
            gen_expected_path, gen_result_path,
            result_manip=gen_result_manip,
            program_args=program_args):
        ret_flag = False

    return ret_flag


def clear_dir(path):
    """
    clears a directory by deleting and creating it again


    Parameters
    ----------------------------------------------------------------------------
    :param path:
        path of the directory


    :return: void
    """
    if isdir(path):
        rmtree(path)
    mkdir(path)


def file_find_string(search_string, file_path):
    """
    checks if a strings appears in a file


    Paramerters
    ----------------------------------------------------------------------------
    :param search_string: string
        string that is going to be searched

    :param file_path: string
        file in which the string is going to be searched

    :return: bool
    ----------------------------------------------------------------------------
        True if found, False otherwise
    """
    if isfile(file_path):
        with open(file_path, encoding="utf-8", newline="\n") as f:
            if search_string.lower() in f.read().lower():
                return True
    else:
        eprint("file_path is not a file: %s" % file_path)

    return False


def check_build_type(build_type, cmake_cache_path):
    """
    checks if a cmake build was of a certain single-configuration type


    Parameters:
    ----------------------------------------------------------------------------
    :param build_type: string
        the build type that is going to be expected

    :param cmake_cache_path: string
        the path of the to be checked CMakeCache.txt file


    :return: bool
    ----------------------------------------------------------------------------
    True if the right build type was used, False if not

    """

    check_string = "CMAKE_BUILD_TYPE:STRING=%s" % build_type

    if file_find_string(check_string, cmake_cache_path):
        return True

    eprint("CMAKE_BUILD_TYPE must be '%s'" % build_type)
    return False


def reg_replace(pattern, replacement):
    """
    returns a generated lambda function that applies a regex string replacement


    Parameters:
    ----------------------------------------------------------------------------

    :param pattern: regex pattern
        the pattern that will be used to find targets to replace

    :param replacement: string
        the replacement that will be applied


    :return: lambda function
    ----------------------------------------------------------------------------
        the generated lambda function, takes in a string on which the
        replacement will be applied and returned

    >>>  l = reg_replace(r"a", "b")
    >>>  a = l("a")
    'b'
    """
    return lambda text: re.sub(pattern, replacement, text)


def string_replace(string_target, replacement):
    """
    returns a generated lambda function that applies a string replacement

    like reg_replace, uses string.replace() instead
    """
    return lambda text: text.replace(string_target, replacement)


def s_path_join(path, *paths):
    """
    Wrapper for the os.path.join function, splits every path component to
    replace it wit a system specific path separator. This is for consistent
    path separators (and also systems that don't use either '\' or '/')


    Parameter
    ----------------------------------------------------------------------------
    :params path, paths: string
        see os.path.join

    :return: sting
    ----------------------------------------------------------------------------
        a joined path, see os.path.join

    >>> s_path_join('./z/d/', '../a/b/c/f')
    r'.\z\a\b\c\f'
    """
    p_splits = list(path_split(path))
    for r in map(path_split, paths):
        p_splits.extend(r)
    return path_join(*p_splits)


def main(args):
    # set working dir to script dir
    sc_dir = dirname(relpath(__file__))

    print("Debugging, python version: " , version)

    parser = argparse.ArgumentParser(description='Test CLI Options')
    parser.add_argument('--diff', help='show diffs when there is a test mismatch', action='store_true')
    parser.add_argument('--apply', help='auto apply the changes from the results folder to the output folder', action='store_true')

    parsed_args = parser.parse_args()

    parsed_args.diff = True
    parsed_args.input_file = ""
    # find the uncrustify binary (keep Debug dir excluded)
    bin_found = False
    uncr_bin = ''
    bin_paths = [s_path_join(sc_dir, '../../build/uncrustify'),
                 s_path_join(sc_dir, '../../build/Release/uncrustify'),
                 s_path_join(sc_dir, '../../build/Release/uncrustify.exe')]
    for uncr_bin in bin_paths:
        if not isfile(uncr_bin):
            eprint("is not a file: %s" % uncr_bin)
        else:
            print("Uncrustify binary found: %s" % uncr_bin)
            bin_found = True
            break
    if not bin_found:
        eprint("No Uncrustify binary found")
        sys_exit(EX_USAGE)

    '''
    Check if the binary was build as Release-type
    
    TODO: find a check for Windows,
          for now rely on the ../../build/Release/ location
    '''
    if os_name != 'nt' and not check_build_type(
                'release', s_path_join(sc_dir, '../../build/CMakeCache.txt')):
        sys_exit(EX_USAGE)

    clear_dir("./Results")

    return_flag = True

    #
    # Test help
    #   -h -? --help --usage
    if not check_output(
            uncr_bin,
            parsed_args,
            out_expected_path=s_path_join(sc_dir, 'Output/help.txt'),
            out_result_path=s_path_join(sc_dir, 'Results/help.txt'),
            out_result_manip=[
                string_replace(' --mtime      : Preserve mtime on replaced files.\n', ''),
                string_replace('.exe', '')]):
        #
        return_flag = False

    #
    # Test --show-config
    #
    if not check_output(
            uncr_bin,
            parsed_args,
            args_arr=['--show-config'],
            out_expected_path=s_path_join(sc_dir, 'Output/show_config.txt'),
            out_result_path=s_path_join(sc_dir, 'Results/show_config.txt'),
            out_result_manip=reg_replace(r'\# Uncrustify.+', '')):
        return_flag = False

    #
    # Test --update-config
    #
    if not check_output(
            uncr_bin,
            parsed_args,
            args_arr=['-c', s_path_join(sc_dir, 'Config/mini_d.cfg'),
                      '--update-config'],
            out_expected_path=s_path_join(sc_dir, 'Output/mini_d_uc.txt'),
            out_result_path=s_path_join(sc_dir, 'Results/mini_d_uc.txt'),
            out_result_manip=reg_replace(r'\# Uncrustify.+', ''),
            err_expected_path=s_path_join(sc_dir, 'Output/mini_d_error.txt'),
            err_result_path=s_path_join(sc_dir, 'Results/mini_d_error0.txt'),
            err_result_manip=string_replace('\\', '/')):
        return_flag = False

    if not check_output(
            uncr_bin,
            parsed_args,
            args_arr=['-c', s_path_join(sc_dir, 'Config/mini_nd.cfg'),
                      '--update-config'],
            out_expected_path=s_path_join(sc_dir, 'Output/mini_nd_uc.txt'),
            out_result_path=s_path_join(sc_dir, 'Results/mini_nd_uc.txt'),
            out_result_manip=reg_replace(r'\# Uncrustify.+', ''),
            err_expected_path=s_path_join(sc_dir, 'Output/mini_d_error.txt'),
            err_result_path=s_path_join(sc_dir, 'Results/mini_d_error1.txt'),
            err_result_manip=string_replace('\\', '/')):
        return_flag = False

    #
    # Test --update-config-with-doc
    #
    if not check_output(
            uncr_bin,
            parsed_args,
            args_arr=['-c', s_path_join(sc_dir, 'Config/mini_d.cfg'),
                      '--update-config-with-doc'],
            out_expected_path=s_path_join(sc_dir, 'Output/mini_d_ucwd.txt'),
            out_result_path=s_path_join(sc_dir, 'Results/mini_d_ucwd.txt'),
            out_result_manip=reg_replace(r'\# Uncrustify.+', ''),
            err_expected_path=s_path_join(sc_dir, 'Output/mini_d_error.txt'),
            err_result_path=s_path_join(sc_dir, 'Results/mini_d_error2.txt'),
            err_result_manip=string_replace('\\', '/')):
        return_flag = False

    if not check_output(
            uncr_bin,
            parsed_args,
            args_arr=['-c', s_path_join(sc_dir, 'Config/mini_nd.cfg'),
                      '--update-config-with-doc'],
            out_expected_path=s_path_join(sc_dir, 'Output/mini_nd_ucwd.txt'),
            out_result_path=s_path_join(sc_dir, 'Results/mini_nd_ucwd.txt'),
            out_result_manip=reg_replace(r'\# Uncrustify.+', ''),
            err_expected_path=s_path_join(sc_dir, 'Output/mini_d_error.txt'),
            err_result_path=s_path_join(sc_dir, 'Results/mini_d_error3.txt'),
            err_result_manip=string_replace('\\', '/')):
        return_flag = False

    #
    # Test -p
    #
    if not check_output(
            uncr_bin,
            parsed_args,
            args_arr=['-c', s_path_join(sc_dir, 'Config/mini_nd.cfg'),
                      '-f', s_path_join(sc_dir, 'Input/testSrc.cpp'),
                      '-p', s_path_join(sc_dir, 'Results/p.txt')],
            gen_expected_path=s_path_join(sc_dir, 'Output/p.txt'),
            gen_result_path=s_path_join(sc_dir, 'Results/p.txt'),
            gen_result_manip=reg_replace(r'\# Uncrustify.+[^\n\r]', '')):
        return_flag = False

    # Debug Options:
    #   -L
    # look at src/log_levels.h
    Ls_A = ['9', '21', '25', '28', '31', '36', '66', '92']
    for L in Ls_A:
        parsed_args.input_file = s_path_join(sc_dir, 'Input/testSrc.cpp') if L is '9' else ""
        if not check_output(
                uncr_bin,
                parsed_args,
                args_arr=['-c', NULL_DEVICE, '-L', L, '-o', NULL_DEVICE,
                          '-f', s_path_join(sc_dir, 'Input/testSrc.cpp')],
                err_expected_path=s_path_join(sc_dir, 'Output/%s.txt' % L),
                err_result_path=s_path_join(sc_dir, 'Results/%s.txt' % L),
                err_result_manip=reg_replace(r'[0-9]', '')):
            return_flag = False

    error_tests = ["I-842", "unmatched_close_pp"]
    for test in error_tests:
        if not check_output(
                uncr_bin,
                parsed_args,
                args_arr=['-q', '-c', s_path_join(sc_dir, 'Config/%s.cfg' % test),
                          '-f', s_path_join(sc_dir, 'Input/%s.cpp' % test),
                          '-o', NULL_DEVICE],
                err_expected_path=s_path_join(sc_dir, 'Output/%s.txt' % test),
                err_result_path=s_path_join(sc_dir, 'Results/%s.txt' % test)):
            return_flag = False

    if return_flag:
        print("all tests are OK")
        sys_exit(EX_OK)
    else:
        print("some problem(s) are still present")
        sys_exit(EX_SOFTWARE)


if __name__ == "__main__":
    main(argv[1:])
