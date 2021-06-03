from pathlib import Path
from typing import Union

from ZombieArmy4Loader.archive.compressed_reader import ZlibByteIO
from ZombieArmy4Loader.byte_io_ac import ByteIO
from ZombieArmy4Loader.chunks.asts import ASTS
from ZombieArmy4Loader.chunks.header import ChunkHeader
from ZombieArmy4Loader.chunks.hskn import HSKN
from ZombieArmy4Loader.chunks.rscf import RSCF
from ZombieArmy4Loader.chunks.rsfl import RSFL


class Archive:
    def __init__(self, filepath: Union[Path, str]):
        self.filepath = Path(filepath)
        self.reader = ByteIO(filepath)
        magic = self.reader.read_ascii_string(8)
        if magic == 'AsuraCmp':
            # offset = 8
            # _zipped = True
            raise NotImplementedError(f'{magic} is not supported')
        elif magic == 'AsuraZlb':
            self.reader = ZlibByteIO(self.reader, 0x14, False)
            self.reader.skip(8)
        elif magic == 'AsuraZbb':
            self.reader = ZlibByteIO(self.reader, 0, True)
            self.reader.skip(8)

    def get_used_chunk_types(self):
        reader = self.reader
        used_types = set()
        with reader.save_current_pos():
            while reader:
                chunk_start = reader.tell()
                if chunk_start + 4 >= reader.size():
                    break
                header = ChunkHeader(reader)
                reader.skip(header.size - 16)
                used_types.add(header.name)
        return used_types

    def extract_files(self, output_directory: Path, dump_unknown_chunks=False):
        reader = self.reader
        with reader.save_current_pos():
            while reader:
                chunk_start = reader.tell()
                if chunk_start + 4 >= reader.size():
                    break
                with reader.save_current_pos():
                    header = ChunkHeader(reader)
                print(f'Processing {header.name} chunk at {reader.tell()}')
                handler = getattr(self, f'handle_{header.name}',
                                  self.dummy_handler if dump_unknown_chunks else self.skip_handler)
                handler(reader, header, output_directory)
                reader.seek(chunk_start + header.size)

    def skip_handler(self, reader: ByteIO, header: ChunkHeader, output_directory: Path):
        reader.skip(header.size - 16)

    def dummy_handler(self, reader: ByteIO, header: ChunkHeader, output_directory: Path):
        chunk_start = reader.tell()
        data = reader.read(header.size)
        tmp_path = output_directory / 'chunks' / self.filepath.stem / header.name
        tmp_path.mkdir(parents=True, exist_ok=True)
        output_file = tmp_path / f'{chunk_start:08x}.chunk'
        if not output_file.exists() or (output_file.exists() and output_file.stat().st_size < header.size):
            with output_file.open('wb') as f:
                f.write(data)

    def handle_RSCF(self, reader: ByteIO, header: ChunkHeader, output_directory: Path):
        resource = RSCF(reader)
        output_file = output_directory / resource.filename
        output_file.parent.mkdir(parents=True, exist_ok=True)
        print(f'Dumping "{resource.filename}"')
        if not output_file.exists() or (output_file.exists() and output_file.stat().st_size < resource.size):
            print(f'Writing file {output_file}')
            with output_file.open('wb') as f:
                f.write(resource.data)

    def handle_HSKN(self, reader: ByteIO, header: ChunkHeader, output_directory: Path):
        with reader.save_current_pos():
            resource = HSKN(reader)
        output_file = output_directory / (resource.name + '.skeleton')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if not output_file.exists() or (output_file.exists() and output_file.stat().st_size < header.size):
            print(f'Writing file {output_file}')
            with output_file.open('wb') as f:
                f.write(reader.read(header.size))

    def handle_RSFL(self, reader: ByteIO, header: ChunkHeader, output_directory: Path):
        start = reader.tell()
        resource = RSFL(reader)
        total = len(list(resource.file_ids))
        for file_id in resource.file_ids:
            file_size, filename = resource.file_info(file_id)
            print(f'Dumping {file_id + 1}/{total} "{filename}"')
            output_file = output_directory / filename
            output_file.parent.mkdir(parents=True, exist_ok=True)
            if not output_file.exists() or (output_file.exists() and output_file.stat().st_size < file_size):
                print(f'Writing file {output_file}')
                file_data = resource.file_data(file_id)
                with output_file.open('wb') as f:
                    f.write(file_data)
        reader.seek(start + header.size)

    def handle_ASTS(self, reader: ByteIO, header: ChunkHeader, output_directory: Path):
        start = reader.tell()
        resource = ASTS(reader)
        total = len(list(resource.file_ids))
        for file_id in resource.file_ids:
            print(f'Dumping {file_id + 1}/{total}')
            file_size, filename = resource.file_info(file_id)
            output_file = output_directory / filename
            output_file.parent.mkdir(parents=True, exist_ok=True)
            if not output_file.exists() or (output_file.exists() and output_file.stat().st_size < file_size):
                print(f'Writing file {output_file}')
                file_data = resource.file_data(file_id)
                with output_file.open('wb') as f:
                    f.write(file_data)
        reader.seek(start + header.size)
