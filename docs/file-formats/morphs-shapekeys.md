# Morphs & Shape Keys (TRI Files)

TRI files contain morph target data for character customization, facial expressions, and body morphs. They define vertex offsets from a base mesh.

## Overview

**Extension:** `.tri`  
**Format:** Binary vertex offset data  
**Type:** Morph targets (blend shapes, shape keys)

**Use cases:**
- Facial expressions (smile, frown, blink)
- Character creation sliders (nose size, jaw width)
- BodySlide morphs (body shape presets)
- Lip-sync phonemes
- Custom race features

**Games:** Skyrim LE, Skyrim SE, Fallout 4

## File Structure

```
TRI File
├── Header
│   ├── Magic string
│   ├── Version
│   └── Morph count
├── Morphs
│   ├── Morph Name (string)
│   ├── Multiplier (scale factor)
│   └── Vertex Offsets
│       ├── Vertex Index (which vertex moves)
│       ├── X offset
│       ├── Y offset
│       └── Z offset
└── (repeat for each morph)
```

**Key points:**
- **Sparse data:** Only stores vertices that move (not all vertices)
- **Additive:** Offsets added to base mesh positions
- **Named morphs:** Each morph has a string name
- **Multiplier:** Global scale for morph strength

## Morph Types

### Facial Expressions

Morphs for emotions and expressions.

`[Skyrim]` **Standard expression morphs:**
```
Aah              - Mouth open (A sound)
BigAah           - Mouth wide open
BMP              - B/M/P sounds (lips closed)
ChJSh            - Ch/J/Sh sounds
DST              - D/S/T sounds
Eee              - Mouth wide (E sound)
Eh               - Eh sound
FV               - F/V sounds (teeth on lip)
I                - I sound
K                - K sound
N                - N sound
Oh               - O sound (mouth round)
OohQ             - Ooh/Q sounds
R                - R sound
Th               - Th sound (tongue out)
W                - W sound (lips pursed)

EyeBlinkLeft     - Left eye blink
EyeBlinkRight    - Right eye blink
EyeClosedLeft    - Left eye closed
EyeClosedRight   - Right eye closed

BrowDownLeft     - Left brow furrow
BrowDownRight    - Right brow furrow
BrowInLeft       - Left brow inward
BrowInRight      - Right brow inward
BrowUpLeft       - Left brow raised
BrowUpRight      - Right brow raised

MoodAnger        - Angry expression
MoodDisgusted    - Disgusted expression
MoodFear         - Fearful expression
MoodHappy        - Happy expression
MoodNeutral      - Neutral (reset)
MoodPuzzled      - Puzzled expression
MoodSad          - Sad expression
MoodSurprised    - Surprised expression

LookDown         - Eyes look down
LookLeft         - Eyes look left
LookRight        - Eyes look right
LookUp           - Eyes look up

Squint           - Squinting
CombatAnger      - Combat angry face
CombatShout      - Combat shout face

(more...)
```

See [Expression Morphs Reference](../reference/expression-morphs.md) [TBD] for complete list.

### CharGen Morphs

Morphs used in character creation (RaceMenu sliders).

**Common CharGen morphs (examples):**
```
Nose Length      - Nose forward/back
Nose Width       - Nose wide/narrow
Nose Height      - Nose up/down
Chin Forward     - Chin protrusion
Chin Width       - Jaw width
Cheekbone Height - Cheekbone prominence
Eye Height       - Eye vertical position
Eye Depth        - Eye socket depth
Brow Height      - Brow vertical position
Lip Thickness    - Lip fullness
(50+ sliders in vanilla Skyrim)
```

`[Skyrim]` **RaceMenu extended:** Additional custom morphs via plugins.

### BodySlide Morphs

Body shape presets for armor and character meshes.

**CBBE/UNP morphs (examples):**
```
Breasts          - Breast size
BreastsSmall     - Smaller breast size
Waist            - Waist width
Hips             - Hip width
Belly            - Belly size
Butt             - Butt size
Arms             - Arm thickness
Legs             - Leg thickness
```

**Usage:** BodySlide builds outfit meshes for specific body morph.

### Custom Morphs

Mods can add custom morphs for unique features.

**Examples:**
- Wings (spread/folded)
- Tail shape variations
- Muscle definition
- Horns, ears, other features

## TRI File Associations

### Head Meshes

TRI files reference specific head meshes.

