# Bethesda Modding Library

A somewhat ideosyncratic reference library for modding **Skyrim** (LE/SE) and **Fallout 4**, focusing on file formats and Python tools. 

I assembled this library out of the understanding of file formats and behavior that I needed to do my own modding, and thought it might be more generally useful.

If you work with AI, download the library and give it to the bot as a resource. That way the bot won't have to recreate all this on its own.

**NOT ALL THIS INFO IS VETTED BY AN ACTUAL HUMAN**. Where I've reviewed and validated it, I wrote a timestamp at the bottom of the page - which doesn't guarantee it's correct, of course, just that I looked at it. Corrections welcome.

## What's Inside

This library consolidates knowledge from multiple sources into a unified, searchable reference for Bethesda game modding. Whether you're creating new armor, custom races, or complex animations, you'll find the technical details you need here.

### 📁 [File Formats](file-formats/overview.md)

Deep dives into Bethesda's binary file formats:

- **[Plugins (ESP/ESM)](file-formats/plugins.md)** - Record structure, FormIDs, master resolution
- **[NIF Files](file-formats/nif-files.md)** - Meshes, skinning, shaders, partitions
- **[Animations (HKX)](file-formats/animations.md)** - Havok skeleton and animation files
- **[Physics & Collision](file-formats/physics-collision.md)** - Havok physics, HDT-SMP configs
- **[Morphs & Shape Keys](file-formats/morphs-shapekeys.md)** - TRI files, expressions, chargen
- **[Textures & Materials](file-formats/textures-materials.md)** - DDS, BGSM/BGEM
- **[Archives (BSA)](file-formats/archives.md)** - BSA format
- **[Scripts (PEX)](file-formats/scripts.md)** - Compiled Papyrus

### 🎮 [Game-Specific Information](game-specific/skyrim-le.md)

Differences between game versions:

- **[Skyrim LE](game-specific/skyrim-le.md)** - 32-bit, NiTriShape, classic features
- **[Skyrim SE](game-specific/skyrim-se.md)** - 64-bit, BSTriShape, BSDynamicTriShape
- **[Fallout 4](game-specific/fallout4/overview.md)** - Segments, connect points, BGSM materials, workshop system

### 🛠️ [Tools](tools/pynifly/overview.md)

Working with the formats programmatically:

- **[PyNifly](tools/pynifly/overview.md)** - Blender addon for NIF/HKX import/export
  - Installation, importing, exporting, Python API, example scripts
- **[esplib](tools/esplib/overview.md)** - Python library for ESP/ESM manipulation
  - Schema system, record definitions, CLI tools
- **[Other Tools](tools/other-tools.md)** - xEdit, Creation Kit, NifSkope (reference only)

### 📝 [Workflows](workflows/character-creation.md)

Step-by-step guides for common modding tasks:

- **[Character Creation](workflows/character-creation.md)** - Races, NPCs, head parts, FaceGen
- **[Armor & Clothing](workflows/armor-clothing.md)** - ARMO/ARMA records, body weights, BodySlide
- **[Meshes & Modeling](workflows/meshes-modeling.md)** - Import/export, Blender workflow
- **[Animations](workflows/animations.md)** - HKX skeleton, creating/exporting animations
- **[Physics & Collisions](workflows/physics-collisions.md)** - HDT-SMP, ground collision, Havok
- **[Textures & Materials](workflows/textures-materials.md)** - Shader setup, DDS workflow

### 🐛 [Debugging](debugging/ctd-crashes.md)

Troubleshooting common issues:

- **[CTD (Crashes)](debugging/ctd-crashes.md)** - Load-time crashes, memory issues
- **[Mesh Issues](debugging/mesh-issues.md)** - Clipping, weighting, missing parts
- **[Animation Issues](debugging/animation-issues.md)** - Import/export failures
- **[Physics Issues](debugging/physics-issues.md)** - HDT not working, collision problems
- **[Plugin Issues](debugging/plugin-issues.md)** - CK errors, FormID conflicts

### 📚 [Reference](reference/record-types.md)

Quick lookup tables:

- **[Record Types](reference/record-types.md)** - ESP/ESM record signatures
- **[Bone Names](reference/bone-names.md)** - Standard skeleton bone names
- **[Shader Flags](reference/shader-flags.md)** - SLSF1/SLSF2 flags
- **[Partition Names](reference/partition-names.md)** - SBP_* naming conventions
- **[Expression Morphs](reference/expression-morphs.md)** - Standard morph names

### 🤖 [AI Reference](ai-reference/glossary.md)

Machine-readable structured data for AI consumers:

- **[Glossary](ai-reference/glossary.md)** - Precise terminology definitions
- **[Validation Rules](ai-reference/validation-rules.md)** - Constraints and limits
- **[Decision Trees](ai-reference/decision-trees.md)** - When to use X vs Y
- **[Code Templates](ai-reference/code-templates.md)** - Complete working examples
- **[State Machines](ai-reference/state-machines.md)** - Multi-step workflows
- **[File Path Conventions](ai-reference/file-path-conventions.md)** - Standard file locations
- **[Default Values](ai-reference/default-values.md)** - Standard defaults

## Scope

**Games Covered:**
- ✅ Skyrim LE (32-bit)
- ✅ Skyrim SE (64-bit)
- ✅ Fallout 4 (64-bit)

**Tools Covered:**
- ✅ PyNifly (Blender addon, Python API)
- ✅ esplib (Python library)
- ✅ xEdit (reference only)
- ✅ Creation Kit (brief reference)

**Explicitly Out of Scope:**
- ❌ Starfield, Fallout 76, Fallout 3, Fallout New Vegas
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

Found an error? Have additional information? Contributions welcome!

## Organization Principles

- **Format vs Tool** - File format specs are tool-agnostic; tool-specific conventions are clearly marked
- **Universal vs Game-Specific** - Common information in "File Formats"; differences in "Game-Specific"
- **Blender-Agnostic** - Game concepts explained first, then Blender implementation details
- **Complete Examples** - No placeholders or "fill in" comments in code examples

---

**Ready to dive in?** Start with [File Formats](file-formats/overview.md) or jump to [Workflows](workflows/character-creation.md) for practical guides.
