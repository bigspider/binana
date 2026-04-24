#!/usr/bin/env python3

"""Verify that the README.md identifiers table matches the BIN-*.md files."""

import difflib
import glob
import os
import re
import sys


VALID_STATUSES = {"Draft", "Complete", "Deployed", "Closed"}


def parse_bin_file(path, errors):
    valid = True
    with open(path) as f:
        lines = f.readlines()

    filename_id = os.path.basename(path).removesuffix('.md')
    filename_year = filename_id.split('-')[1]
    dir_year = path.split('/')[0]

    m = re.match(r'\|\s*(BIN-\d{4}-\d{4})\s*\|\s*(.*)', lines[0])
    if not m:
        errors.append(f"{path}: could not parse header line")
        return None
    contents_id = m.group(1)
    name = m.group(2).strip()

    if contents_id != filename_id:
        errors.append(f"{path}: filename says {filename_id} but header says {contents_id}")
        valid = False

    if dir_year != filename_year:
        errors.append(f"{path}: in directory {dir_year}/ but filename says {filename_year}")
        valid = False

    status = None
    for line in lines:
        m = re.match(r'\|\s*Status\s*\|\s*(.*)', line)
        if m:
            status = m.group(1).strip()
            break

    if status is None:
        errors.append(f"{path}: no Status field found")
        valid = False
    elif status not in VALID_STATUSES:
        errors.append(f"{path}: invalid status '{status}' (expected one of {', '.join(sorted(VALID_STATUSES))})")
        valid = False

    return filename_id, name, status, valid


def generate_table(bin_files, errors):
    """Generate the expected identifiers table from BIN files."""
    entries = []
    for path in sorted(bin_files):
        parsed = parse_bin_file(path, errors)
        if parsed is None:
            continue
        bin_id, name, status, valid = parsed
        if not valid:
            continue
        link = f"[{name}]({path})"
        entries.append((bin_id, status, link))

    lines = []
    lines.append("| Identifier    | Status     | Name")
    lines.append("|:--------------|:-----------|:-----")
    for bin_id, status, link in entries:
        lines.append(f"| {bin_id} | {status:<10s} | {link}")
    return lines


def replace_readme_table(readme_lines, table_lines):
    """Return readme_lines with the identifiers table replaced by table_lines."""
    result = []
    in_table = False
    replaced = False
    for line in readme_lines:
        if not in_table and line.startswith("| Identifier"):
            in_table = True
            replaced = True
            result.extend(table_lines)
            continue
        if in_table:
            if line.startswith("|"):
                continue
            in_table = False
        result.append(line)
    if not replaced:
        result.extend([""] + table_lines)
    return result


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    bin_files = sorted(glob.glob("*/BIN-*.md"))

    with open("README.md") as f:
        readme_lines = f.read().splitlines()

    errors = []
    table = generate_table(bin_files, errors)
    expected = replace_readme_table(readme_lines, table)

    diff = []
    if expected != readme_lines:
        diff = list(difflib.unified_diff(
            readme_lines, expected,
            fromfile="a/README.md",
            tofile="b/README.md",
            lineterm="",
        ))
        errors.append("README.md identifiers table is out of date")

    for e in errors:
        print(f"ERROR: {e}")
    if diff:
        print("")
        for line in diff:
            print(line)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