**Reference in NIF:**
```
NiStringExtraData "BODYTRI"
Value: "headmorph_tri_path.tri"
```

**Location:** Relative to `Data/meshes/`

**Example:**
```
NIF: meshes/actors/character/character assets/female/femaleheadkhajiit.nif
TRI: meshes/actors/character/character assets/female/femaleheadkhajiit.tri
```

**Requirement:** TRI vertex count and order must match NIF mesh vertices.

### Body Meshes

Similar to head meshes, but for body morphs.

**BodySlide workflow:**
- Base mesh (reference)
- TRI with morphs
- Build outputs multiple NIF variants

### FaceGen

Skyrim generates per-NPC head meshes using morph combinations.

**FaceGen files (per NPC):**
- `Data/meshes/actors/character/facegendata/facegeom/<Plugin>/<FormID>.nif`
- Baked head mesh with NPC-specific morphs applied

**TRI still required:** For runtime expressions on baked head.

## Creating TRI Files

### With Blender (PyNifly)

PyNifly supports exporting TRI files with shape keys.

**Workflow:**
1. **Import base NIF** with TRI (if exists)
2. **Create shape keys** in Blender
   - Add shape key: Mesh properties → Shape Keys → + button
   - Edit vertices in Edit mode with shape key selected
   - Name shape key (must match expected morph names)
3. **Export NIF + TRI** via PyNifly
   - File → Export → NetImmerse/Gamebryo (.nif)
   - Check "Export shape keys to TRI"

**Shape key naming:**
- Use exact names from expression/CharGen lists
- Case-sensitive
- PyNifly prefix convention: Some tools use `*_` prefix

**Example Blender setup:**
```
Base mesh: femaleheadkhajiit
Shape keys:
  ├─ Basis (base shape)
  ├─ Aah
  ├─ Eee
  ├─ Oh
  ├─ EyeBlinkLeft
  ├─ EyeBlinkRight
  ├─ MoodHappy
  └─ (more...)
```

### With BodySlide

BodySlide/Outfit Studio workflow for body morphs.

**Outfit Studio:**
1. Load base mesh (reference body)
2. Load outfit mesh (armor/clothing)
3. **Conform to body** (fit outfit to body)
4. **Copy bone weights** from reference
5. **Build morphs** (slider sets)
6. **Save project** (.osp + .xml)

**BodySlide:**
1. Load preset
2. Adjust sliders
3. **Build** → Generates NIF with morphs baked

**TRI generation:** Outfit Studio creates TRI automatically for morph sets.

### Manual/Scripting

**Python with PyNifly:**

```python
from io_scene_nifly import pynifly

# Load base mesh
nif = pynifly.NifFile('base_mesh.nif')

# Create TRI
tri = pynifly.TriFile()

# Add morph
morph = pynifly.TriMorph()
morph.name = "CustomMorph"
morph.multiplier = 1.0

# Add vertex offset
morph.vertices.append({
    'index': 123,  # Vertex index in mesh
    'x': 0.5,      # X offset
    'y': 0.0,      # Y offset  
    'z': 0.2       # Z offset
})

# Add more vertices...

tri.morphs.append(morph)

# Save
tri.save('base_mesh.tri')
```

## Morph Constraints

### Vertex Order

**Critical:** TRI vertex indices must match NIF mesh vertex order exactly.

**Issue:** Re-importing and editing mesh in Blender can reorder vertices.

**Solution:**
- Use shape keys from original import
- Don't delete and recreate mesh
- Verify vertex count matches

### Morph Names

**Case-sensitive:** `Aah` ≠ `aah` ≠ `AAH`

**Game-specific:** CharGen morph names differ between Skyrim and FO4.

**RaceMenu:** Allows custom morph names via configuration.

### Vertex Limits

Same as mesh: 65535 vertices maximum (uint16 index).

### Performance

**Morph count:** No hard limit, but many morphs (100+) can impact performance.

**Sparse data:** Only include vertices that actually move (magnitude > threshold).

**Threshold:** Offsets < 0.001 units effectively invisible, can omit.

## Game-Specific Differences

### Skyrim LE/SE

**Head morphs:**
- Expression morphs (phonemes, emotions)
- CharGen morphs (50+ sliders)
- Required for NPC heads

