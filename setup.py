from os.path import isdir, isfile, join
from platform import system

from setuptools import Extension, find_packages, setup
from setuptools.command.build import build
from wheel.bdist_wheel import bdist_wheel


class Build(build):
    def run(self):
        if isdir("queries"):
            dest = join(self.build_lib, "tree_sitter_al", "queries")
            self.copy_tree("queries", dest)
        # The traversal policy (roadmap F0): one data file shared by every binding.
        if isfile(join("traversal", "policy.json")):
            self.mkpath(join(self.build_lib, "tree_sitter_al"))
            self.copy_file(join("traversal", "policy.json"),
                           join(self.build_lib, "tree_sitter_al", "traversal_policy.json"))
        super().run()


class BdistWheel(bdist_wheel):
    def get_tag(self):
        python, abi, platform = super().get_tag()
        if python.startswith("cp"):
            python, abi = "cp312", "abi3"
        return python, abi, platform


setup(
    packages=find_packages("bindings/python"),
    package_dir={"": "bindings/python"},
    package_data={
        "tree_sitter_al": ["*.pyi", "py.typed", "traversal_policy.json"],
        "tree_sitter_al.queries": ["*.scm"],
    },
    ext_package="tree_sitter_al",
    ext_modules=[
        Extension(
            name="_binding",
            sources=[
                "bindings/python/tree_sitter_al/binding.c",
                "src/parser.c",
                "src/scanner.c",
            ],
            extra_compile_args=[
                "-std=c11",
                "-fvisibility=hidden",
            ] if system() != "Windows" else [
                "/std:c11",
                "/utf-8",
            ],
            define_macros=[
                ("Py_LIMITED_API", "0x030C0000"),
                ("PY_SSIZE_T_CLEAN", None),
                ("TREE_SITTER_HIDE_SYMBOLS", None),
            ],
            include_dirs=["src"],
            py_limited_api=True,
        )
    ],
    cmdclass={
        "build": Build,
        "bdist_wheel": BdistWheel
    },
    zip_safe=False
)
