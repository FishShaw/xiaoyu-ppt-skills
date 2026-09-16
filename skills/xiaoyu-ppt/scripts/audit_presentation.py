#!/usr/bin/env python3
"""Audit slide geometry, required text, and canonical-slide preservation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import zipfile
import posixpath
from pathlib import Path
from xml.etree import ElementTree as ET
from package_io import check_package, xml_root, atomic_publish

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
EMU = 914400


def to_inches(value: str | None) -> float:
    return int(value or 0) / EMU


def slide_parts(zf: zipfile.ZipFile) -> list[str]:
    root = xml_root(zf.read('ppt/presentation.xml'))
    rels = xml_root(zf.read('ppt/_rels/presentation.xml.rels'))
    targets = {r.get('Id'): r for r in rels}
    members = set(zf.namelist())
    parts = []
    for item in root.findall('p:sldIdLst/p:sldId', NS):
        rid = item.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        rel = targets.get(rid)
        if rel is None or rel.get('TargetMode') == 'External':
            raise ValueError('Missing or external slide relationship')
        target = rel.get('Target', '')
        part = posixpath.normpath(target.lstrip('/') if target.startswith('/') else 'ppt/' + target)
        if not part.startswith('ppt/slides/') or part not in members or part in parts:
            raise ValueError('Invalid or repeated slide target')
        parts.append(part)
    if not parts:
        raise ValueError('Presentation contains no ordered slides')
    return parts


def element_text(element: ET.Element) -> str:
    return "".join(node.text or "" for node in element.findall(".//a:t", NS)).strip()


def geometry(shape: ET.Element) -> dict[str, object] | None:
    xfrm = shape.find(".//p:spPr/a:xfrm", NS)
    if xfrm is None:
        return None
    off, ext = xfrm.find("a:off", NS), xfrm.find("a:ext", NS)
    if off is None or ext is None:
        return None
    x, y = to_inches(off.get("x")), to_inches(off.get("y"))
    w, h = to_inches(ext.get("cx")), to_inches(ext.get("cy"))
    return {
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "cx": x + w / 2,
        "cy": y + h / 2,
        "flip_h": xfrm.get("flipH") in {"1", "true"},
        "flip_v": xfrm.get("flipV") in {"1", "true"},
        "rotation": int(xfrm.get('rot', '0')),
    }


def parse_slide(data: bytes) -> dict[str, object]:
    root = xml_root(data)
    nodes, lines = [], []
    unsupported = []
    grouped = {id(s) for g in root.findall('.//p:grpSp', NS) for s in g.iter()}
    shapes = root.findall(".//p:sp", NS) + root.findall(".//p:cxnSp", NS)
    for shape in shapes:
        item = geometry(shape)
        if item is None:
            unsupported.append('Object without explicit local geometry')
            continue
        if id(shape) in grouped or item['rotation']:
            unsupported.append('Grouped or rotated object requires transform-aware inspection')
            continue
        item["text"] = element_text(shape)
        identity = shape.find('.//p:cNvPr', NS)
        item['id'] = identity.get('id') if identity is not None else None
        preset = shape.find(".//p:spPr/a:prstGeom", NS)
        is_connector = shape.tag == f"{{{NS['p']}}}cxnSp"
        if not is_connector and (preset is None or preset.get("prst") != "line"):
            nodes.append(item)
            continue
        if preset is None or preset.get('prst') not in {'line', 'straightConnector1'}:
            unsupported.append('Bent, curved, or custom connector requires path-aware inspection')
            continue
        start_x = float(item["x"]) + (float(item["w"]) if item["flip_h"] else 0)
        end_x = float(item["x"]) + (0 if item["flip_h"] else float(item["w"]))
        start_y = float(item["y"]) + (float(item["h"]) if item["flip_v"] else 0)
        end_y = float(item["y"]) + (0 if item["flip_v"] else float(item["h"]))
        head = shape.find(".//p:spPr/a:ln/a:headEnd", NS)
        tail = shape.find(".//p:spPr/a:ln/a:tailEnd", NS)
        item.update(
            {
                "start": (start_x, start_y),
                "end": (end_x, end_y),
                "head_arrow": head is not None and head.get("type", "none") != "none",
                "tail_arrow": tail is not None and tail.get("type", "none") != "none",
            }
        )
        lines.append(item)
    return {"nodes": nodes, "lines": lines, "text": element_text(root), 'unsupported': unsupported}


def smallest_text_node(slide: dict[str, object], label: str) -> dict[str, object] | None:
    matches = [node for node in slide['nodes'] if
               (node['id'] == label[3:] if label.startswith('id:') else node['text'] == label)]
    return matches[0] if len(matches) == 1 else None


def point_distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def audit_chain(
    slides: list[dict[str, object]],
    labels: list[str],
    tolerance: float,
    orientation: str,
    slide_number: int | None = None,
) -> dict[str, object]:
    candidates = []
    for number, slide in enumerate(slides, start=1):
        if slide_number is not None and number != slide_number:
            continue
        nodes = [smallest_text_node(slide, label) for label in labels]
        if all(nodes):
            candidates.append((number, slide, nodes))
    if len(candidates) != 1:
        return {'passed': False, 'reason': 'Missing or ambiguous exact labels; use --slide and id:<shape-id>', 'labels': labels}

    number, slide, nodes = candidates[0]
    if slide['unsupported']:
        return {'passed': False, 'status': 'unsupported', 'slide': number, 'reason': slide['unsupported']}
    if len({id(n) for n in nodes}) != len(nodes):
        return {'passed': False, 'reason': 'Multiple selectors resolve to the same node'}
    if orientation == "auto":
        x_range = max(float(node["cx"]) for node in nodes) - min(float(node["cx"]) for node in nodes)
        y_range = max(float(node["cy"]) for node in nodes) - min(float(node["cy"]) for node in nodes)
        orientation = "horizontal" if x_range >= y_range else "vertical"

    if orientation == "horizontal":
        ordered = nodes
        cross_axis = [float(node["cy"]) for node in ordered]
        gaps = [float(b["x"]) - float(a["x"]) - float(a["w"]) for a, b in zip(ordered, ordered[1:])]

        def expected_points(left: dict[str, object], right: dict[str, object]) -> tuple[tuple[float, float], tuple[float, float]]:
            return (float(left["x"]) + float(left["w"]), float(left["cy"])), (float(right["x"]), float(right["cy"]))

        def orthogonal(start: tuple[float, float], end: tuple[float, float]) -> bool:
            return abs(start[1] - end[1]) <= tolerance

    else:
        ordered = nodes
        cross_axis = [float(node["cx"]) for node in ordered]
        gaps = [float(b["y"]) - float(a["y"]) - float(a["h"]) for a, b in zip(ordered, ordered[1:])]

        def expected_points(top: dict[str, object], bottom: dict[str, object]) -> tuple[tuple[float, float], tuple[float, float]]:
            return (float(top["cx"]), float(top["y"]) + float(top["h"])), (float(bottom["cx"]), float(bottom["y"]))

        def orthogonal(start: tuple[float, float], end: tuple[float, float]) -> bool:
            return abs(start[0] - end[0]) <= tolerance

    baseline_spread = max(cross_axis) - min(cross_axis)
    gap_spread = max(gaps) - min(gaps) if gaps else 0
    positive_gaps = all(g >= 0 for g in gaps)

    available = list(slide["lines"])
    used: set[int] = set()
    connectors = []
    for left, right in zip(ordered, ordered[1:]):
        expected_start, expected_end = expected_points(left, right)
        ranked = []
        for index, line in enumerate(available):
            if index in used:
                continue
            start, end = tuple(line["start"]), tuple(line["end"])
            forward = point_distance(start, expected_start) + point_distance(end, expected_end)
            reverse = point_distance(end, expected_start) + point_distance(start, expected_end)
            ranked.append((min(forward, reverse), index, line, forward <= reverse))
        if not ranked:
            connectors.append({"passed": False, "reason": "missing connector"})
            continue
        _, index, line, forward = min(ranked, key=lambda item: item[0])
        used.add(index)
        start = tuple(line["start"] if forward else line["end"])
        end = tuple(line["end"] if forward else line["start"])
        arrow = bool(line["tail_arrow"] if forward else line["head_arrow"])
        start_gap, end_gap = point_distance(start, expected_start), point_distance(end, expected_end)
        axis_aligned = orthogonal(start, end)
        obstacles = []
        for node in slide['nodes']:
            if node is left or node is right or not node['text']:
                continue
            x, y, w, h = (float(node[k]) for k in ('x', 'y', 'w', 'h'))
            if orientation == 'horizontal':
                hit = y < start[1] < y+h and max(min(start[0], end[0]), x) < min(max(start[0], end[0]), x+w)
            else:
                hit = x < start[0] < x+w and max(min(start[1], end[1]), y) < min(max(start[1], end[1]), y+h)
            if hit:
                obstacles.append(node['id'])
        connectors.append(
            {
                "passed": arrow and axis_aligned and start_gap <= tolerance and end_gap <= tolerance and not obstacles,
                'text_obstacles': obstacles,
                "arrowhead": arrow,
                "axis_aligned": axis_aligned,
                "start_gap_inches": round(start_gap, 4),
                "end_gap_inches": round(end_gap, 4),
            }
        )

    passed = positive_gaps and baseline_spread <= tolerance and gap_spread <= tolerance and all(item["passed"] for item in connectors)
    return {
        "passed": passed,
        "slide": number,
        "labels": labels,
        "orientation": orientation,
        'ordered_without_overlap': positive_gaps,
        "baseline_spread_inches": round(baseline_spread, 4),
        "gap_spread_inches": round(gap_spread, 4),
        "connectors": connectors,
    }


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", type=Path)
    parser.add_argument("--expected-slides", type=int)
    parser.add_argument("--require-text", action="append", default=[])
    parser.add_argument("--forbid-text", action="append", default=[])
    parser.add_argument('--chain', help='Ordered exact labels or id:<shape-id>, separated by |')
    parser.add_argument('--slide', type=int, help='One-based display position for chain selection')
    parser.add_argument('--aspect', default=None, help='Optional required aspect, e.g. 16:9 or 4:3')
    parser.add_argument(
        "--orientation",
        choices=["auto", "horizontal", "vertical"],
        default="auto",
        help="Chain direction; auto selects the dominant center-axis range",
    )
    parser.add_argument("--tolerance", type=float, default=0.08)
    parser.add_argument("--canonical", type=Path)
    parser.add_argument("--changed-slide", type=int)
    parser.add_argument('--allow-part', action='append', default=[], help='Exact authorized package part, only with --canonical')
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not math.isfinite(args.tolerance) or args.tolerance < 0 or args.tolerance > 0.25:
        parser.error('tolerance must be finite and between 0 and 0.25 inch')
    if args.chain and (len(args.chain.split('|')) < 2 or any(not s.strip() for s in args.chain.split('|')) or len(set(args.chain.split('|'))) != len(args.chain.split('|'))):
        parser.error('chain needs at least two distinct, nonempty selectors')
    if (args.changed_slide is not None or args.allow_part) and args.canonical is None:
        parser.error('change permissions require --canonical')
    if args.output and (args.output.resolve() == args.deck.resolve() or (args.canonical and args.output.resolve() == args.canonical.resolve())):
        parser.error('report output must not be an input deck')
    if args.output and (args.output.exists() or args.output.is_symlink()):
        parser.error('report already exists; use a new output path')
    ratio = None
    if args.aspect:
        try:
            a, b = map(float, args.aspect.split(':'))
            ratio = a / b
            if not math.isfinite(ratio) or a <= 0 or b <= 0:
                raise ValueError()
        except (ValueError, ZeroDivisionError):
            parser.error('aspect must be positive finite width:height')

    report: dict[str, object] = {"deck": str(args.deck), "checks": {}}
    with zipfile.ZipFile(args.deck) as zf:
        check_package(zf)
        parts = slide_parts(zf)
        if any(v is not None and not 1 <= v <= len(parts) for v in (args.slide, args.changed_slide)):
            parser.error('slide number out of range')
        slides = [parse_slide(zf.read(part)) for part in parts]
        all_text = " ".join(str(slide["text"]) for slide in slides)
        presentation = xml_root(zf.read("ppt/presentation.xml"))
        size = presentation.find("p:sldSz", NS)
        width = to_inches(size.get("cx")) if size is not None else 0
        height = to_inches(size.get("cy")) if size is not None else 0

        checks = report["checks"]
        checks["slide_count"] = {"passed": args.expected_slides is None or len(parts) == args.expected_slides, "actual": len(parts)}
        checks['canvas'] = {'passed': width > 0 and height > 0 and (ratio is None or abs(width / height - ratio) <= 0.01), 'expected_aspect': args.aspect, 'width': round(width, 3), 'height': round(height, 3)}
        checks["required_text"] = {text: text in all_text for text in args.require_text}
        checks["forbidden_text_absent"] = {text: text not in all_text for text in args.forbid_text}
        if args.chain:
            checks["geometry_chain"] = audit_chain(slides, args.chain.split("|"), args.tolerance, args.orientation, args.slide)

        report['coverage'] = {'visual_qa': 'not performed by this script', 'text_scope': 'slide DrawingML text only; not OCR, notes, or embedded files', 'geometry': 'selected ungrouped, unrotated straight chain only', 'unsupported_by_slide': {str(i): s['unsupported'] for i, s in enumerate(slides, 1) if s['unsupported']}}

        if args.canonical:
            with zipfile.ZipFile(args.canonical) as source:
                check_package(source)
                source_parts = slide_parts(source)
                before_names, after_names = set(source.namelist()), set(zf.namelist())
                allowed = set(args.allow_part)
                if args.changed_slide is not None:
                    allowed.add(parts[args.changed_slide - 1])
                unknown = allowed - (before_names | after_names)
                if unknown:
                    raise ValueError(f'Unknown authorized parts: {sorted(unknown)}')
                changed = [p for p in sorted(before_names | after_names)
                           if p not in before_names or p not in after_names or sha256(source.read(p)) != sha256(zf.read(p))]
                unexpected = sorted(set(changed) - allowed)
                unchanged = {}
                for number, (before, after) in enumerate(zip(source_parts, parts), start=1):
                    if number != args.changed_slide:
                        unchanged[str(number)] = sha256(source.read(before)) == sha256(zf.read(after))
                checks["canonical_preservation"] = {
                    "passed": source_parts == parts and not unexpected,
                    "unchanged_slide_xml": unchanged,
                    'slide_order_preserved': source_parts == parts,
                    'changed_package_parts': changed,
                    'unexpected_package_parts': unexpected,
                }

    states = []
    for value in report["checks"].values():
        if isinstance(value, dict) and "passed" in value:
            states.append(bool(value["passed"]))
        elif isinstance(value, dict):
            states.extend(bool(item) for item in value.values())
    report["passed"] = all(states)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    print(payload)
    if args.output:
        atomic_publish(args.output, lambda p: p.write_text(payload + '\n', encoding='utf-8'))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, zipfile.BadZipFile, ET.ParseError) as error:
        print(json.dumps({'passed': False, 'status': 'error', 'reason': str(error)}))
        raise SystemExit(2)
