"""Bounded local OOXML reads and atomic, no-clobber output publication."""

import os
from pathlib import Path, PurePosixPath
import tempfile
from xml.etree import ElementTree as ET
import zipfile


def check_package(zf):
    infos = zf.infolist()
    if len(infos) > 20000 or sum(i.file_size for i in infos) > 512 * 1024 * 1024:
        raise ValueError('Package exceeds inspection limits (20000 entries / 512 MiB expanded)')
    names = [i.filename for i in infos]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate ZIP member names')
    for i in infos:
        p = PurePosixPath(i.filename)
        if p.is_absolute() or '..' in p.parts or '\\' in i.filename:
            raise ValueError('Unsafe ZIP member path')
        if i.flag_bits & 1 or i.file_size > 128 * 1024 * 1024:
            raise ValueError('Encrypted or oversized ZIP member')
        if i.filename.endswith(('.xml', '.rels')) and i.file_size > 16 * 1024 * 1024:
            raise ValueError('XML member exceeds 16 MiB inspection limit')


def xml_root(data):
    # Reject declarations before parsing, including UTF-16/32 encodings.
    probe = data.replace(b'\x00', b'').upper()
    if b'<!DOCTYPE' in probe or b'<!ENTITY' in probe:
        raise ValueError('DTD/entity declarations are unsupported')
    return ET.fromstring(data)


def atomic_publish(output, producer):
    """Create a sibling temp file, then publish only if output is absent."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or output.is_symlink():
        raise ValueError(f'Output already exists; use a new path: {output}')
    fd, temporary = tempfile.mkstemp(prefix='.xiaoyu-', dir=output.parent)
    os.close(fd)
    try:
        producer(Path(temporary))
        # Atomic no-clobber, unlike replace(); source and target share a filesystem.
        os.link(temporary, output)
    finally:
        Path(temporary).unlink(missing_ok=True)
