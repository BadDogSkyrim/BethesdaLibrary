"""Dump Havok packfile (.hkx) structure as human-readable text.

Reflects the actual binary layout: the 80-byte file header, the section
table (with all six fixup offsets per section), the classname lookup
table, and the data-section object layout (enumerated via virtual
fixups). Unlike hkxc/hkxpack XML, this preserves the binary's section
structure and does not lose float precision (it does not parse object
contents at all -- it just shows the structural skeleton).

Usage:
    python dump_hkx.py path/to/file.hkx
    python dump_hkx.py path/to/file.hkx -o dump.txt

Tested against hk_2010.2.0-r1 packfiles (Skyrim LE/SE skeletons and
animations). Pre-2014 layouts only -- newer Havok versions add fields.
"""

import argparse
import struct
import sys
from pathlib import Path

HK_MAGIC = bytes.fromhex("57E0E057" "10C0C010")
HEADER_SIZE = 0x40
SECTION_ENTRY_SIZE = 0x30


def parse_header(buf: bytes) -> dict:
    if buf[:8] != HK_MAGIC:
        raise ValueError(f"Not an HKX packfile: bad magic {buf[:8].hex()}")
    (
        user_tag,
        file_version,
        ptr_size,
        little_endian,
        reuse_padding,
        empty_base_class_opt,
        num_sections,
        contents_section_index,
        contents_section_offset,
        contents_class_name_section_index,
        contents_class_name_section_offset,
        version_string,
    ) = struct.unpack_from("<IIBBBBIIIII16s", buf, 8)
    flags = struct.unpack_from("<I", buf, 0x38)[0]
    return {
        "user_tag": user_tag,
        "file_version": file_version,
        "pointer_size": ptr_size,
        "little_endian": bool(little_endian),
        "reuse_padding": bool(reuse_padding),
        "empty_base_class_optimization": bool(empty_base_class_opt),
        "num_sections": num_sections,
        "contents_section_index": contents_section_index,
        "contents_section_offset": contents_section_offset,
        "contents_class_name_section_index": contents_class_name_section_index,
        "contents_class_name_section_offset": contents_class_name_section_offset,
        "version_string": version_string.rstrip(b"\x00\xff").decode("ascii", "replace"),
        "flags": flags,
    }


def parse_section_table(buf: bytes, num_sections: int) -> list[dict]:
    sections = []
    for i in range(num_sections):
        off = HEADER_SIZE + i * SECTION_ENTRY_SIZE
        name = buf[off : off + 19].rstrip(b"\x00").decode("ascii", "replace")
        # offsets begin at off+0x14 (after 19-byte name + 1 separator byte)
        offsets = struct.unpack_from("<7I", buf, off + 0x14)
        sections.append(
            {
                "index": i,
                "name": name,
                "absolute_data_start": offsets[0],
                "local_fixups_offset": offsets[1],
                "global_fixups_offset": offsets[2],
                "virtual_fixups_offset": offsets[3],
                "exports_offset": offsets[4],
                "imports_offset": offsets[5],
                "end_offset": offsets[6],
            }
        )
    return sections


def parse_classnames(buf: bytes, section: dict) -> list[dict]:
    """Each entry: u32 signature | u8 0x09 separator | null-terminated name."""
    start = section["absolute_data_start"]
    end = start + section["local_fixups_offset"]
    entries = []
    pos = start
    while pos + 5 < end:
        if buf[pos] == 0xFF:
            pos += 1
            continue
        signature = struct.unpack_from("<I", buf, pos)[0]
        if buf[pos + 4] != 0x09:
            break
        name_start = pos + 5
        name_end = buf.find(b"\x00", name_start, end)
        if name_end == -1:
            break
        entries.append(
            {
                "entry_offset": pos - start,
                "name_offset": name_start - start,
                "signature": signature,
                "name": buf[name_start:name_end].decode("ascii", "replace"),
            }
        )
        pos = name_end + 1
    return entries


def parse_local_fixups(buf: bytes, section: dict) -> list[tuple[int, int]]:
    """Each entry: u32 src_offset | u32 dst_offset (both relative to section data)."""
    start = section["absolute_data_start"]
    fx_start = start + section["local_fixups_offset"]
    fx_end = start + section["global_fixups_offset"]
    out = []
    for off in range(fx_start, fx_end, 8):
        if off + 8 > fx_end:
            break
        src, dst = struct.unpack_from("<II", buf, off)
        if src == 0xFFFFFFFF:
            continue  # terminator
        out.append((src, dst))
    return out


