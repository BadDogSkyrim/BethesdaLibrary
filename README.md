# Bethesda Modding Library

A somewhat ideosyncratic reference library for modding **Skyrim** (LE/SE), **Fallout 4**, and **Starfield**, focusing on file formats and Python tools. 

I assembled this library out of the understanding of file formats and behavior that I needed to do my own modding, and thought it might be more generally useful.

If you work with AI, download the library and give it to the bot as a resource. That way the bot won't have to recreate all this on its own.

**NOT ALL THIS INFO IS VETTED BY AN ACTUAL HUMAN**. Where I've reviewed and validated it, I wrote a timestamp at the bottom of the page - which doesn't guarantee it's correct, of course, just that I looked at it. Corrections welcome.

**LOTS OF ELEMENTS ARE STILL TBD**. I'm building this as I need it, so there are a lot of pages that are TBD. It's actually more useful for Starfield and FO4 than for Skyrim because that's where I'm working right now. Links tagged **[TBD]** point at pages I haven't written yet — no need to chase them.

## What's Inside

This library consolidates knowledge from multiple sources into a unified, searchable reference for Bethesda game modding. Whether you're creating new armor, custom races, or complex animations, you'll find the technical details you need here.

### 📁 [File Formats](docs/file-formats/overview.md)

Deep dives into Bethesda's binary file formats (shared across Skyrim and Fallout 4):

- **[Plugins (ESP/ESM)](docs/file-formats/plugins.md)** - Record structure, FormIDs, master resolution
- **[NIF Files](docs/file-formats/nif-files.md)** - Meshes, skinning, shaders, partitions
- **[NIF Animations](docs/file-formats/nif-animations.md)** - Scene-graph object animations (doors, banners, glow)
- **[Animations (HKX)](docs/file-formats/animations.md)** - Havok skeleton and animation files
- **[Physics & Collision](docs/file-formats/physics-collision.md)** - Havok physics, HDT-SMP configs
- **[Morphs & Shape Keys](docs/file-formats/morphs-shapekeys.md)** - TRI files, expressions, chargen
- **[Textures & Materials](docs/file-formats/textures-materials.md)** - DDS, BGSM/BGEM
- **[Connect Points](docs/file-formats/connect-points.md)** - FO4 runtime mesh attachment points
- **[Dismemberment](docs/file-formats/dismemberment.md)** - FO4 limb severing (BSDismemberSkinInstance, segments)
- **[Archives (BSA)](docs/file-formats/archives.md)** - BSA format
- **[Scripts (PEX)](docs/file-formats/scripts.md)** - Compiled Papyrus

### 🎮 Game-Specific Information

Where a game diverges from the shared formats above, it gets its own section fronted by a game-overview page:

- **[Starfield](docs/file-formats/starfield-overview.md)** - Creation Engine 2: geometry-less NIF + external `.mesh`, layered `.mat`/`.cdb` materials, component-based plugins, in-house animation. The most complete area right now:
  - **[Meshes (NIF + .mesh)](docs/file-formats/starfield-meshes.md)** - BSGeometry, external `.mesh` binary format, skinning
  - **[Materials & Textures](docs/file-formats/starfield-materials.md)** - layered `.mat`/`.cdb`, shader models, DDS conventions ([worked example](docs/file-formats/starfield-material-worked-example.md))
  - **[Chargen, Race & Skeleton](docs/file-formats/starfield-chargen.md)** - RACE/HDPT/MRPH/BMOD, morphs, custom races
  - **[Plugins & Archives](docs/file-formats/starfield-plugins.md)** - component records, master tiers, BA2 v2/v3
  - **[Tools](docs/file-formats/starfield-tools.md)** - the Starfield tooling directory, grouped by task
- **Skyrim LE** [TBD] - 32-bit, NiTriShape, classic features
- **Skyrim SE** [TBD] - 64-bit, BSTriShape, BSDynamicTriShape
- **Fallout 4** [TBD] - workshop system, FaceBones, BGSM material system (see Connect Points / Dismemberment above)

### 🛠️ [Tools](docs/tools/pynifly/overview.md)

Working with the formats programmatically:

- **[PyNifly](docs/tools/pynifly/overview.md)** - Blender addon for NIF/HKX import/export
  - **[Installation](docs/tools/pynifly/installation.md)** - setup and configuration
  - Importing, exporting, Python API, example scripts [TBD]
- **[esplib](tools/esplib/overview.md) [TBD]** - Python library for ESP/ESM manipulation
  - Schema system, record definitions, CLI tools
- **[Other Tools](tools/other-tools.md) [TBD]** - xEdit, Creation Kit, NifSkope (reference only)

### 🐍 Repository Scripts

Python scripts that live in this repo — used while working out the plugin format. Most are Skyrim-focused investigation scripts with hardcoded data paths, so read them before running:

- **[dump_hkx.py](dump_hkx.py)** - dump a Havok `.hkx` packfile's structure as human-readable text (the one general-purpose tool here)
- **[inspect_masters.py](inspect_masters.py)** - dump a plugin's TES4 header and master list
- FormID range investigation:
  - [check_all_formid_ranges.py](check_all_formid_ranges.py) - FormID ranges across masters, DLC, and ESL files
  - [check_formids_deep.py](check_formids_deep.py) - recurse records and FormIDs in Skyrim.esm
  - [check_formids_raw.py](check_formids_raw.py) - first 50 FormIDs in Skyrim.esm
  - [check_esl_formids.py](check_esl_formids.py) - ESL-relevant FormID ranges in Skyrim.esm + DLCs
  - [check_esl_ranges.py](check_esl_ranges.py) - FormID ranges in actual `.esl` files
  - [check_dawnguard.py](check_dawnguard.py) - recursive record read of Dawnguard.esm
