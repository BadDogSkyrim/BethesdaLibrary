# Bethesda Modding Library

A somewhat ideosyncratic reference library for modding **Skyrim** (LE/SE), **Fallout 4**, and **Starfield**, focusing on file formats and Python tools. If you work with AI, hand this library to the bot as a resource so it doesn't have to reconstruct all this itself.

**NOT ALL THIS INFO IS VETTED BY AN ACTUAL HUMAN.** Where I've reviewed and validated a page, there's a timestamp at the bottom — which doesn't guarantee it's correct, just that I looked at it. Corrections welcome.

**LOTS OF ELEMENTS ARE STILL TBD.** I'm building this as I need it, so many pages aren't written yet. It's more complete for Starfield and FO4 than for Skyrim, because that's where I'm working right now. Links tagged **[TBD]** point at pages that don't exist yet — no need to chase them.

## What's Inside

This library consolidates knowledge from multiple sources into a unified, searchable reference for Bethesda game modding. Whether you're creating new armor, custom races, or complex animations, you'll find the technical details you need here.

### 📁 [File Formats](file-formats/overview.md)

Deep dives into Bethesda's binary file formats (shared across Skyrim and Fallout 4):

- **[Plugins (ESP/ESM)](file-formats/plugins.md)** - Record structure, FormIDs, master resolution
- **[NIF Files](file-formats/nif-files.md)** - Meshes, skinning, shaders, partitions
- **[NIF Animations](file-formats/nif-animations.md)** - Scene-graph object animations (doors, banners, glow)
- **[Animations (HKX)](file-formats/animations.md)** - Havok skeleton and animation files
- **[Physics & Collision](file-formats/physics-collision.md)** - Havok physics, HDT-SMP configs
- **[Morphs & Shape Keys](file-formats/morphs-shapekeys.md)** - TRI files, expressions, chargen
- **[Textures & Materials](file-formats/textures-materials.md)** - DDS, BGSM/BGEM
- **[Archives (BSA)](file-formats/archives.md)** - BSA format
- **[Scripts (PEX)](file-formats/scripts.md)** - Compiled Papyrus

### 🎮 Game-Specific Information

Where a game diverges from the shared formats above, it gets its own section fronted by a game-overview page:

- **[Starfield](file-formats/starfield-overview.md)** - Creation Engine 2: geometry-less NIF + external `.mesh`, layered `.mat`/`.cdb` materials, component-based plugins, in-house animation. The most complete area right now:
  - **[Meshes (NIF + .mesh)](file-formats/starfield-meshes.md)** - BSGeometry, external `.mesh` binary format, skinning
  - **[Materials & Textures](file-formats/starfield-materials.md)** - layered `.mat`/`.cdb`, shader models, DDS conventions ([worked example](file-formats/starfield-material-worked-example.md))
  - **[Chargen, Race & Skeleton](file-formats/starfield-chargen.md)** - RACE/HDPT/MRPH/BMOD, morphs, custom races
  - **[Plugins & Archives](file-formats/starfield-plugins.md)** - component records, master tiers, BA2 v2/v3
  - **[Tools](file-formats/starfield-tools.md)** - the Starfield tooling directory, grouped by task
- **[Fallout 4](game-specific/fallout4/overview.md)** - 64-bit Creation Engine: BGSM/BGEM materials, mesh segments, connect points, BA2 archives, ESL plugins:
  - **[Connect Points](game-specific/fallout4/connect-points.md)** - runtime mesh attachment points
  - **[Dismemberment](game-specific/fallout4/dismemberment.md)** - limb severing (BSSubIndexTriShape segments, `.ssf`)
- **[Skyrim](game-specific/skyrim/overview.md)** - LE (32-bit, NiTriShape) and SE (64-bit, BSTriShape); shared formats with per-edition differences

### 🛠️ [Tools](tools/pynifly/overview.md)

Working with the formats programmatically:

- **[PyNifly](tools/pynifly/overview.md)** - Blender addon for NIF/HKX import/export
  - **[Installation](tools/pynifly/installation.md)** - setup and configuration
  - Importing, exporting, Python API, example scripts [TBD]
- **[esplib](tools/esplib/overview.md) [TBD]** - Python library for ESP/ESM manipulation
  - Schema system, record definitions, CLI tools
- **[Other Tools](tools/other-tools.md) [TBD]** - xEdit, Creation Kit, NifSkope (reference only)

### 🐍 Repository Scripts

Python scripts that live in the [repository](https://github.com/BadDogSkyrim/BethesdaLibrary) — used while working out the plugin format. Most are Skyrim-focused investigation scripts with hardcoded data paths, so read them before running:

- **[dump_hkx.py](https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/dump_hkx.py)** - dump a Havok `.hkx` packfile's structure as human-readable text (the one general-purpose tool here)
- **[inspect_masters.py](https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/inspect_masters.py)** - dump a plugin's TES4 header and master list
- FormID range investigation:
  - [check_all_formid_ranges.py](https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/check_all_formid_ranges.py) - FormID ranges across masters, DLC, and ESL files
  - [check_formids_deep.py](https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/check_formids_deep.py) - recurse records and FormIDs in Skyrim.esm
  - [check_formids_raw.py](https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/check_formids_raw.py) - first 50 FormIDs in Skyrim.esm
  - [check_esl_formids.py](https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/check_esl_formids.py) - ESL-relevant FormID ranges in Skyrim.esm + DLCs
  - [check_esl_ranges.py](https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/check_esl_ranges.py) - FormID ranges in actual `.esl` files
  - [check_dawnguard.py](https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/check_dawnguard.py) - recursive record read of Dawnguard.esm
- Override detection:
  - [check_overrides.py](https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/check_overrides.py) - read subrecords and detect override records
  - [check_override_final.py](https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/check_override_final.py) - override detection with record-type filtering
  - [simple_override_check.py](https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/simple_override_check.py) - examine overrides in a single ESP

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

Found an error? Have additional information? Contributions welcome! See **[CONVENTIONS.md](CONVENTIONS.md)** for the page style and formatting conventions.

## Organization Principles

- **Format vs Tool** - File format specs are tool-agnostic; tool-specific conventions are clearly marked
- **Universal vs Game-Specific** - Common information in "File Formats"; per-game divergences in "Game-Specific"
- **Blender-Agnostic** - Game concepts explained first, then Blender implementation details
- **Complete Examples** - No placeholders or "fill in" comments in code examples

---

**Ready to dive in?** Start with [File Formats](file-formats/overview.md) for the shared formats, or jump straight to [Starfield](file-formats/starfield-overview.md) for the most complete section.