def parse_global_fixups(buf: bytes, section: dict) -> list[tuple[int, int, int]]:
    """Each entry: u32 src_offset | u32 dst_section_index | u32 dst_offset."""
    start = section["absolute_data_start"]
    fx_start = start + section["global_fixups_offset"]
    fx_end = start + section["virtual_fixups_offset"]
    out = []
    for off in range(fx_start, fx_end, 12):
        if off + 12 > fx_end:
            break
        src, target_sec, target_off = struct.unpack_from("<III", buf, off)
        if src == 0xFFFFFFFF:
            continue
        out.append((src, target_sec, target_off))
    return out


def parse_virtual_fixups(buf: bytes, section: dict) -> list[tuple[int, int, int]]:
    """Each entry: u32 src_offset | u32 classname_section_index | u32 classname_offset.

    Each entry marks the start of a top-level object in the section's data,
    tagged by class name. classname_offset points at the *name string* (i.e.
    past the signature + 0x09 separator), so it can be matched directly
    against parse_classnames()' name_offset field.
    """
    start = section["absolute_data_start"]
    fx_start = start + section["virtual_fixups_offset"]
    fx_end = start + section["exports_offset"]
    out = []
    for off in range(fx_start, fx_end, 12):
        if off + 12 > fx_end:
            break
        src, classnames_sec, classname_off = struct.unpack_from("<III", buf, off)
        if src == 0xFFFFFFFF:
            continue
        out.append((src, classnames_sec, classname_off))
    return out


# Class layouts for hk_2010.2.0-r1, 64-bit pointers.
#
# Each class entry lists its serialized fields with their byte offset within
# the object. We label fixups by matching the fixup's src-offset against a
# field's offset.
#
# Field tuple: (offset, name, kind[, details])
#   kind = "string"    -> char*, single pointer at this offset (8 bytes)
#   kind = "pointer"   -> single pointer at this offset (8 bytes)
#   kind = "array"     -> hkArray<T> struct (16 bytes: data ptr + size + cap)
#                         details["element_size"]   bytes per element
#                         details["element_fields"] (optional) sub-fields per
#                                                   element, same tuple format
# An array's data ptr lives at offset+0; size at offset+8; cap_and_flags at
# offset+12. The inline array data lives at whatever offset the local fixup
# points to (we read that at label time).
CLASS_LAYOUTS: dict = {
    "hkRootLevelContainer": {
        "fields": [
            (0x00, "namedVariants", "array", {
                "element_size": 24,
                "element_fields": [
                    (0x00, "name", "string"),
                    (0x08, "className", "string"),
                    (0x10, "variant", "pointer"),
                ],
            }),
        ],
    },
    "hkaAnimationContainer": {
        "fields": [
            (0x10, "skeletons",   "array", {"element_size": 8}),
            (0x20, "animations",  "array", {"element_size": 8}),
            (0x30, "bindings",    "array", {"element_size": 8}),
            (0x40, "attachments", "array", {"element_size": 8}),
            (0x50, "skins",       "array", {"element_size": 8}),
        ],
    },
    "hkaSkeleton": {
        "fields": [
            (0x10, "name",            "string"),
            (0x18, "parentIndices",   "array", {"element_size": 2}),
            (0x28, "bones",           "array", {
                "element_size": 16,
                "element_fields": [
                    (0x00, "name", "string"),
                    # 0x08 = bool lockTranslation (no fixup)
                ],
            }),
            (0x38, "referencePose",   "array", {"element_size": 48}),
            (0x48, "referenceFloats", "array", {"element_size": 4}),
            (0x58, "floatSlots",      "array", {
                "element_size": 8,
                "element_fields": [(0x00, "", "string")],
            }),
            (0x68, "localFrames",     "array", {"element_size": 16}),
        ],
    },
    "hkaRagdollInstance": {
        "fields": [
            (0x10, "rigidBodies",        "array", {"element_size": 8}),
            (0x20, "constraints",        "array", {"element_size": 8}),
            (0x30, "boneToRigidBodyMap", "array", {"element_size": 4}),
            (0x40, "skeleton",           "pointer"),
        ],
    },
    "hkpPhysicsData": {
        "fields": [
            (0x10, "worldCinfo", "pointer"),
            (0x18, "systems",    "array", {"element_size": 8}),
        ],
    },
    "hkpPhysicsSystem": {
        "fields": [
            (0x10, "rigidBodies", "array", {"element_size": 8}),
            (0x20, "constraints", "array", {"element_size": 8}),
            (0x30, "actions",     "array", {"element_size": 8}),
            (0x40, "phantoms",    "array", {"element_size": 8}),
            (0x50, "name",        "string"),
            # 0x58 int userData; 0x60 bool active
        ],
    },
    "hkMemoryResourceContainer": {
        "fields": [
            (0x10, "name",            "string"),
            (0x18, "parent",          "pointer"),
            (0x20, "resourceHandles", "array", {"element_size": 8}),
            (0x30, "children",        "array", {"element_size": 8}),
        ],
    },
}