- Override detection:
  - [check_overrides.py](check_overrides.py) - read subrecords and detect override records
  - [check_override_final.py](check_override_final.py) - override detection with record-type filtering
  - [simple_override_check.py](simple_override_check.py) - examine overrides in a single ESP

### 📝 [Workflows](workflows/character-creation.md) [TBD]

Step-by-step guides for common modding tasks:

- **[Character Creation](workflows/character-creation.md) [TBD]** - Races, NPCs, head parts, FaceGen
- **[Armor & Clothing](workflows/armor-clothing.md) [TBD]** - ARMO/ARMA records, body weights, BodySlide
- **[Meshes & Modeling](workflows/meshes-modeling.md) [TBD]** - Import/export, Blender workflow
- **[Animations](workflows/animations.md) [TBD]** - HKX skeleton, creating/exporting animations
- **[Physics & Collisions](workflows/physics-collisions.md) [TBD]** - HDT-SMP, ground collision, Havok
- **[Textures & Materials](workflows/textures-materials.md) [TBD]** - Shader setup, DDS workflow

### 🐛 [Debugging](debugging/ctd-crashes.md) [TBD]

Troubleshooting common issues:

- **[CTD (Crashes)](debugging/ctd-crashes.md) [TBD]** - Load-time crashes, memory issues
- **[Mesh Issues](debugging/mesh-issues.md) [TBD]** - Clipping, weighting, missing parts
- **[Animation Issues](debugging/animation-issues.md) [TBD]** - Import/export failures
- **[Physics Issues](debugging/physics-issues.md) [TBD]** - HDT not working, collision problems
- **[Plugin Issues](debugging/plugin-issues.md) [TBD]** - CK errors, FormID conflicts

### 📚 [Reference](reference/record-types.md) [TBD]

Quick lookup tables:

- **[Record Types](reference/record-types.md) [TBD]** - ESP/ESM record signatures
- **[Bone Names](reference/bone-names.md) [TBD]** - Standard skeleton bone names
- **[Shader Flags](reference/shader-flags.md) [TBD]** - SLSF1/SLSF2 flags
- **[Partition Names](reference/partition-names.md) [TBD]** - SBP_* naming conventions
- **[Expression Morphs](reference/expression-morphs.md) [TBD]** - Standard morph names

### 🤖 [AI Reference](ai-reference/glossary.md) [TBD]

Machine-readable structured data for AI consumers:

- **[Glossary](ai-reference/glossary.md) [TBD]** - Precise terminology definitions
- **[Validation Rules](ai-reference/validation-rules.md) [TBD]** - Constraints and limits
- **[Decision Trees](ai-reference/decision-trees.md) [TBD]** - When to use X vs Y
- **[Code Templates](ai-reference/code-templates.md) [TBD]** - Complete working examples
- **[State Machines](ai-reference/state-machines.md) [TBD]** - Multi-step workflows
- **[File Path Conventions](ai-reference/file-path-conventions.md) [TBD]** - Standard file locations
- **[Default Values](ai-reference/default-values.md) [TBD]** - Standard defaults

## Scope

**Games Covered:**
- ✅ Skyrim LE (32-bit)
- ✅ Skyrim SE (64-bit)
- ✅ Fallout 4 (64-bit)
- ✅ Starfield (Creation Engine 2) - most complete area right now

**Tools Covered:**
- ✅ PyNifly (Blender addon, Python API)
- ✅ esplib (Python library)
- ✅ xEdit (reference only)
- ✅ Creation Kit (brief reference)

**Explicitly Out of Scope:**
- ❌ Fallout 76, Fallout 3, Fallout New Vegas
- ❌ Pascal/xEdit scripting (deprecated)
- ❌ Detailed Creation Kit workflows
- ❌ Executable validators or decision tree functions

## Source Materials

This library consolidates knowledge from:

- **xEditDev** - ESP/ESM plugin development, esplib toolkit
- **PyNifly** - NIF/HKX mesh and animation toolkit
- **PyNifly Wiki** - Format documentation and usage guides
- **Field Experience** - Debugging notes and practical solutions

## Contributing

Found an error? Have additional information? Contributions welcome! See **[docs/CONVENTIONS.md](docs/CONVENTIONS.md)** for the page style and formatting conventions.

## Organization Principles

- **Format vs Tool** - File format specs are tool-agnostic; tool-specific conventions are clearly marked
- **Universal vs Game-Specific** - Common information in "File Formats"; per-game divergences in "Game-Specific"
- **Blender-Agnostic** - Game concepts explained first, then Blender implementation details
- **Complete Examples** - No placeholders or "fill in" comments in code examples

---

**Ready to dive in?** Start with [File Formats](docs/file-formats/overview.md) for the shared formats, or jump straight to [Starfield](docs/file-formats/starfield-overview.md) for the most complete section.
