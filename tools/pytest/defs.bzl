load("@pip//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_test")

def pytest_test(name, srcs, deps = [], **kwargs):
    py_test(
        name = name,
        srcs = srcs + ["//tools/pytest:__test__.py"],
        main = "__test__.py",
        args = ["$(location %s)" % src for src in srcs],
        deps = deps + [requirement("pytest")],
        **kwargs,
    )
