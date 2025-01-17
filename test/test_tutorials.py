"""Unit tests for the tutorials."""

import glob
import os
import subprocess
import tempfile


def _exec_tutorial(path):
    """Execute a tutorial notebook.

    Parameters
    ----------
    path : str
        The path to the tutorial.
    """
    file_name = tempfile.NamedTemporaryFile(suffix=".ipynb").name
    args = [
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        "--ExecutePreprocessor.timeout=1000",
        "--ExecutePreprocessor.kernel_name=python3",
        "--output",
        file_name,
        path,
    ]
    subprocess.check_call(args)


class TutorialsParametrizer(type):
    def __new__(cls, name, bases, attrs):
        def _create_new_test(path):
            def new_test(self):
                return _exec_tutorial(path=path)

            return new_test

        paths = locals()["attrs"].get("paths")

        for path in paths:
            name = path.split(os.sep)[-1].split(".")[0]

            test_func = _create_new_test(path)
            func_name = f"test_{name}"

            attrs[func_name] = test_func

        return super().__new__(cls, name, bases, attrs)


class TestTutorial(metaclass=TutorialsParametrizer):
    paths = sorted(glob.glob("tutorials/*.ipynb"))