**Body morphs:**
- Optional (vanilla bodies don't use TRI)
- Mod frameworks (CBBE, UNP) add body morphs

**FaceGen:**
- TRI applied to base head mesh
- Game bakes FaceGen NIF per NPC
- TRI still needed for runtime expressions

### Fallout 4

**FaceGen system:**
- More complex morph system
- Separate morph categories
- Dual-armature FaceBones complicate workflow

**CharGen morphs:**
- Different names than Skyrim
- More granular face control

**Body morphs:**
- Less common (vanilla doesn't use)
- Mod frameworks exist but less standardized

**LooksMenu:** FO4's RaceMenu equivalent.

## Common Issues

### Morphs Not Working
- **TRI not referenced:** NIF missing NiStringExtraData "BODYTRI"
- **Path wrong:** TRI path in NIF doesn't match actual file location
- **Vertex mismatch:** TRI vertex indices don't match mesh
- **Fix:** Check BODYTRI reference, verify TRI path, re-export mesh and TRI together

### Morphs Look Wrong
- **Vertex order changed:** Mesh edited after TRI created
- **Scale mismatch:** Mesh scaled but TRI not updated
- **Multiplier wrong:** TRI multiplier too high or low
- **Fix:** Re-export TRI from current mesh, check multiplier values

### CharGen Sliders Don't Appear
- **Missing morph names:** TRI doesn't have expected morph names
- **Race doesn't support:** Race definition doesn't reference TRI
- **Mod conflict:** Another mod overriding CharGen
- **Fix:** Verify morph names, check race RACE record, check load order

### FaceGen Looks Different
- **TRI morph mismatch:** FaceGen baked with different TRI
- **Regenerate FaceGen:** CK or tool generated with wrong assets
- **Fix:** Regenerate FaceGen with correct TRI, ensure TRI in correct location

### BodySlide Build Fails
- **Reference body mismatch:** Outfit not conformed to reference
- **Bone weights missing:** Outfit not weighted
- **Vertex count mismatch:** Outfit edited after project saved
- **Fix:** Re-conform in Outfit Studio, copy bone weights, rebuild project

## Tools

### PyNifly (Blender)

**Import/export TRI** with shape keys.

**Features:**
- Shape key ↔ TRI morph conversion
- Automatic BODYTRI reference in NIF
- Batch export multiple meshes

See [PyNifly documentation](../tools/pynifly/overview.md).

### BodySlide / Outfit Studio

**Body morph workflow** for armor/clothing.

**Features:**
- Visual slider adjustment
- Batch building multiple presets
- Morph set management

### RaceMenu (SKSE Plugin)

**In-game CharGen extender** for Skyrim SE.

**Features:**
- Additional morph sliders
- Morph loading from files
- Preset save/load
- Sculpt mode (real-time vertex editing)

### LooksMenu (F4SE Plugin)

**RaceMenu equivalent for Fallout 4.**

### Nif-Scanner (xEdit Script)

**Scan for BODYTRI references** in NIFs.

**Usage:** Find which NIFs reference which TRI files.

## Workflow Tips

### Creating Expression Morphs

1. **Use reference photos:** Real facial expressions as guide
2. **Subtle movements:** Small vertex offsets (0.1-2.0 units)
3. **Symmetric morphs:** Mirror left/right for most expressions
4. **Test in-game:** Preview with console commands

`[Skyrim]` **Console:**
```
showracemenu  ; Open CharGen
tfc 1         ; Free camera
; Use RaceMenu to test expression sliders
```

### Creating CharGen Morphs

1. **Define range:** Extreme negative and positive values
2. **Zero at default:** Morph at 0.0 = base head
3. **Independent morphs:** Each slider affects different vertices
4. **Test combinations:** Ensure morphs don't conflict

### Creating Body Morphs

1. **Start with reference:** Use established body (CBBE, UNP)
2. **Preserve topology:** Don't add/remove vertices
3. **Maintain weights:** Keep bone weights intact
4. **Build variations:** Multiple presets (slim, curvy, athletic, etc.)

## See Also

- [NIF Files](nif-files.md) - BODYTRI references, BSDynamicTriShape
- [PyNifly](../tools/pynifly/overview.md) - Blender TRI workflow
- [Expression Morphs Reference](../reference/expression-morphs.md) [TBD] - Standard morph names
- [Character Creation Workflow](../workflows/character-creation.md) [TBD] - Using TRI in races
- [Mesh Issues Debugging](../debugging/mesh-issues.md) [TBD] - TRI troubleshooting
