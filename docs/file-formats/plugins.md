# Plugin Files (ESP/ESM/ESL)

Plugin files are the primary way to add or modify game data in Bethesda games. They define everything from items and NPCs to quests and world spaces.

## Overview

**Extensions:**
- `.esp` - Plugin (mod file)
- `.esm` - Master file (dependency, loads first)
- `.esl` - Light plugin (Skyrim SE/FO4, loads early in load order)

**Note:** ESL behavior (plugin limit exemption, FormID range) is determined by a **flag** (`0x00000200`), not the file extension. Plugins with `.esp` extension can be ESL-flagged. The engine orders files by extension family — `.esm` first, then `.esl`, then `.esp` — so giving an ESL-flagged plugin the `.esp` extension is the standard trick to place it later in the load order.

**Format:** Binary record structure  
**Tools:** Creation Kit, xEdit (SSEEdit/FO4Edit), esplib (Python)

## File Structure

```
Plugin File
├── Header (TES4 record)
│   ├── Version
│   ├── Master files (dependencies)
│   └── Description/author
├── Records (game data)
│   ├── Record Header (24 bytes)
│   │   ├── Type (4 bytes, ASCII: ARMO, NPC_, CELL, etc.)
│   │   ├── Data Size (4 bytes, uint32)
│   │   ├── Flags (4 bytes, compressed, persistent, etc.)
│   │   ├── FormID (4 bytes, unique identifier)
│   │   ├── Revision (4 bytes)
│   │   ├── Version (2 bytes)
│   │   └── Unknown (2 bytes)
│   └── Record Data (contains subrecords)
│       └── Subrecords (simpler structure: type + size + data)
│           ├── EDID - Editor ID (string name)
│           ├── FULL - Display name
│           ├── MODL - Model path (NIF)
│           └── (type-specific fields)
└── Groups (organizational containers)
    ├── Top-level groups (by record type)
    ├── World space groups (WRLD → CELL)
    └── Cell children (REFR, ACHR, etc.)
```

**Record header (24 bytes):**
```
[TYPE:4] [SIZE:4] [FLAGS:4] [FORMID:4] [REVISION:4] [VERSION:2] [UNKNOWN:2]
```

**Important:** Records have full headers with flags and FormIDs. Subrecords (within record data) have simpler headers with only type and size.

## Groups (GRUPs)

GRUPs are containers that hold records of the same type, letting parsers skip large blocks of data they don't care about. CELL, WRLD, and DIAL records also use subgroups for structural information — persistent vs. temporary references, world children, dialog topic children, etc.

**GRUP header (24 bytes):**