def build_object_labels(
    class_name: str,
    obj_offset: int,
    obj_size: int,
    locals_in_obj: list[tuple[int, int]],
    globals_in_obj: list[tuple[int, int, int]],
) -> dict[int, str]:
    """Build {fixup_src_offset_within_object: label} for an object whose class
    we have a layout for. Labels top-level fields and (where the layout
    provides element_fields) array-element sub-fields."""
    layout = CLASS_LAYOUTS.get(class_name)
    if not layout:
        return {}

    labels: dict[int, str] = {}
    for field in layout["fields"]:
        f_off, f_name, f_kind = field[0], field[1], field[2]
        details = field[3] if len(field) > 3 else {}

        if f_kind in ("string", "pointer"):
            labels[f_off] = f_name
            continue

        if f_kind != "array":
            continue

        labels[f_off] = f"{f_name}.data"
        # Find the inline array start (the local fixup whose src is at f_off
        # patches the array's data pointer).
        inline_start = None
        for src, dst in locals_in_obj:
            if src - obj_offset == f_off:
                inline_start = dst - obj_offset
                break
        if inline_start is None:
            continue

        element_size = details.get("element_size")
        element_fields = details.get("element_fields") or []
        if not element_size:
            continue

        # Label any fixup that lands within the array.
        all_fx_offsets = [s - obj_offset for s, _ in locals_in_obj]
        all_fx_offsets += [s - obj_offset for s, _, _ in globals_in_obj]
        for fx_off in all_fx_offsets:
            if fx_off < inline_start or fx_off >= obj_size:
                continue
            rel = fx_off - inline_start
            idx = rel // element_size
            sub_off = rel % element_size
            if element_fields:
                for esp_off, esp_name, _esp_kind in element_fields:
                    if esp_off == sub_off:
                        if esp_name:
                            labels[fx_off] = f"{f_name}[{idx}].{esp_name}"
                        else:
                            labels[fx_off] = f"{f_name}[{idx}]"
                        break
            else:
                # No element field info; if it lands at element start, label
                # as the array slot. Otherwise leave unlabelled.
                if sub_off == 0:
                    labels[fx_off] = f"{f_name}[{idx}]"

    return labels


def hex32(n: int) -> str:
    return f"0x{n:08X}"


def peek_string(buf: bytes, abs_offset: int, max_len: int = 80) -> str | None:
    """If a null-terminated printable-ASCII string starts at abs_offset, return
    it (without trailing null). Used to surface embedded labels (named-variant
    titles, bone names) that local fixups point at, so the dump shows them
    inline instead of just an offset.
    """
    if abs_offset < 0 or abs_offset >= len(buf):
        return None
    end = min(abs_offset + max_len, len(buf))
    nul = buf.find(b"\x00", abs_offset, end)
    if nul == -1 or nul == abs_offset:
        return None
    s = buf[abs_offset:nul]
    if not all(0x20 <= b < 0x7F for b in s):
        return None
    return s.decode("ascii")


