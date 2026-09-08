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
    archive_names, file_paths = set(), set()
    for archive in manifest["archives"]:
        validate_record(archive, "name")
        if "/" in archive["name"] or not archive["name"].endswith(".zip"):
            raise ValueError("Archive name must be a plain .zip filename")
        if archive["name"] in archive_names:
            raise ValueError("Duplicate archive: " + archive["name"])
        archive_names.add(archive["name"])
        for entry in archive["files"]:
            validate_record(entry)
            if entry["path"] in file_paths:
                raise ValueError("Duplicate file path: " + entry["path"])
            file_paths.add(entry["path"])
    for duplicate in manifest.get("duplicates", []):
        validate_record(duplicate, "source")
        relative_path(duplicate["target"])
        if duplicate["target"] in file_paths:
            raise ValueError("Duplicate target path: " + duplicate["target"])
        file_paths.add(duplicate["target"])
    return manifest


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


def already_restored(target, record):
    if not target.exists():
        return False
    if not target.is_file():
        raise ValueError("Destination is not a regular file: " + str(target))
    with target.open("rb") as handle:
        if digest_stream(handle) != (record["bytes"], record["sha256"]):
            raise ValueError("Existing file has different contents; refusing overwrite: "
                             + str(target))
    return True


def install_stream(handle, destination, relative, record):
    target = safe_target(destination, relative)
    if already_restored(target, record):
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
            if not already_restored(safe_target(destination, relative), record):
                raise
        print("Restored: " + relative)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def restore_archive(path, archive, destination):
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
        # Verify destination conflicts before writing any file from this archive.
        for relative, record in expected.items():
            already_restored(safe_target(destination, relative), record)
        for relative, record in expected.items():
            with bundle.open(relative) as handle:
                install_stream(handle, destination, relative, record)


def restore_duplicates(manifest, destination):
    for duplicate in manifest.get("duplicates", []):
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


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archives", nargs="+", metavar="NAME.zip",
                        help="Restore only these archive names (default: all)")
    parser.add_argument("--from-dir", type=Path, metavar="PATH",
                        help="Use downloaded ZIP files from this directory instead of gh")
    parser.add_argument("--destination", type=Path, default=root, metavar="PATH",
                        help="Restore into this directory (default: repository root)")
    args = parser.parse_args()
    manifest = read_manifest(root / "docs" / "assets-manifest.json")
    archive_names = {archive["name"] for archive in manifest["archives"]}
    selected = set(args.archives) if args.archives else archive_names
    unknown = selected - archive_names
    if unknown:
        parser.error("Unknown archive(s): " + ", ".join(sorted(unknown)))
    destination = Path(os.path.abspath(args.destination))
    with tempfile.TemporaryDirectory(prefix="holly-assets-") as temporary:
        archive_dir = args.from_dir if args.from_dir is not None else Path(temporary)
        for archive in manifest["archives"]:
            if archive["name"] not in selected:
                continue
            print("Checking archive: " + archive["name"], flush=True)
            if args.from_dir is None:
                subprocess.run([
                    "gh", "release", "download", manifest["release_tag"],
                    "--repo", manifest["repository"], "--pattern", archive["name"],
                    "--dir", str(archive_dir),
                ], check=True)
            restore_archive(archive_dir / archive["name"], archive, destination)
        restore_duplicates(manifest, destination)
    print("Asset restoration complete.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile,
            subprocess.CalledProcessError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        sys.exit(1)
