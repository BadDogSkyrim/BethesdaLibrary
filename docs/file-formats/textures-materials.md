# Textures & Materials

Textures provide surface appearance (color, normal maps, specular) while materials define how textures are applied and rendered.

## Overview

**Texture format:** DDS (DirectDraw Surface)  
**Material systems:**
- **Skyrim LE/SE:** Material properties embedded in NIF (BSLightingShaderProperty)
- **Fallout 4:** External material files (BGSM/BGEM)

## DDS Textures

### Format

**Extension:** `.dds`  
**Type:** DirectX compressed texture format  
**Compression:** Block-based (DXT1/DXT5, BC5, BC7)

**Advantages:**
- GPU-native format (loads directly to VRAM)
- Compressed (smaller file size)
- Mipmaps included (LOD support)
- Fast to load

### Compression Types

#### DXT1 (BC1)
**Use case:** Opaque textures (no alpha)

**Compression:** 6:1 ratio  
**Quality:** Good for diffuse textures  
**Alpha:** 1-bit alpha (on/off only)

**Best for:**
- Diffuse maps (base color)
- Specular maps
- Environment maps

#### DXT3 (BC2)
**Use case:** Textures with sharp alpha transitions

**Compression:** 4:1 ratio  
**Alpha:** Explicit 4-bit alpha (16 levels)

**Best for:**
- Billboards with cutouts
- Decals with hard edges

#### DXT5 (BC3)
**Use case:** Textures with smooth alpha gradients

**Compression:** 4:1 ratio  
**Alpha:** Interpolated alpha (smooth gradients)

**Best for:**
- Normal maps (compress well)
- Alpha-blended effects
- Transparency masks

#### BC5 (Skyrim SE, Fallout 4)
**Use case:** Two-channel maps (tangent normals, packed specular/glossiness)

**Also known as:** ATI2 / 3Dc  
**Compression:** 4:1 vs. 32-bit RGBA (2:1 vs. storing two 8-bit channels uncompressed)  
**Channels:** Red and Green only — **blue channel is omitted**. Each of the two stored channels uses the same 8-bit interpolated encoding as DXT5's alpha block, giving far better precision than DXT5's RGB block.

**How the missing blue is handled:**
- For tangent-space normals, the shader reconstructs Z from X and Y: `B = sqrt(1 - R² - G²)`. Because the surface normal is unit-length, the blue component is redundant and can be recomputed exactly.

**Best for:**
- **`[FO4]` Tangent-space normal maps (`_n`)** - Fallout 4's default normal format. Two high-precision channels with no cross-channel bleeding produce cleaner normals than DXT5.
- **`[FO4]` Combined specular/glossiness (`_s`)** - FO4 packs specular into one channel and glossiness/smoothness into the other.

**Requirement:** DX11+ (SE/FO4 only, not LE).

**Note:** Because blue is dropped, a BC5 file opened in an image viewer looks yellow/green rather than the familiar purple of a DXT5 normal map — this is expected, not corruption.

#### BC7 (Skyrim SE, Fallout 4)
**Use case:** High-quality diffuse textures

**Compression:** 4:1 ratio  
**Quality:** Better than DXT1/5 (fewer artifacts)

**Best for:**
- Diffuse maps (SE/FO4)
- Anything needing high quality

**Requirement:** DX11+ (SE/FO4 only, not LE)

#### Uncompressed
**Use case:** Maximum quality, large file size

**Formats:**
- A8R8G8B8 (32-bit RGBA)
- R8G8B8 (24-bit RGB)

**Best for:**
- UI elements (minimal in-game use)
- Source files (compress to DXT for game)

### Mipmaps

**Mipmaps:** Progressively smaller versions of texture for distant objects.

**Example:**
```
Mip 0: 2048x2048 (full resolution)
Mip 1: 1024x1024
Mip 2: 512x512
Mip 3: 256x256
...
Mip 11: 1x1
```

**Benefits:**
- Better performance (fewer pixels to sample)
- Reduces aliasing/shimmering at distance
- GPU automatically selects appropriate mip level

**Generation:** Most tools auto-generate mipmaps on DDS export.

**Requirement:** Bethesda games expect mipmaps - missing them causes performance issues.

### Normal Maps

**Purpose:** Store surface detail without additional geometry.

**Format:** DDS (usually DXT5)

**Channels:**
- **R:** X normal component
- **G:** Y normal component  
- **B:** Z normal component (up) — omitted entirely in BC5 (reconstructed in-shader)
- **A:** (varies by use)

