import math
import os
import sys
from enum import IntFlag
from pathlib import Path
from zlib import decompress

from ZombieArmy4Loader.archive import Archive
from ZombieArmy4Loader.byte_io_ac import ByteIO, get_pad


class ArchiveFlags(IntFlag):
    CHUNKS = 1 << 0
    ZIP = 1 << 1


# archive = Path(r"D:\SteamLibrary\steamapps\common\ZombieArmy4\misc\common.asr")
base_path = Path(r"D:\SteamLibrary\steamapps\common\ZombieArmy4\misc")
archive_dump_dir = Path(r"D:\SteamLibrary\steamapps\common\ZombieArmy4\UNPACK")
for archive in base_path.rglob('common.asr'):

    arc = Archive(archive)
    # print(arc.get_used_chunk_types())
    arc.extract_files(archive_dump_dir, True)
    # archive_dump_dir = archive_dump_dir / archive.stem
    # HSKL - links to .model file
    # HMPT - Attachments maybe?
    # SDSM - references some wav files
    # TTXT - merged icon textures, defines boundaries of each merged icon
    # FX** - seems to be related to particles and FX stuff
