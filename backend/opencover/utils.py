# coding=utf-8
import re

""" Helper methods to access xml elements """


def get_module_name(module):
    return next(module.iter("ModuleName")).text


def get_module_tracked_methods(module):
    return next(module.iter("TrackedMethods"))


def get_module_classes(module):
    return next(module.iter("Classes"))


def get_module_files(module):
    return next(module.iter("Files"))


def get_class_methods(clazz):
    return next(clazz.iter("Methods"))


def get_method_name(method):
    return next(method.iter("Name")).text


def get_method_file_ref(method):
    return next(method.iter("FileRef"), None)


def is_relevant_method(method):
    # relevant -> not lambda, not constructors or not other generated things
    # name = get_method_name(method)
    # regexes = [
    #     "<.*>f__AnonymousType.*::",
    #     "::.ctor()",
    #     "::.cctor()",
    #     "<.*>b__.*",
    #     "<.*>d__.*::",
    #     "<.*>c__DisplayClass",
    #     "<.*>c::",
    #     ".*::get_.*()",
    #     ".*::set_.*()",
    #     ".*::.*.get_.*()",
    #     ".*::.*.set_.*()",
    # ]
    # combined = "(" + ")|(".join(regexes) + ")"

    # if re.search(combined, name):
    #     # print(f"Some regex matched! --> {name}")
    #     return False
    return True


def get_method_coverage(method):
    # get method point tag
    method_point = next(method.iter("MethodPoint"), None)
    if method_point is None or not list(method_point):
        return [None, None]

    # look at tracked method refs
    tracked_refs = method_point[0]
    if not list(tracked_refs):
        return [None, None]

    # return uids of tests that visit the 1st sequence point
    tests_uids = list(map(lambda x: x.attrib["uid"], tracked_refs))

    return [get_method_name(method), tests_uids]