**Tangent space:** Normals relative to surface, not world.

**Color interpretation:**
- Purple/blue = flat surface (normal pointing straight out)
- Red/green variations = surface bumps/indentations

**Compression:**
- **Skyrim LE/SE:** DXT5 (good quality for normals).
- **`[FO4]` Fallout 4:** BC5 (two-channel, blue reconstructed in-shader — see [BC5](#bc5-skyrim-se-fallout-4)). Higher-precision than DXT5 and the FO4 default for `_n` maps.

**Baking:** Generate from high-poly mesh to low-poly mesh + normal map.

### Texture Sizes

**Power of 2:** Width and height should be powers of 2 (512, 1024, 2048, 4096).

**Non-power-of-2:** Game supports NPOT, but mipmaps may not generate correctly.

**Aspect ratio:** Don't need to be square (1024x2048 is fine).

**Recommended sizes:**
- **Armor/clothing:** 2048x2048 (diffuse), 2048x2048 (normal)
- **Weapons:** 2048x2048 or 1024x2048
- **Hair:** 512x512 or 1024x1024
- **Clutter:** 512x512 or 256x256
- **Landscape:** 2048x2048 or 4096x4096 (repeating tiles)

**Performance:** Larger textures = more VRAM usage. Balance quality vs. performance.

### Texture Paths

**Relative to Data folder:**
```
Data/textures/actors/character/male/malebody_d.dds
             └─────────┬────────────────────────────┘
                    Relative path
```

**In NIF/BGSM:** Store relative path without `Data/` prefix and without `.dds` extension (auto-appended).

**Example:**
```
NIF texture path: textures\actors\character\male\malebody
Actual file: Data\textures\actors\character\male\malebody_d.dds
```

**Suffixes (convention):**
- `_d.dds` - Diffuse (base color)
- `_n.dds` - Normal map
- `_s.dds` - Specular map (SE)
- `_g.dds` - Glow map (emissive)
- `_p.dds` - Parallax/height map
- `_e.dds` - Environment map (cubemap)
- `_sk.dds` - Skin tint
- `_b.dds` - Backlight (subsurface)

**Note:** Suffixes are convention only - actual slot determined by shader assignment.

## Materials (Skyrim)

### BSLightingShaderProperty

Skyrim embeds material properties in NIF files.

**Location:** Attached to BSTriShape/NiTriShape in NIF.

**Properties:**

#### Shader Type
Determines rendering mode:
- **0:** Default lighting
- **1:** Environment map
- **5:** Skin tint
- **6:** Hair
- **7:** Parallax
- **11:** Multitexture landscape
- **14:** Eye environment map

#### Shader Flags

**SLSF1 (Set 1):**
- `SLSF1_Specular` (0x00000001) - Enable specular lighting
- `SLSF1_Skinned` (0x00000002) - Mesh is skinned to bones
- `SLSF1_Temp_Refraction` (0x00000004) - Refraction effect
- `SLSF1_Vertex_Alpha` (0x00000008) - Use vertex alpha for transparency
- `SLSF1_Greyscale_To_PaletteColor` (0x00000010) - Tint grayscale texture
- `SLSF1_Greyscale_To_PaletteAlpha` (0x00000020) - Control alpha via palette
- `SLSF1_Use_Falloff` (0x00000040) - Fresnel falloff
- `SLSF1_Environment_Mapping` (0x00000080) - Cubemap reflections
- `SLSF1_Recieve_Shadows` (0x00000100) - Receive cast shadows
- `SLSF1_Cast_Shadows` (0x00000200) - Cast shadows
- `SLSF1_Facegen_Detail_Map` (0x00000400) - FaceGen tint
- `SLSF1_Parallax` (0x00000800) - Parallax/height mapping
- `SLSF1_Model_Space_Normals` (0x00001000) - Model-space normals (not tangent)
- `SLSF1_Non_Projective_Shadows` (0x00002000) - Shadow technique
- `SLSF1_Landscape` (0x00004000) - Landscape multitexture
- `SLSF1_Refraction` (0x00008000) - Refraction effect
- `SLSF1_Fire_Refraction` (0x00010000) - Fire effect
- `SLSF1_Eye_Environment_Mapping` (0x00020000) - Eye cubemap
- `SLSF1_Hair_Soft_Lighting` (0x00040000) - Hair-specific lighting
- `SLSF1_Screendoor_Alpha_Fade` (0x00080000) - Dithered alpha fade
- `SLSF1_Localmap_Hide_Secret` (0x00100000) - Hide on local map
- `SLSF1_FaceGen_RGB_Tint` (0x00200000) - Face tint
- `SLSF1_Own_Emit` (0x00400000) - Self-illumination
- `SLSF1_Projected_UV` (0x00800000) - Projected UVs
- `SLSF1_Multiple_Textures` (0x01000000) - Landscape multi-texture
- `SLSF1_Remappable_Textures` (0x02000000) - Texture index remapping
- `SLSF1_Decal` (0x04000000) - Decal rendering
- `SLSF1_Dynamic_Decal` (0x08000000) - Dynamic decal
- `SLSF1_Parallax_Occlusion` (0x10000000) - Parallax occlusion mapping
- `SLSF1_External_Emittance` (0x20000000) - External light
- `SLSF1_Soft_Effect` (0x40000000) - Soft particle effect
- `SLSF1_ZBuffer_Test` (0x80000000) - Z-buffer testing

**SLSF2 (Set 2):**
- `SLSF2_ZBuffer_Write` (0x00000001) - Write to Z-buffer
- `SLSF2_LOD_Landscape` (0x00000002) - LOD landscape
- `SLSF2_LOD_Objects` (0x00000004) - LOD object
- `SLSF2_No_Fade` (0x00000008) - Disable distance fade
- `SLSF2_Double_Sided` (0x00000010) - Render both sides of faces
- `SLSF2_Vertex_Colors` (0x00000020) - Use vertex colors
- `SLSF2_Glow_Map` (0x00000040) - Has glow map
- `SLSF2_Assume_Shadowmask` (0x00000080) - Shadow optimization
- `SLSF2_Packed_Tangent` (0x00000100) - Tangent format
- `SLSF2_Multi_Index_Snow` (0x00000200) - Snow shader
- `SLSF2_Vertex_Lighting` (0x00000400) - Use vertex lighting
- `SLSF2_Uniform_Scale` (0x00000800) - Uniform scale optimization
- `SLSF2_Fit_Slope` (0x00001000) - Fit to slope
- `SLSF2_Billboard` (0x00002000) - Billboard sprite
- `SLSF2_No_LOD_Land_Blend` (0x00004000) - Disable LOD blending
- `SLSF2_EnvMap_Light_Fade` (0x00008000) - Env map fades with light
- `SLSF2_Wireframe` (0x00010000) - Wireframe rendering
- `SLSF2_Weapon_Blood` (0x00020000) - Weapon blood decal
- `SLSF2_Hide_On_Local_Map` (0x00040000) - Hide on local map
- `SLSF2_Premult_Alpha` (0x00080000) - Premultiplied alpha
- `SLSF2_Cloud_LOD` (0x00100000) - Cloud LOD
- `SLSF2_Anisotropic_Lighting` (0x00200000) - Anisotropic lighting (hair)
- `SLSF2_No_Transparency_Multisampling` (0x00400000) - MSAA control
- `SLSF2_Unused01` (0x00800000)
- `SLSF2_Multi_Layer_Parallax` (0x01000000) - Multi-layer parallax
- `SLSF2_Soft_Lighting` (0x02000000) - Soft lighting
- `SLSF2_Rim_Lighting` (0x04000000) - Rim lighting
- `SLSF2_Back_Lighting` (0x08000000) - Backlight/subsurface
- `SLSF2_Unused02` (0x10000000)
- `SLSF2_Tree_Anim` (0x20000000) - Tree wind animation
- `SLSF2_Effect_Lighting` (0x40000000) - Effect lighting
- `SLSF2_HD_LOD_Objects` (0x80000000) - HD LOD

See [Shader Flags Reference](../reference/shader-flags.md) [TBD] for detailed descriptions.

#### Colors

- **Specular Color:** RGB (shininess tint)
- **Emissive Color:** RGB (self-illumination)
- **Emissive Multiplier:** Float (glow brightness)

#### Glossiness

- Float (0.0-1.0+) - Higher = shinier surface

#### Alpha

- Float (0.0-1.0) - Material transparency (if alpha enabled)

#### UV Offset/Scale

- U Offset, V Offset - Shift texture coordinates
- U Scale, V Scale - Tile texture

### BSShaderTextureSet

**Contains texture paths** (up to 10 slots):

**Skyrim LE/SE:**
```
[0] Diffuse         - Base color texture
[1] Normal          - Normal map
[2] Glow            - Emissive map
[3] Parallax        - Height map
[4] Cubemap         - Environment map
[5] Environment Mask- Controls cubemap strength
[6] Tint/Detail     - Skin tint or detail map
[7] Backlight       - Subsurface scattering map
[8] Specular (SE)   - Specular map (SE only)
[9] Lighting (SE)   - (SE only, rarely used)
```

**Path format:**
```
textures\actors\character\male\malebody
```
- Relative to Data/
- No extension (`.dds` auto-appended)
- Backslashes or forward slashes both work

### BSEffectShaderProperty

**For special effects** (glows, magic).

**Properties:**
- Base texture
- Grayscale texture (modulated by color)
- Emissive color and multiplier
- Falloff (Fresnel effect)
- Soft depth (soft particles)

**Use cases:**
- Magic effects
- Fire, water, energy
- UI elements
- Glowing objects

## Materials (Fallout 4)

### BGSM Files

**Fallout 4 materials are external files** instead of embedded in NIF.

**Extension:** `.bgsm` (material)  
**Format:** JSON-like text format  
**Location:** `Data/Materials/`

**Structure:**
```json
{
    "Version": 2,
    "DiffuseTexture": "Textures\\Actors\\Character\\BaseHumanMale\\BaseHumanMale_d.dds",
    "NormalTexture": "Textures\\Actors\\Character\\BaseHumanMale\\BaseHumanMale_n.dds",
    "SpecularTexture": "Textures\\Actors\\Character\\BaseHumanMale\\BaseHumanMale_s.dds",
    "Tiling": {
        "U": 1.0,
        "V": 1.0
    },
    "Offset": {
        "U": 0.0,
        "V": 0.0
    },
    "bTileU": true,
    "bTileV": true,
    "fAlpha": 1.0,
    "bAlphaBlend": false,
    "bAlphaTest": false,
    "iAlphaTestRef": 127,
    "bZBufferWrite": true,
    "bZBufferTest": true,
    "bScreenSpaceReflections": false,
    "bWetnessControl_ScreenSpaceReflections": false,
    "bDecal": false,
    "bTwoSided": false,
    "bDecalNoFade": false,
    "bNonOccluder": false,
    "bRefraction": false,
    "bRefractionFalloff": false,
    "fRefractionPower": 0.0,
    "bEnvironmentMapping": false,
    "fEnvironmentMappingMaskScale": 1.0,
    "bGrayscaleToPaletteColor": false,
    "Shader": "Lighting",
    "SourceTextureFolder": ""
}
```

**Key properties:**

#### Textures
- `DiffuseTexture` - Base color
- `NormalTexture` - Normal map
- `SpecularTexture` - Specular/glossiness
- `GlowTexture` - Emissive
- `GreyscaleTexture` - For tinting
- `EnvmapTexture` - Environment/cubemap
- `SmoothSpecTexture` - Specular smoothness

#### Flags
- `bAlphaBlend` - Smooth transparency
- `bAlphaTest` - Hard cutout transparency
- `iAlphaTestRef` - Threshold for alpha test (0-255)
- `bTwoSided` - Render both sides
- `bDecal` - Decal rendering
- `bEnvironmentMapping` - Cubemap reflections
- `bGrayscaleToPaletteColor` - Tint grayscale texture
- `bScreenSpaceReflections` - SSR

#### Values
- `fAlpha` - Material alpha (0.0-1.0)
- `fSpecular` - Specularity strength
- `fGlossiness` - Shininess
- `fEmittanceMultiplier` - Glow brightness

**Shader types:**
- `Lighting` - Standard PBR shader
- `Effect` - Special effects (see BGEM)

**Vertex format control:**
- Vertex colors: Determined by vertex data in NIF (not a BGSM flag)
- Vertex alpha: Used if `bAlphaBlend` true and vertex has alpha channel

### BGEM Files

**Effect materials** for special effects.

**Extension:** `.bgem`  
**Format:** Similar to BGSM

**Use cases:**
- Blood decals
- Magic effects
- Water surfaces
- Fire, smoke

**Key differences from BGSM:**
- `Shader: "Effect"`
- Additive/multiply blend modes
- Soft particle depth
- Falloff controls

### In NIF (FO4)

**BSLightingShaderProperty name field** references BGSM/BGEM path.

**Example:**
```
BSLightingShaderProperty
  Name: "Materials\\Actors\\Character\\BaseHumanMale.bgsm"
```

**Path:** Relative to Data/, with extension.

**Shader setup:**
1. NIF has BSLightingShaderProperty
2. Name field = BGSM path
3. BGSM has texture paths
4. Game loads textures and applies material

**Advantage:** Editing BGSM updates all meshes that reference it (no NIF editing).

## Creating Textures

### Photoshop / GIMP

**Export DDS:**
1. Create/edit texture (RGBA, power-of-2 size)
2. **Save as DDS** (requires plugin)
   - Photoshop: NVIDIA DDS plugin
   - GIMP: Built-in DDS support
3. **Choose compression:**
   - DXT1 (opaque)
   - DXT5 (alpha or normals)
   - BC7 (SE/FO4 high quality)
4. **Enable mipmaps:** Check "Generate Mipmaps"

### Paint.NET

**Built-in DDS support** (easier than Photoshop).

**Workflow:** File → Save As → DDS file type → Choose compression.

### Substance Painter / Designer

**PBR workflow** for game assets.

**Export preset:** Fallout 4 / Skyrim SE

**Outputs:**
- Base Color → `_d.dds`
- Normal → `_n.dds`
- Roughness/Metallic → `_s.dds` (packed channels)

### Baking Normal Maps

**Blender:**
1. High-poly model (detailed sculpt)
2. Low-poly model (game mesh)
3. **Bake:** Select low-poly, then high-poly (Shift+click), Render → Bake → Normal
4. **Export normal as DDS**

**Result:** Low-poly mesh with high-poly detail in normal map.

## Common Issues

### Purple Textures (Missing Textures)
- **Wrong path:** Check MODL/BGSM texture paths
- **File doesn't exist:** Texture not installed
- **Wrong extension:** `.dds` missing or wrong
- **Fix:** Verify texture path, ensure file exists, check Data folder

### Textures Too Dark/Bright
- **Wrong color space:** sRGB vs. linear
- **Lighting:** In-game lighting affects appearance
- **Specular:** Too high glossiness washes out color
- **Fix:** Adjust diffuse brightness, tweak specular/glossiness

### Normal Map Not Working
- **Wrong compression:** Use DXT5 for normals
- **Wrong format:** R/G/B channel swapped (OpenGL vs. DirectX)
- **Not assigned:** Normal texture slot empty
- **Tangent/bitangent missing:** Mesh needs tangent data
- **Fix:** Re-export with DXT5, check format, verify slot, recalculate tangents

### Textures Look Blocky
- **No mipmaps:** DDS exported without mipmaps
- **Too low resolution:** Texture size too small
- **Fix:** Re-export with mipmaps, increase texture size

### Transparency Not Working
- **Alpha blend/test not enabled:** SLSF1_Vertex_Alpha or bAlphaBlend flag
- **Wrong compression:** Use DXT5 (alpha support)
- **Vertex alpha wrong:** Mesh vertex alpha all white
- **Fix:** Enable alpha flag, use DXT5, check vertex alpha in mesh

### Seams Visible
- **UV seam mismatch:** Vertices split at UV boundaries
- **Bleeding:** Mipmaps blend across seams
- **Padding:** Need UV padding on texture
- **Fix:** Weld UVs where possible, add texture padding, use higher resolution

## Tools

**Photoshop + NVIDIA DDS Plugin:** Industry standard

**GIMP:** Free, built-in DDS

**Paint.NET:** Easy DDS workflow (Windows only)

**Substance Painter/Designer:** PBR texturing

**NifSkope:** View/edit material properties in NIFs

`[FO4]` **Material Editor:** Creation Kit tool for BGSM editing

**PyNifly:** Edit shader properties via Python

```python
from io_scene_nifly import pynifly

nif = pynifly.NifFile('armor.nif')
shape = nif.shapes[0]

# Get shader property
shader = shape.shader

# Set textures
shader.textures[0] = 'textures\\armor\\myarmor_d'
shader.textures[1] = 'textures\\armor\\myarmor_n'

# Set flags
shader.Shader_Flags_1 |= 0x00000001  # SLSF1_Specular
shader.Shader_Flags_2 |= 0x00000020  # SLSF2_Vertex_Colors

# Set colors
shader.Specular_Color = (1.0, 1.0, 1.0)
shader.Glossiness = 50.0

nif.save('armor_updated.nif')
```

## See Also

- [NIF Files](nif-files.md) - BSLightingShaderProperty, BSShaderTextureSet
- [Shader Flags Reference](../reference/shader-flags.md) [TBD] - Complete flag list and descriptions
- [Texture Workflows](../workflows/textures-materials.md) [TBD] - Creating and applying textures
- [Mesh Issues Debugging](../debugging/mesh-issues.md) [TBD] - Texture troubleshooting