def dump(path: str, out) -> None:
    buf = Path(path).read_bytes()
    header = parse_header(buf)
    sections = parse_section_table(buf, header["num_sections"])

    print(f"=== HKX packfile: {path} ===", file=out)
    print(f"File size: {len(buf)} bytes ({hex32(len(buf))})\n", file=out)

    print("--- Header (offsets 0x00..0x3F) ---", file=out)
    print(f"  magic                              57 E0 E0 57 10 C0 C0 10", file=out)
    print(f"  user_tag                           {header['user_tag']}", file=out)
    print(f"  file_version (classversion)        {header['file_version']}", file=out)
    print(
        f"  pointer_size                       {header['pointer_size']} bytes "
        f"({header['pointer_size'] * 8}-bit)",
        file=out,
    )
    print(f"  little_endian                      {header['little_endian']}", file=out)
    print(f"  reuse_padding                      {header['reuse_padding']}", file=out)
    print(
        f"  empty_base_class_optimization      {header['empty_base_class_optimization']}",
        file=out,
    )
    print(f"  num_sections                       {header['num_sections']}", file=out)
    print(
        f"  contents_section_index             {header['contents_section_index']}",
        file=out,
    )
    print(
        f"  contents_section_offset            {hex32(header['contents_section_offset'])}",
        file=out,
    )
    print(
        f"  contents_class_name_section_index  {header['contents_class_name_section_index']}",
        file=out,
    )
    print(
        f"  contents_class_name_section_offset {hex32(header['contents_class_name_section_offset'])}",
        file=out,
    )
    print(f"  version_string                     '{header['version_string']}'", file=out)
    print(f"  flags                              {hex32(header['flags'])}", file=out)
    print("", file=out)

    print(
        f"--- Section table ({header['num_sections']} entries × 48 bytes, starts at 0x40) ---",
        file=out,
    )
    for s in sections:
        ds = s["absolute_data_start"]
        print(f"  [{s['index']}] '{s['name']}'", file=out)
        print(
            f"      absolute_data_start    {hex32(ds)}",
            file=out,
        )
        print(
            f"      local_fixups_offset    {hex32(s['local_fixups_offset'])}  "
            f"(abs: {hex32(ds + s['local_fixups_offset'])})",
            file=out,
        )
        print(
            f"      global_fixups_offset   {hex32(s['global_fixups_offset'])}  "
            f"(abs: {hex32(ds + s['global_fixups_offset'])})",
            file=out,
        )
        print(
            f"      virtual_fixups_offset  {hex32(s['virtual_fixups_offset'])}  "
            f"(abs: {hex32(ds + s['virtual_fixups_offset'])})",
            file=out,
        )
        print(f"      exports_offset         {hex32(s['exports_offset'])}", file=out)
        print(f"      imports_offset         {hex32(s['imports_offset'])}", file=out)
        print(
            f"      end_offset             {hex32(s['end_offset'])}  "
            f"(section size: {s['end_offset']} bytes)",
            file=out,
        )
        print("", file=out)

    classnames_section = next((s for s in sections if s["name"] == "__classnames__"), None)
    classname_lookup: dict[int, str] = {}
    if classnames_section:
        entries = parse_classnames(buf, classnames_section)
        print(f"--- __classnames__ contents ({len(entries)} entries) ---", file=out)
        print(f"  {'sec_off':>8s}  {'name_off':>8s}  {'signature':>10s}  name", file=out)
        for e in entries:
            classname_lookup[e["name_offset"]] = e["name"]
            print(
                f"  {hex32(e['entry_offset']):>8s}  "
                f"{hex32(e['name_offset']):>8s}  "
                f"{hex32(e['signature']):>10s}  {e['name']}",
                file=out,
            )
        print("", file=out)

    types_section = next((s for s in sections if s["name"] == "__types__"), None)
    if types_section:
        size = types_section["end_offset"]
        print(f"--- __types__ contents ---", file=out)
        if size == 0:
            print("  (empty -- type info not embedded; reader uses class name + signature)", file=out)
        else:
            print(f"  ({size} bytes; not parsed)", file=out)
        print("", file=out)

    data_section = next((s for s in sections if s["name"] == "__data__"), None)
    if data_section:
        local_fx = parse_local_fixups(buf, data_section)
        global_fx = parse_global_fixups(buf, data_section)
        virtual_fx = parse_virtual_fixups(buf, data_section)

        print("--- __data__ section structure ---", file=out)
        ds = data_section["absolute_data_start"]
        print(
            f"  payload          {hex32(ds)}..{hex32(ds + data_section['local_fixups_offset'])}  "
            f"({data_section['local_fixups_offset']} bytes)",
            file=out,
        )
        print(f"  local fixups     {len(local_fx):4d} entries (8 bytes each)", file=out)
        print(f"  global fixups    {len(global_fx):4d} entries (12 bytes each)", file=out)
        print(f"  virtual fixups   {len(virtual_fx):4d} entries (12 bytes each)", file=out)
        print("", file=out)

        # Each virtual fixup marks an object. Sort by offset and compute size from gaps.
        objs = sorted(virtual_fx, key=lambda f: f[0])
        boundary = data_section["local_fixups_offset"]
        # Build offset -> class lookup for fast target resolution.
        obj_class_at: dict[int, str] = {
            src: classname_lookup.get(cname_off, "<unknown>")
            for src, _, cname_off in objs
        }
        # Pre-bucket fixups by object for O(n) attribution. Both fixup
        # types are sorted by src in file order already, so a sweep works.
        local_fx_sorted = sorted(local_fx, key=lambda f: f[0])
        global_fx_sorted = sorted(global_fx, key=lambda f: f[0])
        local_by_obj: dict[int, list] = {src: [] for src, _, _ in objs}
        global_by_obj: dict[int, list] = {src: [] for src, _, _ in objs}
        # Build [start, end) ranges aligned with objs order.
        obj_ranges = [
            (objs[i][0], (objs[i + 1][0] if i + 1 < len(objs) else boundary))
            for i in range(len(objs))
        ]
        idx = 0
        for src, dst in local_fx_sorted:
            while idx < len(obj_ranges) and src >= obj_ranges[idx][1]:
                idx += 1
            if idx >= len(obj_ranges):
                break
            local_by_obj[obj_ranges[idx][0]].append((src, dst))
        idx = 0
        for src, target_sec, target_off in global_fx_sorted:
            while idx < len(obj_ranges) and src >= obj_ranges[idx][1]:
                idx += 1
            if idx >= len(obj_ranges):
                break
            global_by_obj[obj_ranges[idx][0]].append((src, target_sec, target_off))

        data_section_index = data_section["index"]
        classnames_section_index = (
            classnames_section["index"] if classnames_section else -1
        )

        print(
            f"--- __data__ object layout ({len(objs)} top-level objects) ---",
            file=out,
        )
        print(
            "  Each object: byte range, class, and outgoing references derived from",
            file=out,
        )
        print(
            "  the local + global fixup tables. Local fixups are intra-section pointers",
            file=out,
        )
        print(
            "  (e.g. an object pointing at its own embedded array). Global fixups are",
            file=out,
        )
        print(
            "  cross-section pointers (typically into __data__ to reference another",
            file=out,
        )
        print(
            "  object, or into __classnames__ for a class-name string).",
            file=out,
        )
        print("", file=out)
        for i, (src, _csec, cname_off) in enumerate(objs):
            next_off = obj_ranges[i][1]
            size = next_off - src
            cname = classname_lookup.get(cname_off, f"<unknown @{hex32(cname_off)}>")
            print(f"  {hex32(src):>8s}  size={size:<5d}  {cname}", file=out)
            field_labels = build_object_labels(
                cname, src, size, local_by_obj[src], global_by_obj[src]
            )
            # Merge local + global fixups in one timeline so the per-object
            # detail reads in offset order. Global entries get a 3-tuple, local
            # entries a 2-tuple; we tag with the kind.
            timeline: list = []
            for gsrc, gsec, gdst in global_by_obj[src]:
                timeline.append((gsrc, "global", (gsec, gdst)))
            for lsrc, ldst in local_by_obj[src]:
                timeline.append((lsrc, "local", ldst))
            timeline.sort(key=lambda t: t[0])

            for fx_src, kind, payload in timeline:
                rel = fx_src - src
                label = field_labels.get(rel)
                tag = f" [{label}]" if label else ""
                if kind == "global":
                    gsec, gdst = payload
                    if gsec == data_section_index:
                        target = obj_class_at.get(gdst, "?")
                        print(
                            f"      global  @+{hex32(rel)} -> data {hex32(gdst)}  ({target}){tag}",
                            file=out,
                        )
                    elif gsec == classnames_section_index:
                        target_name = classname_lookup.get(gdst, f"@{hex32(gdst)}")
                        print(
                            f"      global  @+{hex32(rel)} -> classnames '{target_name}'{tag}",
                            file=out,
                        )
                    else:
                        print(
                            f"      global  @+{hex32(rel)} -> [section {gsec}] +{hex32(gdst)}{tag}",
                            file=out,
                        )
                else:  # local
                    ldst = payload
                    s = peek_string(buf, ds + ldst)
                    str_part = f"  '{s}'" if s else ""
                    print(
                        f"      local   @+{hex32(rel)} -> @+{hex32(ldst - src)}{str_part}{tag}",
                        file=out,
                    )
        print("", file=out)

        # Class breakdown (counts)
        from collections import Counter
        class_counts = Counter(
            classname_lookup.get(cname_off, "<unknown>") for _, _, cname_off in virtual_fx
        )
        print("--- Class counts ---", file=out)
        for cname, count in sorted(class_counts.items(), key=lambda kv: -kv[1]):
            print(f"  {count:4d}  {cname}", file=out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("hkx", help="Input .hkx file")
    p.add_argument("-o", "--output", help="Write to a file instead of stdout")
    args = p.parse_args()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            dump(args.hkx, f)
    else:
        dump(args.hkx, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
