#!/usr/bin/env python3
"""Create a temporary PPTX copy with DrawingML fonts replaced for render-only QA."""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape
from xml.etree import ElementTree as ET
from package_io import check_package, xml_root, atomic_publish


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument('--font', required=True, help='A font verified available in the QA renderer')
    args = parser.parse_args()

    if args.source.resolve() == args.output.resolve():
        parser.error("output must differ from source; this tool never edits the canonical deck")
    if not args.font.strip() or any(ord(c) < 32 for c in args.font):
        parser.error('font must be nonempty and contain no control characters')

    font = escape(args.font, {'"': '&quot;', "'": '&apos;'})
    def produce(path):
        with zipfile.ZipFile(args.source) as source, zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as output:
            check_package(source)
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename.endswith('.xml') and item.filename.startswith(('ppt/slides/', 'ppt/slideMasters/', 'ppt/slideLayouts/', 'ppt/theme/')):
                    xml_root(data)
                    # UTF-8 XML only; other encodings fail before publication.
                    text = data.decode('utf-8')
                    text = re.sub(r'''typeface\s*=\s*(?:"[^"]*"|'[^']*')''', lambda _: 'typeface="' + font + '"', text)
                    data = text.encode('utf-8')
                    xml_root(data)
                output.writestr(item, data)
    atomic_publish(args.output, produce)
    print(args.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, zipfile.BadZipFile, ET.ParseError) as error:
        raise SystemExit(f'Render-copy failed: {error}')
