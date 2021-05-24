import math
import os
import sys
from enum import IntFlag
from pathlib import Path
from zlib import decompress
from ZombieArmy4Loader.byte_io_ac import ByteIO, get_pad


class ArchiveFlags(IntFlag):
    CHUNKS = 1 << 0
    ZIP = 1 << 1


# archive = Path(r"D:\SteamLibrary\steamapps\common\ZombieArmy4\misc\common.asr")
base_path = Path(r"D:\SteamLibrary\steamapps\common\ZombieArmy4\sounds")
archive_dump_dir = Path(r"D:\SteamLibrary\steamapps\common\ZombieArmy4\UNPACK")
dump_chunks = True
override_files = False
for archive in base_path.rglob('*.asr.pc.streamsounds'):
    # archive_dump_dir = archive_dump_dir / archive.stem
    # HSKL - links to .model file
    # HMPT - Attachments maybe?
    # SDSM - references some wav files
    # TTXT - merged icon textures, defines boundaries of each merged icon
    # FX** - seems to be related to particles and FX stuff

    flags = ArchiveFlags(0)

    reader = ByteIO(archive)

    archive_size = reader.size()
    magic = reader.read_ascii_string(8)
    offset = 0
    compressed_size = 0
    decompressed_size = 0
    if magic == 'AsuraCmp':
        offset = 8
        flags |= ArchiveFlags.ZIP
        raise NotImplementedError(f'{magic} is not supported')
    elif magic == 'AsuraZlb':
        flags |= ArchiveFlags.ZIP
        offset = 0x14
        reader.skip(4)
    elif magic == 'AsuraZbb':
        flags |= ArchiveFlags.CHUNKS
        flags |= ArchiveFlags.ZIP
        compressed_size = reader.read_uint32()
        decompressed_size = reader.read_uint32()

    decomp_archive = archive.with_suffix('.decompressed')

    if not decomp_archive.exists() or (decomp_archive.exists() and decomp_archive.stat().st_size != decompressed_size):
        with decomp_archive.open('wb') as decompressed_file:
            if flags & ArchiveFlags.ZIP:
                decompressed_buffer = ByteIO(decompressed_file)
                start = reader.tell()
                block_id = 0
                while reader:
                    compressed_block_size = reader.read_uint32()
                    decompressed_block_size = reader.read_uint32()
                    print(f'Decompessing block {block_id} {compressed_block_size}:{decompressed_block_size}')
                    if not (flags & ArchiveFlags.CHUNKS):
                        compressed_block_size = archive_size
                        compressed_block_size -= offset
                    decompressed_block = decompress(reader.read(compressed_block_size))
                    assert len(decompressed_block) == decompressed_block_size
                    block_id += 1
                    decompressed_buffer.write_bytes(decompressed_block)

                assert decompressed_buffer.size() == decompressed_size

    if magic != 'Asura   ':
        archive_path = decomp_archive
    else:
        archive_path = archive

    with archive_path.open('rb') as file:
        reader = ByteIO(file)
        magic = reader.read_ascii_string(8)

        if magic != 'Asura   ':
            raise NotImplementedError(f'Unknown header {magic}')

        os.makedirs((archive_dump_dir / 'chunks'), exist_ok=True)

        chunk_types = set()

        while reader:
            chunk_start = reader.tell()
            if chunk_start + 4 == reader.size():
                break
            chunk_name = reader.read_ascii_string(4).strip()
            chunk_size = reader.read_uint32()
            chunk_version = reader.read_int32()
            chunk_unk = reader.read_uint32()
            print(f'Found chunk {chunk_name} size:{chunk_size} version:{chunk_version}')

            chunk_types.add(chunk_name)

            if chunk_name == 'RSCF':
                ctype = reader.read_uint32()
                dummy = reader.read_uint32()
                size = reader.read_uint32()
                filename = reader.read_ascii_padded()
                print(f'Found embedded file {ctype}: {filename} ')
                if filename[0] == '\\':
                    filename = filename[1:]
                filename = Path(filename)
                if ctype == 2:
                    filename = filename.with_suffix('.dds')
                elif ctype == 0:
                    filename = filename.with_suffix('.model')
                else:
                    print(f'Found unknown CTYPE {ctype}')

                os.makedirs((archive_dump_dir / filename).parent, exist_ok=True)
                if (archive_dump_dir / filename).exists():
                    f_size = (archive_dump_dir / filename).stat().st_size
                    if f_size < size:
                        print(f'Found larger version of {filename}')
                        with (archive_dump_dir / filename).open('wb') as f:
                            f.write(reader.read(size))
                else:
                    with (archive_dump_dir / filename).open('wb') as f:
                        f.write(reader.read(size))
            elif chunk_name == 'RSFL':
                filename_count = reader.read_uint32()
                for _ in range(filename_count):
                    filename = reader.read_ascii_padded()
                    if filename[0] == '\\':
                        filename = filename[1:]
                    filename = Path(filename)

                    relative_file_offset, file_size, unk = reader.read_fmt('3I')
                    file_offset = relative_file_offset + chunk_size

                    os.makedirs((archive_dump_dir / filename).parent, exist_ok=True)

                    if (archive_dump_dir / filename).exists():
                        f_size = (archive_dump_dir / filename).stat().st_size
                        if f_size < file_size:
                            print(f'Found larger version of {filename}')
                            with (archive_dump_dir / filename).open('wb') as f:
                                f.write(reader.read(file_size))
                    else:
                        with (archive_dump_dir / filename).open('wb') as f:
                            f.write(reader.read(file_size))

            elif chunk_name == 'ASTS':
                file_count = reader.read_uint32()
                if chunk_version >= 2:
                    unk2 = reader.read_uint8()
                for _ in range(file_count):
                    filename = reader.read_ascii_padded()
                    print(f'Found streamed file: {filename} ')
                    unk = reader.read_uint8()
                    size = reader.read_uint32()
                    offset = reader.read_uint32()
                    with reader.save_current_pos():
                        reader.seek(offset)

                        os.makedirs((archive_dump_dir / filename).parent, exist_ok=True)
                        if (archive_dump_dir / filename).exists():
                            f_size = (archive_dump_dir / filename).stat().st_size
                            if f_size < size:
                                print(f'Found larger version of {filename}')
                                with (archive_dump_dir / filename).open('wb') as f:
                                    f.write(reader.read(size))
                        else:
                            with (archive_dump_dir / filename).open('wb') as f:
                                f.write(reader.read(size))

            elif chunk_name == 'TTXT':
                card_count = reader.read_uint32()
                target_filename = reader.read_ascii_string()
                reader.skip(get_pad(target_filename))

            elif chunk_name == 'HSKN':
                unk, bone_count = reader.read_fmt('2I')
                name = reader.read_ascii_string()
                reader.skip(get_pad(name))
                with (archive_dump_dir / f'{name.lower()}.skeleton').open('wb') as cf:
                    reader.seek(chunk_start)
                    cf.write(reader.read(chunk_size))


            elif dump_chunks:
                os.makedirs(archive_dump_dir / 'chunks' / archive.stem / chunk_name, exist_ok=True)
                with (archive_dump_dir / 'chunks' / archive.stem / chunk_name / f'{chunk_start:08x}.chunk').open(
                        'wb') as cf:
                    reader.seek(chunk_start)
                    cf.write(reader.read(chunk_size))
            reader.seek(chunk_start + chunk_size)

    if archive_path.suffix == '.decompressed':
        os.remove(archive_path)
    print(chunk_types)
