"""Organize files in a directory by extension.
"""

import asyncio
import glob
import os
import pathlib as _pathlib
from collections import namedtuple
import shutil

import aiofiles.os

_FileMap = namedtuple("_FileMap", ["extension", "path"])


def time_it(func):
    """Decorator to time the execution of a function.

    Args:
        func (function): Function to be timed.

    Returns:
        function: The timed function.

    """

    def wrapper(*args, **kwargs):
        import cProfile
        import pstats
        import time

        profile = cProfile.Profile()
        start = time.time()
        profile.enable()
        result = func(*args, **kwargs)
        profile.disable()
        print(f"{func.__name__} took {time.time() - start} seconds to execute.")

        # Print the profile
        stats = pstats.Stats(profile).sort_stats("cumulative")
        stats.print_stats(10)

        return result

    return wrapper


def glob_scan(directory) -> list[_FileMap]:
    """Scan directory for files and group by extension"""
    mapping = []
    for file_ in glob.glob(f"{directory}/**", recursive=True):
        path = _pathlib.Path(file_)

        fp = _FileMap(extension=path.suffix[1:].lower(), path=path)
        mapping.append(fp)
    return mapping


def walk_scan(directory) -> list[_FileMap]:
    """Scan directory for files and group by extension"""
    mapping = []
    for root, _, files in os.walk(directory):
        for file_ in files:
            path = _pathlib.Path(root) / file_
            fp = _FileMap(extension=path.suffix[1:].lower(), path=path)
            mapping.append(fp)
    return mapping


async def async_map_walk(directory):
    # Walk the directory and if the file is a file, return the FileMap
    mapping = []
    for scanned_directory in await aiofiles.os.scandir(directory):
        # Check if the directory is a file
        if scanned_directory.is_file():
            path = _pathlib.Path(scanned_directory.path)
            extension = path.suffix[1:].lower()
            if extension == "xmp":
                extension = os.path.splitext(path.stem)[1][1:].lower()
            fp = _FileMap(extension=extension, path=path)
            mapping.append(fp)
            continue
        # If the directory is a directory, walk it
        mapping.extend(await async_map_walk(scanned_directory.path))

    return mapping


async def async_level_scan(directory):
    """Scan directory for files and group by extension"""

    directory = _pathlib.Path(directory)

    mapping = await async_map_walk(directory)

    return mapping


async def async_relocate(directory: str | _pathlib.Path, mapping: list[_FileMap], version_up: bool = False):
    """Relocate files to new directory asynchronously.

    Args:
        directory (str): Directory to relocate files to.
        mapping (list): List of files to relocate.
    """
    directory = _pathlib.Path(directory)
    for file_map in mapping:
        new_directory = directory / file_map.extension
        await aiofiles.os.makedirs(new_directory, exist_ok=True)

        # Check if the file already exists
        version = 1
        clean_stem = file_map.path.stem.split("_v")[0]
        new_file = new_directory / f"{clean_stem}_v{version:03d}{file_map.path.suffix}".replace(" ", "").replace(
            "-", "_"
        )

        if not version_up and new_file.exists():
            print(f"Skipping {file_map.path} as {new_file} already exists")
            continue
        if version_up:
            while await aiofiles.os.path.exists(new_file):
                version += 1
                new_file = new_directory / f"{file_map.path.stem}_v{version:03d}{file_map.path.suffix}"
        await aiofiles.os.rename(file_map.path, new_file)

    return True


async def directory_cleanup(directory: str | _pathlib.Path):
    """Clean up empty directories in a directory.

    Args:
        directory (str): Directory to clean up.
    """
    directory = _pathlib.Path(directory)

    for sub_directory in directory.iterdir():
        # Check if the file has any files
        if sub_directory.is_dir() and list(sub_directory.iterdir()):
            await directory_cleanup(sub_directory)
            continue
        elif sub_directory.is_dir():
            # print(f"Removing {sub_directory}")
            await aiofiles.os.rmdir(sub_directory)
            continue


if __name__ == "__main__":
    top_directory = "/mnt/e/GH5"

    # Really slow - glob_scan took 1.5275776386260986 seconds to execute.
    # glob_scan_mapping = glob_scan(top_directory)
    # print(len(glob_scan_mapping))

    async_mapping = asyncio.run(async_level_scan(top_directory))

    # relocate(top_directory, walk_scan_mapping)
    from pprint import pprint as pp

    pp(async_mapping)

    asyncio.run(async_relocate(top_directory, async_mapping))

    asyncio.run(directory_cleanup(top_directory))
