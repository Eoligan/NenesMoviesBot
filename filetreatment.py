"""Methods for file treatment"""
import re
from collections import deque


def read_file(func):
    """Decorator for reading the file"""

    def a_wrapper(file, *args):
        with open(file, "r", encoding="utf8") as file:  # type: ignore
            return func(file, *args)

    return a_wrapper


def append_file(func):
    """Decorator for writing the file"""

    def a_wrapper(file, *args):
        with open(file, "a", encoding="utf8") as file:
            return func(file, *args)

    return a_wrapper


def read_write_file(func):
    """Decorator for r/w the file"""

    def a_wrapper(file, *args):
        with open(file, "r+", encoding="utf8") as file:
            return func(file, *args)

    return a_wrapper


@read_file
def len_(file):
    """Function that returns the length of the file"""
    return sum(1 for line in file)


@read_file
def list_(file):
    """Function that lists for any file"""
    list_return = file.readlines()
    return list_return


@read_file
def find_(file, req):
    """Function that finds movie/serie requested"""
    found_list = []
    for line in file:
        if re.search(" ".join(str(i) for i in req), line, flags=re.IGNORECASE):
            found_list.append(line)
    return found_list


@read_file
def find_last(file):
    """Function that returns las 10 movies/series"""
    return deque(file, 10)


@read_file
def find_pos(file, pos):
    """Function that finds movie/serie given a position"""
    lines = file.readlines()
    return (pos, lines[pos - 1][6:])


@append_file
def add(file, text, pos):
    """Function that adds movie/serie requested"""
    file.write(f"{pos:03d}--- {text}\n")


@read_write_file
def edit(file, text, pos: int):
    """Function that edit in any file"""
    lines = file.readlines()
    lines[pos - 1] = f"{pos:03d}--- {text}\n"
    file.seek(0)
    file.truncate()
    file.writelines(lines)


@read_write_file
def del_(file, pos: int):
    """Function that delete in any file by position"""
    lines = file.readlines()
    lines.pop(pos - 1)

    for i, txt in enumerate(lines[pos - 1 :]):
        lines[i + pos - 1] = f"{i+pos:03d}{txt[3:]}"

    file.seek(0)
    file.truncate()
    file.writelines(lines)


@read_write_file
def del_last(file):
    """Function that delete the last item in any file"""
    lines = file.readlines()
    lines.pop()
    file.seek(0)
    file.truncate()
    file.writelines(lines)


def which_file(filename) -> str:
    """Function that returns the worked file"""
    name = re.split(r"\/|\.", filename)
    return name[4].upper()
