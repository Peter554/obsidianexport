import argparse
import collections
import logging
import pathlib
import re
import shutil

_INTERNAL_LINK_PATTERN = re.compile(r"\[\[([\w \-\.\/]+)(?:[#^|].*)?\]\]")


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("file")
    arg_parser.add_argument("outdir")
    arg_parser.add_argument("--dryrun", default=False, action="store_true")
    arg_parser.add_argument("--verbose", default=False, action="store_true")
    args = arg_parser.parse_args()

    dryrun = args.dryrun
    verbose = args.verbose

    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING)

    file = pathlib.Path(args.file)
    if not file.is_file():
        raise ValueError(f"{file} is not a file")

    outdir = pathlib.Path(args.outdir)
    if (
        not dryrun
        and outdir.exists()
        # If the output path already exists, then
        # make sure that it is an empty directory.
        and not (outdir.is_dir() and not list(outdir.iterdir()))
    ):
        raise ValueError(f"{outdir} is not an empty directory")

    try:
        vault = [p for p in file.parents if (p / ".obsidian").is_dir()][0]
    except KeyError as e:
        raise ValueError(f"{file} is not within an obsidian vault") from e

    q = collections.deque([file])
    files_to_export = set()
    while q:
        file = q.popleft()
        if file in files_to_export:
            continue
        files_to_export.add(file)
        if file.suffix != ".md":
            continue
        with open(file) as f:
            file_content = f.read()
        for match in _INTERNAL_LINK_PATTERN.finditer(file_content):
            linked_file = vault / match.group(1)
            if not linked_file.suffix:
                linked_file = vault / (match.group(1) + ".md")
            q.append(linked_file)

    for file_to_export in sorted(files_to_export):
        exportfile = outdir / file_to_export.relative_to(vault)
        logging.info(f"Exporting {file_to_export} to {exportfile}")
        if dryrun:
            continue
        exportfile.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file_to_export, exportfile)