| Field       | Size | Notes |
|-------------|------|-------|
| `"GRUP"`    | 4    | Magic identifier |
| Group size  | 4    | uint32 — **includes** the 24-byte header (unlike records/fields, whose sizes exclude their headers) |
| Label       | 4    | Format depends on group type (see below) |
| Group type  | 4    | int32 (see below) |
| Timestamp   | 2    | uint16 — bit-packed date, see [Timestamp Encoding](#timestamp-encoding) |
| VC info     | 2    | low byte = last user to check the form out; high byte = user (if any) currently holding it |
| Unknown     | 4    | uint32 — usually 0; `0xCCCCCCCC` and other small values seen in cell/world/topic subgroups |

**CK quirk:** The "ignored" flag in the CK Details view corrupts the label field (e.g. `HAIR` → `HQIR`) but doesn't actually prevent loading. Treat group labels as advisory; trust the group type instead.

### Group types

| Type | Name                       | Label format | Description |
|------|----------------------------|--------------|-------------|
| 0    | Top                        | `char[4]`    | Record type (e.g. `"ARMO"`) |
| 1    | World Children             | formid       | Parent WRLD |
| 2    | Interior Cell Block        | int32        | Block number |
| 3    | Interior Cell Sub-Block    | int32        | Sub-block number |
| 4    | Exterior Cell Block        | int16[2]     | Grid **Y, X** (reversed!) |
| 5    | Exterior Cell Sub-Block    | int16[2]     | Grid **Y, X** (reversed!) |
| 6    | Cell Children              | formid       | Parent CELL |
| 7    | Topic Children             | formid       | Parent DIAL |
| 8    | Cell Persistent Children   | formid       | Parent CELL |
| 9    | Cell Temporary Children    | formid       | Parent CELL |

### Subgroup-only record types

These record types never appear at the top level — they only exist inside subgroups of other records. Useful for parser validation:

`REFR`, `ACHR`, `NAVM`, `PGRE`, `PHZD`, `LAND`, `INFO`

### Top group order (Skyrim.esm)

The canonical order top groups appear in Skyrim.esm. Whether the engine requires this order is unverified, but matching it is the safe default for any tool that emits a plugin from scratch:

```
GMST, KYWD, LCRT, AACT, TXST, GLOB, CLAS, FACT, HDPT, HAIR, EYES, RACE, SOUN,
ASPC, MGEF, SCPT, LTEX, ENCH, SPEL, SCRL, ACTI, TACT, ARMO, BOOK, CONT, DOOR,
INGR, LIGH, MISC, APPA, STAT, SCOL, MSTT, PWAT, GRAS, TREE, CLDC, FLOR, FURN,
WEAP, AMMO, NPC_, LVLN, KEYM, ALCH, IDLM, COBJ, PROJ, HAZD, SLGM, LVLI, WTHR,
CLMT, SPGD, RFCT, REGN, NAVI, CELL, WRLD, DIAL, QUST, IDLE, PACK, CSTY, LSCR,
LVSP, ANIO, WATR, EFSH, EXPL, DEBR, IMGS, IMAD, FLST, PERK, BPTD, ADDN, AVIF,
CAMS, CPTH, VTYP, MATT, IPCT, IPDS, ARMA, ECZN, LCTN, MESG, RGDL, DOBJ, LGTM,
MUSC, FSTP, FSTS, SMBN, SMQN, SMEN, DLBR, MUST, DLVW, WOOP, SHOU, EQUP, RELA,
SCEN, ASTP, OTFT, ARTO, MATO, MOVT, HAZD, SNDR, DUAL, SNCT, SOPM, COLL, CLFM,
REVB
```

Notes:
- 6 record types have a GRUP but no records in Skyrim.esm: `CLDC`, `HAIR`, `RGDL`, `SCPT`, `SCOL`, `PWAT`.
- `HAZD` appears twice; the second occurrence is empty.

### Timestamp encoding

The 2-byte timestamp at offset 16 in both group and record headers encodes the date the form was last modified. The encoding differs between editions:

`[SSE]` Bit-packed `0bYYYYYYY MMMM DDDDD` — 7-bit two-digit year, 4-bit month, 5-bit day. January 25, 2021 = `0b0010101 0001 11001` = `0x2A39`.

`[LE]` Low byte is day-of-month; high byte encodes month and year-last-digit:
```
HB = ((Y - 4) MOD 10 + 1) * 12 + M
```
Range nominally 13–132, covering Jan-20x4 through Dec-20x3. To decode:
```
Y = ((HB - 1) / 12 + 3) MOD 10    (single-digit year)
M = ((HB - 1) MOD 12) + 1
```
Lower values appear in Skyrim.esm, held over from Oblivion-era records where 1–12 represented 2003.

## FormIDs

**FormID:** 32-bit unique identifier for every record.

**Structure:**
```
0xMMXXXXXX
  ││└─────── Local ID (assigned within plugin)
  ││
  └┴──────── Load order index (master index)
```

**Examples:**
- `0x00012E46` - Skyrim.esm record (master index 0x00)
- `0x0100A3F2` - First .esp record (master index 0x01)
- `0xFE000800` - ESL record (ESL flag 0xFE)

**Local IDs** are restricted to the range 0x800-0xFFFFFF for regular plugins. IDs 0x000-0x7FF are reserved for Skyrim.esm (master ID 0). Creation Kit enforces this.

**ESL local ID range:**
- **Skyrim SE v1.6.1130 and later:** 0x000-0xFFF (4096 records)
- **Skyrim SE before v1.6.1130, and Fallout 4:** 0x800-0xFFF (2048 records — range 0x000-0x7FF was reserved)

**ESL FormID Structure:**

ESL-flagged plugins use a special FormID format to allow thousands of ESLs without using regular load order slots:

```
0xFE [III] [LLL]
   │   │     │
   │   │     └─ Local ID (12 bits, 0x000-0xFFF, max 4096 records)
   │   └─────── ESL Index (12 bits, 0x000-0xFFF, which ESL plugin)
   └─────────── ESL Flag (always 0xFE for ESL records)
```

**Example:** `0xFE000800`
- `FE` - ESL flag
- `000` - First ESL plugin in load order (ESL index 0)
- `800` - Record 0x800 in that plugin

(On Skyrim SE ≥ v1.6.1130, the first valid local ID is `0x000`; on older Skyrim and Fallout 4 the range starts at `0x800` because `0x000-0x7FF` is reserved.)

**ESL Index resolution:**
- Game maintains separate ESL load order (all ESL-flagged plugins)
- ESL index (0x000-0xFFF) maps to position in ESL load order
- Allows up to 4096 ESL plugins, each with up to 4096 records
- ESL index stored in **middle 12 bits** of the FormID itself

**Master list vs. ESL index:**
- ESL-flagged plugins CAN be listed in another plugin's master list (like any dependency)
- BUT: When resolving a 0xFE FormID, the game uses the **ESL index** (middle 12 bits), not the master list position
- Regular FormIDs (0x01XXXXXX, 0x02XXXXXX, etc.) use master list position to resolve
- ESL FormIDs (0xFE\*\*\*\*\*\*) bypass master list and resolve directly via ESL index

**Resolution:**
- **Regular FormIDs:** Master index maps to plugin's master list position
- **ESL FormIDs (0xFE\*\*\*\*\*\*):** ESL index (middle 12 bits) maps to ESL load order position
- Game resolves at runtime based on actual load order

## Record Types

Common record signatures:

### Game Objects

- **ARMO** - Armor/clothing
- **WEAP** - Weapon
- **ALCH** - Potion, food, ingredient
- **BOOK** - Book, note, spell tome
- **MISC** - Miscellaneous item
- **AMMO** - Ammunition
- **KEYM** - Key

### Characters & Creatures

- **NPC_** - Non-player character
- `[LE]` **CREA** - Creature (merged into NPC_ on SE/FO4)
- **RACE** - Race definition
- **FACT** - Faction

### World Data

- **CELL** - Interior cell or exterior grid
- **WRLD** - World space (exterior)
- **REFR** - Object reference (placed object)
- **ACHR** - Actor reference (placed NPC)
- **NAVM** - Navigation mesh

### Visual & Audio

- **TXST** - Texture set
- **MATT** - Material type
- **SNDR** - Sound descriptor
- **SOUN** - Sound marker

### Gameplay

- **LVLI** - Leveled item list
- **LVLN** - Leveled NPC list
- **SPEL** - Spell, disease, ability
- **ENCH** - Enchantment
- **MGEF** - Magic effect
- **PERK** - Perk
- **QUST** - Quest
- **DIAL** - Dialogue topic

### Definitions

- **GMST** - Game setting
- **GLOB** - Global variable
- `[FO4]` `[SSE]` **KYWD** - Keyword
- **FLST** - Form list

See [Record Types Reference](../reference/record-types.md) [TBD] for complete list.

## Record Flags

The 4-byte flags field in the record header is **not a single universal bitfield**. A handful of bits mean the same thing on every record; most bits have meanings that depend on the record type (so e.g. `0x00000400` means one thing on a REFR and something unrelated on a QUST). Only the universal flags and TES4-header flags are listed below; for per-type flag tables, see UESP or xEdit's record definitions.

**Universal flags (any record):**
- `0x00000020` - Deleted
- `0x00040000` - Compressed (record data is zlib-compressed; see [Compression](#compression))

**TES4 header flags (plugin header record only):**
- `0x00000001` - ESM (master file)
- `0x00000080` - Localized (strings externalized to `.STRINGS` files)
- `[FO4]` `[SSE]` `0x00000200` - Light master / ESL-flagged
  - Doesn't count toward the 255 plugin limit
  - Limited to 4096 new records on Skyrim SE ≥ v1.6.1130 (FormID range `0x000-0xFFF`); 2048 on older Skyrim and Fallout 4 (range `0x800-0xFFF`)

**Record-type-specific flags:** Many bits (`0x00000040`, `0x00000100`, `0x00000400`, `0x00008000`, `0x00020000`, `0x00080000`, etc.) are defined per record type — e.g. REFR uses them for things like Persistent, Initially Disabled, and Visible When Distant; CELL has its own set; NPC_ has its own. Consult UESP or xEdit for the authoritative per-type table.

**ESL Requirements:**

A plugin can be ESL-flagged only if it meets these criteria:

1. **All Form IDs in the ESL range:** All new records must use FormIDs in the allowed local-ID range:
   - Skyrim SE ≥ v1.6.1130: `0x000-0xFFF`
   - Skyrim SE < v1.6.1130 and Fallout 4: `0x800-0xFFF`

2. **New record limit:** As a consequence the maximum number of new records is 4096 (or 2048 on the older range)
   - "New" means records with unique FormIDs defined in this plugin
   - Overrides of existing master records don't count toward this limit

**Important:** ESL status is determined by the **flag**, not the file extension.

**File extension behavior:**
- A plugin with `.esp` extension + ESL flag = ESL (doesn't count toward limit)
- A plugin with `.esl` extension + ESL flag = ESL (same behavior)
- The engine orders files by **extension family** — `.esm` first, then `.esl`, then `.esp`. The ESL flag itself does not affect load order; only the extension does.

**Common practice:** Most modders use `.esp` extension even for ESL-flagged plugins to maintain normal load order position. Using `.esl` extension forces the plugin into the early (master) section of the load order, which can cause issues if it needs to load after other ESPs.

**Summary:**
- Flag determines ESL behavior (FormID range, plugin limit exemption)
- Extension determines load order position (`.esm` → `.esl` → `.esp`)
- Use `.esp` extension for ESL-flagged plugins unless you specifically need early loading

## Subrecords (Fields)

Records contain subrecords (fields, or elements in xEdit parlance) with specific data. Each subrecord has a consistent binary structure.

**Subrecord structure:**
```
Subrecord (within record data)
├── Type (4 bytes, ASCII signature: EDID, FULL, MODL, etc.)
├── Data Size (2 bytes, uint16, size of data field)
└── Data (variable length, type-specific)
    ├── Raw bytes (strings, integers, floats, FormIDs)
    ├── Arrays (multiple values of same type)
    └── Structured data (can contain nested subrecords)
```

**Subrecord binary format:**
```
[TYPE:4] [SIZE:2] [DATA:SIZE]
```

**Large fields (the XXXX trick):** The size field is uint16, capping a single subrecord at 65,535 bytes. To store larger payloads (commonly used for navmesh data in Skyrim.esm), a special pattern is used:

```
[XXXX:4]  [04 00]   [actualSize:4]              ← XXXX subrecord; uint16 size is always 4, data is a uint32 holding the real size
[FIELD:4] [00 00]   [actualSize bytes of data]  ← following subrecord; its uint16 size is 0 and is overridden
```

When a parser sees `XXXX`, it must use the 32-bit size from the XXXX data when reading the *next* subrecord, ignoring that subrecord's own uint16 size (which will be 0).

**Examples:**

**EDID (Editor ID) - Simple string:**
```
45 44 49 44  02 00  49 72 6F 6E 53 77 6F 72 64 00
^EDID        ^14    ^"IronSword\0"
```

`[FO4]` `[SSE]` **FULL (Display Name) - Localized string:**
```
46 55 4C 4C  04 00  A3 F2 00 00
^FULL        ^4     ^String ID (0x0000F2A3)
```

**KWDA (Keyword Array) - Array of FormIDs:**
```
4B 57 44 41  0C 00  12 34 56 00  AB CD EF 00  01 23 45 00
^KWDA        ^12    ^FormID 1   ^FormID 2    ^FormID 3
(3 keywords × 4 bytes each = 12 bytes)
```

**VMAD (Scripts) - Complex nested structure:**
```
56 4D 41 44  [SIZE]  [version:2] [objFormat:2] [scriptCount:2] ...
^VMAD        ^varies  [nested property data, script names, etc.]
```

**Common subrecord types:**
- **EDID** - Editor ID (null-terminated ASCII string)
- **FULL** - Display name (string or string ID)
- **MODL** - Model path (null-terminated string, NIF path)
- **ICON** - Icon path (null-terminated string, DDS path)
- **DESC** - Description (string or string ID)
- **DATA** - Generic data (format varies by record type)
- `[FO4]` `[SSE]` **KSIZ** - Keyword count (uint32)
- `[FO4]` `[SSE]` **KWDA** - Keyword array (array of FormIDs)
- **VMAD** - Virtual Machine Adapter (complex structured data for Papyrus scripts)

**Notes:**
- Subrecords appear in sequence within record data
- Some subrecords are required, others optional
- Order can matter for some record types
- Compressed records (flag `0x00040000`) have compressed subrecord data (see below)
- `[FO4]` `[SSE]` String fields typically contain string ID (uint32) instead of text (when the Localized flag is set)

## String Tables

String externalization is controlled by the **Localized flag** (`0x00000080`) in the TES4 record header — not by the game edition. When the flag is set, the game loads strings from external files alongside the plugin; when it isn't, lstring fields are read as embedded zstrings (null-terminated text inside the plugin itself).

**External files (when Localized flag is set):**
- `PluginName_English.STRINGS` - Display names (FULL)
- `PluginName_English.DLSTRINGS` - Dialogue
- `PluginName_English.ILSTRINGS` - UI strings

**Format:** Binary table mapping string ID to text

**In plugin:** String fields contain a uint32 string ID into the table instead of actual text.

In practice, Skyrim SE and Fallout 4 plugins almost always set the flag (the CK enables it by default); Skyrim LE plugins almost always don't. But it is a per-plugin choice, not a hard edition difference.

## Compression

Records can be compressed with zlib. The compression flag is in the **record header** (not subrecord headers).

**Compression flag:** `0x00040000` in record header flags field

**What gets compressed:**
- The entire **record data** (all subrecords together)
- The record header itself is NOT compressed
- Subrecords don't have individual compression - the whole record data is compressed as one block

**Process:**
1. Read record header (24 bytes, uncompressed)
2. Check flags for compression bit
3. If compressed: decompress the record data with zlib
4. Parse subrecords from (decompressed) record data
5. (Recompress on save if flag set)

**Binary layout:**
```
[Record Header: 24 bytes, uncompressed]
[Record Data: compressed or uncompressed based on flag]
  ├── [Subrecord 1]
  ├── [Subrecord 2]
  └── ...
```

**xEdit:** Handles compression automatically  
**esplib:** Handles compression automatically

## Master Files

Plugins can depend on other plugins (masters).

**Master list (TES4 header):**
```
MAST - Master filename (null-terminated string)
DATA - Unknown/reserved (uint64, 8 bytes, always 0x0000000000000000)
MAST - Another master filename
DATA - Unknown/reserved (8 bytes, always 0)
...
```

**Load order:** Masters always load before dependents.

**FormID resolution:**
- FormID `0x01XXXXXX` with masters `[Skyrim.esm, Update.esm]`
- Master index `0x01` → Update.esm
- Resolved FormID points to record in Update.esm

**Behavior details**

- _ITM_ (Identical To Master) records exactly duplicate their master record. This is considered a problem because it unnecessarily masks changes to the master and interferes with other mods.

- _Deleting a master's record_ can be done--but dont. It can cause crashes when other records depend on it. Use "disable" instead.

## Plugin Best Practices

### Creating New Plugins

1. **Set up masters:**
   - Skyrim.esm (always)
   - Update.esm (Skyrim SE/FO4)
   - DLCs if using their assets

2. **Use unique editor IDs:**
   - Prefix with mod name: `MyMod_IronSword01`
   - Prevents conflicts with other mods

3. **Flag appropriately:**
   - ESM for large overhauls requiring load-first
   - ESL for small mods (≤4096 records on Skyrim SE ≥ v1.6.1130, ≤2048 elsewhere) in SE/FO4
   - ESP for standard mods

4. **Clean with xEdit:**
   - Remove ITM (identical to master) records
   - Remove UDR (undeleted references)

5. **Prefer ESL or ESM over plain ESP when possible:** Every reference in a non-flagged ESP is treated as **permanent** by the engine — always loaded into memory, always processed, always counted against the engine's reference cap, regardless of which cell it's in. ESL-flagged and ESM plugins don't have this behavior. Even if your mod has only a handful of records, ESL-flagging it (or shipping as ESM) is meaningfully gentler on the runtime than a plain ESP.

### Editing Existing Records

**Override:** Create a record with same FormID in dependent plugin
- Overrides copy all fields from the master record (xEdit/CK behavior)
- Load order determines which version wins

**Conflicts:**
- Last-loading plugin wins for each field
- Use xEdit to resolve conflicts visually

**Merging:**
- Combine subrecords from multiple plugins to preserve all changes
- Required when multiple mods edit same record

### FormID Management

**Never renumber FormIDs** after release - breaks save games.

**ESL conversion:**
- Can compact FormIDs to the ESL range (`0xFE000000-0xFE000FFF` on Skyrim SE ≥ v1.6.1130; `0xFE000800-0xFE000FFF` on older Skyrim and Fallout 4)
- Only if record count fits the range (≤4096 or ≤2048 respectively)
- Breaks saves - do before release only

## Tools

### xEdit (SSEEdit/FO4Edit)

**View/edit plugins:** Record tree, conflict detection

**Cleaning:**
```
Right-click plugin → Apply Filter for Cleaning
Remove "Identical to Master" records
Remove "Deleted" references (undelete and disable)
```

**Conflict detection:** Shows which plugins override which records

### Creation Kit

**Official editor:** WYSIWYG interface

**Common tasks:**
- Place objects in world
- Edit dialogue
- Create quests
- Set up NavMesh

**Limitations:**
- Can crash on complex edits
- Poor handling of multiple masters
- No batch operations

### esplib (Python)

**Programmatic plugin editing:**

```python
from esplib import ESPFile

# Load plugin
esp = ESPFile('MyPlugin.esp')

# Iterate records
for record in esp.records:
    if record.type == 'ARMO':
        print(f"{record.editor_id}: {record.name}")
        
# Get specific record
armor = esp.get_record('MyMod_IronArmor')

# Modify field
armor.set_field('FULL', 'Shiny Iron Armor')

# Save
esp.save('MyPlugin_Modified.esp')
```

See [esplib documentation](../tools/esplib/overview.md) [TBD] for details.

## Game-Specific Differences

### Skyrim LE
- Localized flag typically not set — strings embedded in records
- No ESL format

### Skyrim SE
- Localized flag typically set — strings externalized to STRINGS/DLSTRINGS/ILSTRINGS
- Keyword system (KYWD records)
- ESL support (Light plugins): 2048 records pre-v1.6.1130, 4096 records since
- Form 44 (updated from LE's Form 43)

### Fallout 4
- Localized flag typically set — strings externalized
- ESL support: 2048 records (FormID range `0x800-0xFFF`)
- Extended keyword system
- Material swaps (MSWP)
- OMOD attachments (weapon/armor mods)
- Structured actor values (new AVIF format)
- Form 131

## Common Issues

### Purple Textures
- Missing texture reference in MODL/texture set
- Texture file doesn't exist
- **Fix:** Check NIF or material references, ensure textures installed

### Missing Meshes (Yellow exclamation)
- MODL path incorrect or file missing
- **Fix:** Verify NIF path in MODL field

### CTD on Load
- Deleted records without proper handling
- Circular master dependencies
- Missing masters
- Corrupted record data
- **Fix:** Clean with xEdit, check load order

### Script Errors
- Missing PEX file (VMAD references missing script)
- Property not filled
- **Fix:** Recompile scripts, check Data/Scripts/

### FormID Out of Range (ESL)
- ESL plugin has record with FormID outside the allowed range (`0x000-0xFFF` on Skyrim SE ≥ v1.6.1130; `0x800-0xFFF` on older Skyrim/FO4)
- **Fix:** Compact FormIDs or convert to ESP

## See Also

- [esplib Tools](../tools/esplib/overview.md) [TBD] - Python library for plugin manipulation
- [Record Types Reference](../reference/record-types.md) [TBD] - Complete record type list
- [Plugin Issues Debugging](../debugging/plugin-issues.md) [TBD] - Troubleshooting guide
- [xEdit Reference](../tools/other-tools.md#xedit) [TBD] - xEdit usage

_Reviewed 2026-04-23, Bad Dog_