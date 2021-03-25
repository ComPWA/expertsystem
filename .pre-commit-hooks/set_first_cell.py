# cspell:ignore nargs
"""Add install statements to first cell in a Jupyter notebook.

Google Colaboratory does not install a package automatically, so this has to be
done through a code cell. At the same time, this cell needs to be hidden from
the documentation pages, when viewing through Jupyter Lab (Binder), and when
viewing Jupyter slides.

Additionally, this scripts sets the IPython InlineBackend.figure_formats option
to SVG. This is because the Sphinx configuration can't set this externally.
"""

import argparse
import configparser
import json
import sys
import textwrap
from typing import List, Optional, Sequence

import nbformat  # type: ignore

cfg = configparser.ConfigParser()
cfg.read("setup.cfg")

PACKAGE_NAME = cfg["metadata"]["name"]
EXPECTED_CELL_CONTENT = f"""
%%capture
%config Completer.use_jedi = False
%config InlineBackend.figure_formats = ['svg']

# Install on Google Colab
import sys  # noqa: F401

!{{sys.executable}} -m pip freeze | grep {PACKAGE_NAME} || {{sys.executable}} -m pip install {PACKAGE_NAME}
"""

EXPECTED_CELL_METADATA = {
    "jupyter": {"source_hidden": True},
    "slideshow": {"slide_type": "skip"},
    "tags": ["remove-cell"],
}


class WrongCellContent(ValueError):
    pass


class WrongMetadata(ValueError):
    pass


def check_first_cell(filename: str, expected_content: str) -> None:
    notebook = nbformat.read(filename, as_version=4)
    first_cell = notebook.cells[0]
    cell_content = "".join(first_cell.source)
    cell_content = cell_content.strip("\n")
    expected_cell_content = expected_content.strip("\n")
    if cell_content != expected_cell_content:
        raise WrongCellContent(filename)
    if first_cell.metadata != EXPECTED_CELL_METADATA:
        raise WrongMetadata(filename)


def fix_first_cell(
    filename: str, new_content: str, replace: bool = False
) -> None:
    notebook = nbformat.read(filename, as_version=nbformat.NO_CONVERT)
    new_cell = nbformat.v4.new_code_cell(
        new_content,
        metadata=EXPECTED_CELL_METADATA,
    )
    del new_cell["id"]  # following nbformat_minor = 4
    if replace:
        notebook["cells"][0] = new_cell
    else:
        notebook["cells"] = [new_cell] + notebook["cells"]
    nbformat.validate(notebook)
    nbformat.write(notebook, filename)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    parser.add_argument(
        "--additional_packages",
        type=str,
        help="Additional packages to be installed through the first notebook cell",
    )
    parser.add_argument(
        "--autofix",
        action="store_true",
        help="Automatically fix first cell in the notebook.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace first cell instead of prepending a new cell.",
    )
    args = parser.parse_args(argv)

    expected_cell_content = EXPECTED_CELL_CONTENT.strip("\n")
    for package in args.additional_packages.split(","):
        # pylint: disable=line-too-long
        expected_cell_content += f"\n!{{sys.executable}} -m pip freeze | grep {package} || {{sys.executable}} -m pip install {package}"

    exit_code = 0
    wrong_content_files: List[str] = []
    wrong_metadata_files: List[str] = []
    for filename in args.filenames:
        try:
            check_first_cell(filename, expected_cell_content)
        except ValueError as exception:
            if args.autofix:
                fix_first_cell(filename, expected_cell_content, args.replace)
            if isinstance(exception, WrongCellContent):
                wrong_content_files.append(filename)
            if isinstance(exception, WrongMetadata):
                wrong_metadata_files.append(filename)
            exit_code = 1
    if exit_code != 0 and not args.autofix:
        if wrong_content_files or wrong_metadata_files:
            print("First cells in notebooks should follow a certain standard.")
            if wrong_content_files:
                print("Cell content problems for notebooks:")
                print(" ", *wrong_content_files, sep="\n ")
                print("\nCell content should be:")
                print(textwrap.indent(EXPECTED_CELL_CONTENT, prefix="  "))
            if wrong_metadata_files:
                print("Metadata problems for notebooks:")
                print(" ", *wrong_metadata_files, sep="\n ")
                print("\nMetadata should be:\n")
                print(
                    textwrap.indent(
                        json.dumps(EXPECTED_CELL_METADATA, indent=2),
                        prefix="  ",
                    )
                )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
