# Starfield `.cdb` — Compiled Material Database Binary Format

`materialsbeta.cdb` (inside `Data\Starfield - Materials.ba2`) is the compiled form of *every*
vanilla material. It's what the game reads at load time to resolve a material by path. This page
documents its on-disk binary layout — enough to write a reader that extracts a material as a loose
`.mat` (the JSON described on the [materials page](starfield-materials.md)). For how the `.mat`
graph is structured once decoded, see the [worked example](starfield-material-worked-example.md).

The format is a **self-describing reflection database** (`BSComponentDB2`): it carries its own class
schemas, so a single generic reader can decode any component without hardcoding ~100 struct layouts.
There is no writer anywhere (see the [tools page](starfield-tools.md)); the database is read-only, and
authoring is done with loose `.mat` files.

> **Version note.** The shipped database is **version 4** (game build ≥ 1.16.244). v4 changed a
> record size (see [ObjectInfo](#the-file-index-dbfileindex)); readers written for the older layout
> misalign on the first object, read a garbage count, and allocate unbounded — the "cdb reader
> OOM/crash" people hit. All offsets below are v4.

All integers are little-endian. Strings are `uint16` length-prefixed **including** the trailing NUL:
read the length `n`, then `n` bytes, and the string is the first `n-1` of them.

## Top-level layout

```
[Header]              BETH magic, version, chunk count
[String table]        one blob of NUL-terminated strings, referenced by byte offset
[Class registry]      the reflection schema: every class and its fields
[CompiledDB]          resource-id → db-id hash map (+ build version, collisions)
[DBFileIndex]         component-type table, Objects, Components, Edges
[Component data]      one "diff" blob per component, in Components order
```

Data is **chunked**: a chunk is `uint32 sig` + `uint32 size`, where `sig` is four ASCII bytes read
little-endian. The signatures:

| Sig | Bytes | Use |
|---|---|---|
| `BETH` | file magic | header |
| `STRT` | — | string table |
| `LIST` | — | a serialized vector/list |
| `MAPC` | — | a serialized map |
| `OBJT` | — | a full object (component read in full) |
| `DIFF` / `USRD` | — | a diff object (only changed fields) |
| `USER` / `USRD` | — | a user-cast value |

A **serialized vector** is `Chunk{LIST,size}` + `List{uint32 elementType, uint32 count}` + `count`
elements. (Same 16-byte header for the object/component/edge arrays below.)

## Header

```
uint32  magic            = 'BETH'
uint32  headerSize       = 8
uint32  version          = 4
uint32  chunkCount
Chunk   strtChunk        (STRT); read strtChunk.size bytes → the string table
Chunk   typeChunk;  uint32 typeCount
  ×typeCount:
    Chunk
    uint32  nameRef      (offset into string table = the class name; also its TypeRef)
    uint32  typeId
    uint16  flags        (bit2 = User, bit3 = Struct)
    uint16  fieldCount
    ×fieldCount: { uint32 nameRef, uint32 typeRef, uint16 offset, uint16 size }
```

The **class registry** is the reflection schema. A field's `typeRef` is either a *builtin* (high
three bytes `0xFFFFFF`, low byte the type code) or a *class* (the value equals that class's
`nameRef`). Builtin codes:

| Code | Type | | Code | Type |
|---|---|---|---|---|
| `01` | null | | `0D` | uint32 |
| `02` | string | | `0E` | int64 |
| `03` | list | | `0F` | uint64 |
| `04` | map | | `10` | bool |
| `05` | ref (pointer) | | `11` | float |
| `08…0C` | int8…int32 | | `12` | double |

## Resource IDs and path hashing

Materials (and their textures/layers/etc.) are keyed by a **`BSResource::ID`** = three `uint32`s:
`{ dir, file, ext }`. In the stream they are written **`file, ext, dir`**; the conventional display
form is `res:DIR:FILE:EXT`.

For a material path `Materials\...\Foo.mat`:

- `dir`  = CRC-32 of the directory part (everything before the last slash)
- `file` = CRC-32 of the file name **without** extension
- `ext`  = the extension characters packed little-endian, up to 4 (`"mat"` → `0x0074616D`)

The CRC is a **standard reflected CRC-32** (polynomial `0xEDB88320`) with **initial value 0 and no
final XOR** (i.e. *not* the zlib convention), and every character is transformed first:
lower-cased, and `/` folded to `\`.

```python
def crc32(s):
    r = 0
    for ch in s:
        c = ord(ch); c = c + 0x20 if 0x41 <= c <= 0x5A else (0x5C if ch == '/' else c)
        r = TABLE[(c ^ r) & 0xFF] ^ (r >> 8)   # TABLE = standard 0xEDB88320 CRC table
    return r & 0xFFFFFFFF
```

## The CompiledDB block

Preceded by a `Chunk` + a `TypeRef` naming it (`BSMaterial::Internal::CompiledDB`). Fields:

```
string   BuildVersion          (e.g. "1.16.244.0")
uint32   pad
vector<pair<BSResource::ID, uint64>>  HashMap      ← resource-id → internal id
vector<pair<BSResource::ID, BSResource::ID>>  Collisions
vector<empty>  Circular
```

## The file index (`DBFileIndex`)

Preceded by a `Chunk` + `TypeRef` (`BSComponentDB2::DBFileIndex`).

```
bool     Optimized
uint32   pad
vector<pair<uint16, {uint16 version, bool isEmpty}>>  typeVec
  ×typeVec: { Chunk; User{uint32,uint32}; string className; uint32 pad }   ← component-type table
vector<ObjectInfo>     Objects
vector<ComponentInfo>  Components
vector<EdgeInfo>       Edges
```

**`ObjectInfo` — 33 bytes in v4** (this is the record that broke older readers):

| Field | Size | Notes |
|---|---|---|
| `PersistentID` | 12 | `BSResource::ID` (file, ext, dir) |
| `DBID` | 4 | this object's internal id |
| `ParentDBID` | 4 | parent object's internal id (0 = none) |
| **`ParentPersistentID`** | **12** | **new in v4** — the parent's full resource id |
| `HasData` | 1 | |

The pre-v4 record was 21 bytes (no `ParentPersistentID`). A 21-byte reader misaligns on object 0.

`ComponentInfo` (8 bytes): `{ uint32 objectID, uint16 index, uint16 type }` — attaches a component
of registry-type `type` (index within a set) to an object. `EdgeInfo` (12 bytes):
`{ uint32 source, uint32 target, uint16 index, uint16 type }`.

Build a **resource-id → DBID** map from the Objects whose `PersistentID.ext == 'mat'` — that's the
material lookup table. Group Components by `objectID` to know which components each object carries.

## Component data (the reflection reader)

After the index comes the actual per-component data, **one blob per component in `Components`
order**, with no offset table — so a reader either parses them all, or skip-scans once to record
each blob's start. Each blob is a small chunk sequence read against the class registry:

- The **main chunk** (`OBJT` full / `DIFF` diff) is followed by a `TypeRef`; read that class's value.
- **Primitives** are read as their fixed width and stored as **strings** (`"0.5"`, `"true"`, `"5"`)
  — that's the database convention, and it's why the emitted `.mat` JSON has string-valued numbers.
- A **class value** becomes `{ "Type": <className>, "Data": { field: value, … } }`. In a **full**
  (`OBJT`) read, every field is read in order. In a **diff** (`DIFF`) read, only changed fields are
  present: read `uint16 fieldIndex` repeatedly until `0xFFFF`, reading each named field's value.
- A field whose type is **list/map**, or a **User** class, isn't inline — it's *deferred*: a
  placeholder is queued and filled by a following `LIST`/`MAPC`/`USER` chunk (LIFO). The reader keeps
  consuming chunks until both the list/map queue and the user queue are empty.
- `BSComponentDB2::ID` field: a `uint32` id (full read), or `uint16 pad, uint32 id, uint16 pad`
  (diff) — emitted as the id string, or `""` if 0.

## Reconstructing a material

To turn a material **path** into a loose `.mat` graph:

1. Hash the path → `BSResource::ID` → look up its `DBID` in the material map.
2. **Compose the parent chain.** Walk `ParentDBID` from the object up to its root template, then apply
   each ancestor's components root-first, deep-merging so a descendant overrides its template. This is
   how a concrete material inherits everything it doesn't explicitly set.
3. **Follow references.** Components whose type is `BSMaterial::LayerID` / `MaterialID` /
   `TextureSetID` / `UVStreamID` / `BlenderID` / `LODMaterialID` / `LayeredMaterialID` point (by DBID)
   at another object — resolve each to its resource id, emit it as a separate object in the `.mat`,
   and recurse. This expands the root LayeredMaterial into its layers → materials → texture sets →
   texture files.
4. Set each object's `Parent` to the root template path it derives from (the six
   `Materials\Layered\Root\*.mat` graphs).

The result is exactly the `.mat` JSON of the [worked example](starfield-material-worked-example.md).

## Practical notes

- **No writer exists** — the database is read-only. Author materials as loose `.mat`; the game merges
  a loose `.mat` over the compiled entry with the matching path hash.
- **v4 compatibility.** A reader must handle the 33-byte `ObjectInfo`. Known-working: PyNifly's
  `pyn/sf_cdb.py`. Older readers (fo76utils, Gibbed.Starfield, the `MaxieStarfieldScripts` engine
  behind SFME) predate v4 and misalign/OOM until updated — see the [tools page](starfield-tools.md).
- Reference implementation to compare against: `maximusmaxy/MaxieStarfieldScripts` `include/cdb.h`
  and `src/crc.cpp` (the pre-v4 reader; the byte layout matches except for `ObjectInfo`'s size).

---

_Draft 2026-07-10 — not yet reviewed_
