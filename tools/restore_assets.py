#!/usr/bin/env python3
"""Restore verified Blender assets from GitHub Release archives (Python 3 stdlib)."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile


CHUNK_SIZE = 1024 * 1024


def relative_path(value):
    if (not isinstance(value, str) or not value or "\\" in value
            or "\x00" in value or ":" in value
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ValueError("Unsafe relative path: {!r}".format(value))
    return Path(*value.split("/"))


def validate_record(record, path_key="path"):
    relative_path(record[path_key])
    if type(record["bytes"]) is not int or record["bytes"] < 0:
        raise ValueError("Invalid byte count for " + record[path_key])
    if not isinstance(record["sha256"], str) or not re.fullmatch(
            r"[0-9a-f]{64}", record["sha256"]):
        raise ValueError("Invalid SHA256 for " + record[path_key])


def read_manifest(path):
    with path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest["schema_version"] != 1:
        raise ValueError("Unsupported manifest schema_version")
    if not isinstance(manifest["repository"], str) or not isinstance(
            manifest["release_tag"], str):
        raise ValueError("Invalid repository or release tag")
    archive_names, file_versions = set(), {}
    for archive in manifest["archives"]:
        validate_record(archive, "name")
        if "/" in archive["name"] or not archive["name"].endswith(".zip"):
            raise ValueError("Archive name must be a plain .zip filename")
        if archive["name"] in archive_names:
            raise ValueError("Duplicate archive: " + archive["name"])
        archive_names.add(archive["name"])
        if "release_tag" in archive and (
                not isinstance(archive["release_tag"], str) or not archive["release_tag"]):
            raise ValueError("Invalid release tag for " + archive["name"])
        archive_paths = set()
        for entry in archive["files"]:
            validate_record(entry)
            relative = entry["path"]
            if relative in archive_paths:
                raise ValueError("Duplicate file path in archive: " + relative)
            archive_paths.add(relative)
            previous = file_versions.get(relative)
            if previous is None:
                if "replaces_sha256" in entry:
                    raise ValueError("Replacement has no earlier version: " + relative)
            elif entry.get("replaces_sha256") != previous["sha256"]:
                raise ValueError("Replacement must match the previous SHA256: " + relative)
            file_versions[relative] = entry
    extensions = {}
    for archive in manifest["archives"]:
        if "extends_archive" not in archive:
            continue
        parent = archive["extends_archive"]
        if not isinstance(parent, str) or parent not in archive_names:
            raise ValueError("Unknown extended archive for " + archive["name"])
        extensions[archive["name"]] = parent
    # Validate the whole graph, even if this invocation selects only one archive.
    checked = set()
    for name in archive_names:
        chain = set()
        while name in extensions and name not in checked:
            if name in chain:
                raise ValueError("Archive extension cycle: " + name)
            chain.add(name)
            name = extensions[name]
        checked.update(chain)
    file_paths = set(file_versions)
    for duplicate in manifest.get("duplicates", []):
        validate_record(duplicate, "source")
        relative_path(duplicate["target"])
        if duplicate["target"] in file_paths:
            raise ValueError("Duplicate target path: " + duplicate["target"])
        file_paths.add(duplicate["target"])
    return manifest


def restore_plan(manifest, requested=None):
    """Select descendants and derive owners and validated same-path predecessors."""
    archive_names = {archive["name"] for archive in manifest["archives"]}
    selected = set(requested) if requested is not None else set(archive_names)
    unknown = selected - archive_names
    if unknown:
        raise ValueError("Unknown archive(s): " + ", ".join(sorted(unknown)))
    while True:
        additions = {archive["name"] for archive in manifest["archives"]
                     if archive.get("extends_archive") in selected}
        if additions <= selected:
            break
        selected.update(additions)
    owners, predecessors, history = {}, {}, {}
    for archive in manifest["archives"]:
        for entry in archive["files"]:
            relative = entry["path"]
            previous = history.setdefault(relative, [])
            if archive["name"] in selected:
                owners[relative] = archive["name"]
                # read_manifest has checked every link, including unselected ones.
                predecessors[relative] = tuple(previous)
            previous.append((entry["bytes"], entry["sha256"]))
    return selected, owners, predecessors


def digest_stream(handle):
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = handle.read(CHUNK_SIZE)
        if not chunk:
            break
        size += len(chunk)
        digest.update(chunk)
    return size, digest.hexdigest()


def verify_stream(handle, record, label):
    if digest_stream(handle) != (record["bytes"], record["sha256"]):
        raise ValueError("Size or SHA256 mismatch: " + label)


def safe_target(destination, relative):
    target = destination / relative_path(relative)
    # Inspect the destination's ancestors too; resolving paths would hide symlinks.
    for component in reversed((target,) + tuple(target.parents)):
        try:
            mode = component.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise ValueError("Refusing symlink in destination: " + str(component))
        if component != target and not stat.S_ISDIR(mode):
            raise ValueError("Destination parent is not a directory: " + str(component))
    return target


def already_restored(target, record, predecessors=()):
    if not target.exists():
        return False
    if not target.is_file():
        raise ValueError("Destination is not a regular file: " + str(target))
    with target.open("rb") as handle:
        current = digest_stream(handle)
    if current == (record["bytes"], record["sha256"]):
        return True
    if current in predecessors:
        return False
    raise ValueError("Existing file has different contents; refusing overwrite: "
                     + str(target))


def install_stream(handle, destination, relative, record, predecessors=()):
    target = safe_target(destination, relative)
    if already_restored(target, record, predecessors):
        print("Already present: " + relative)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    safe_target(destination, relative)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".restore-", dir=target.parent,
                                         delete=False) as output:
            temporary = Path(output.name)
            shutil.copyfileobj(handle, output, CHUNK_SIZE)
        with temporary.open("rb") as saved:
            verify_stream(saved, record, relative)
        temporary.chmod(0o644)
        safe_target(destination, relative)
        try:
            # Creating a hard link is atomic and cannot overwrite an existing file.
            os.link(temporary, target)
        except FileExistsError:
            target = safe_target(destination, relative)
            before = target.lstat()
            if already_restored(target, record, predecessors):
                print("Already present: " + relative)
                return
            after = safe_target(destination, relative).lstat()
            signature = lambda value: (value.st_dev, value.st_ino, value.st_size,
                                       value.st_mtime_ns, value.st_ctime_ns)
            if signature(before) != signature(after):
                raise ValueError("Destination changed during verification: " + str(target))
            # Only a same-path predecessor from the validated manifest can reach
            # this branch. The verified replacement becomes visible atomically.
            os.replace(temporary, target)
            print("Updated: " + relative)
            return
        print("Restored: " + relative)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def restore_archive(path, archive, destination, owners=None, predecessors=None):
    with path.open("rb") as handle:
        verify_stream(handle, archive, archive["name"])
    expected = {entry["path"]: entry for entry in archive["files"]}
    with zipfile.ZipFile(path) as bundle:
        seen = set()
        actual_files = set()
        for entry in bundle.infolist():
            relative_path(entry.filename.rstrip("/") if entry.is_dir() else entry.filename)
            if entry.filename in seen:
                raise ValueError("Duplicate ZIP entry: " + entry.filename)
            seen.add(entry.filename)
            kind = stat.S_IFMT(entry.external_attr >> 16)
            if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("ZIP contains a symlink or special file: " + entry.filename)
            if entry.is_dir():
                continue
            if kind == stat.S_IFDIR or entry.filename not in expected:
                raise ValueError("Unexpected ZIP file: " + entry.filename)
            actual_files.add(entry.filename)
            record = expected[entry.filename]
            if entry.file_size != record["bytes"]:
                raise ValueError("ZIP entry size mismatch: " + entry.filename)
            with bundle.open(entry) as handle:
                verify_stream(handle, record, entry.filename)
        if actual_files != set(expected):
            raise ValueError("ZIP is missing manifest files: "
                             + ", ".join(sorted(set(expected) - actual_files)))
        effective = {relative: record for relative, record in expected.items()
                     if owners is None or owners.get(relative) == archive["name"]}
        predecessors = predecessors or {}
        # Validate the entire ZIP above, including superseded members. Only the
        # selected final owner participates in destination checks or installation.
        for relative, record in effective.items():
            already_restored(safe_target(destination, relative), record,
                             predecessors.get(relative, ()))
        for relative, record in effective.items():
            with bundle.open(relative) as handle:
                install_stream(handle, destination, relative, record,
                               predecessors.get(relative, ()))


def restore_duplicates(manifest, destination, selected_paths=None):
    eligible = set(selected_paths) if selected_paths is not None else None
    for duplicate in manifest.get("duplicates", []):
        if eligible is not None and duplicate["source"] not in eligible:
            continue
        source = safe_target(destination, duplicate["source"])
        if not source.exists():
            print("Skipped duplicate (source not restored): " + duplicate["target"])
            continue
        if not source.is_file():
            raise ValueError("Duplicate source is not a file: " + str(source))
        with source.open("rb") as handle:
            verify_stream(handle, duplicate, duplicate["source"])
            handle.seek(0)
            install_stream(handle, destination, duplicate["target"], duplicate)
        if eligible is not None:
            eligible.add(duplicate["target"])


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archives", nargs="+", metavar="NAME.zip",
                        help="Restore these archives and their extensions (default: all)")
    parser.add_argument("--from-dir", type=Path, metavar="PATH",
                        help="Use downloaded ZIP files from this directory instead of gh")
    parser.add_argument("--destination", type=Path, default=root, metavar="PATH",
                        help="Restore into this directory (default: repository root)")
    args = parser.parse_args()
    manifest = read_manifest(root / "docs" / "assets-manifest.json")
    try:
        selected, owners, predecessors = restore_plan(manifest, args.archives)
    except ValueError as error:
        parser.error(str(error))
    destination = Path(os.path.abspath(args.destination))
    with tempfile.TemporaryDirectory(prefix="holly-assets-") as temporary:
        archive_dir = args.from_dir if args.from_dir is not None else Path(temporary)
        for archive in manifest["archives"]:
            if archive["name"] not in selected:
                continue
            print("Checking archive: " + archive["name"], flush=True)
            if args.from_dir is None:
                subprocess.run([
                    "gh", "release", "download", archive.get("release_tag", manifest["release_tag"]),
                    "--repo", manifest["repository"], "--pattern", archive["name"],
                    "--dir", str(archive_dir),
                ], check=True)
            restore_archive(archive_dir / archive["name"], archive, destination,
                            owners, predecessors)
        restore_duplicates(manifest, destination, owners)
    print("Asset restoration complete.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile,
            subprocess.CalledProcessError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        sys.exit(1)
