# Starfield Materials & Textures

Starfield replaced Fallout 4's flat `BGSM`/`BGEM` text materials with a **layered, graph-based
material system**. Instead of one file listing a handful of texture slots and boolean flags, a
Starfield material is a small **object graph** (a set of nodes and edges) describing 1–6 stacked
material *layers*, the *blenders* between them, per-layer *texture sets*, and attached *component*
settings (alpha, translucency/SSS, hair, decal, emissive, etc.). This graph is authored as JSON in
a `.mat` file and compiled into a global binary **material database** (`.cdb`).

This page targets modders coming from `[FO4]`/`[Skyrim]` who need to author skin/fur materials and
get textures rendering correctly in Blender and in-game.

---

## 1. Architecture at a glance

```
BSGeometry (mesh)
  └─ BSLightingShaderProperty
        └─ Name = "Materials\Path\MyMaterial.mat"   ← material reference (relative to Data\, WITH .mat)
                     │
                     ▼
   .mat  (JSON object graph)  ──compiled into──▶  materialsbeta.cdb  (binary database)
     ├─ LayeredMaterial (root)
     │    ├─ Layer1 ─ Material ─ TextureSet ─▶ *.dds files
     │    ├─ Blender1
     │    ├─ Layer2 ─ Material ─ TextureSet ─▶ *.dds files
     │    └─ … up to Layer6
     └─ Components: AlphaSettings, TranslucencySettings, HairSettings, DecalSettings, …
```

Key ideas:

- **The mesh references a material by path**, exactly like `[FO4]`: the NIF's
  `BSLightingShaderProperty.Name` holds `Materials\...\Foo.mat` (relative to `Data\`, backslashes,
  **including** the `.mat` extension). In `[FO4]` this pointed at a `.bgsm`; in Starfield it points
  at a `.mat`. Everything else about the material lives in the `.mat`/`.cdb`, not the NIF.
- **Layers stack.** Each layer is a full PBR material (its own albedo/normal/roughness/etc.). Layers
  above are composited onto layers below through a **Blender** node using a mask, vertex color, or
  height. This is how one mesh gets, e.g., base skin + a dirt layer + a tattoo layer.
- **A material database, not a folder of files.** At load time the game reads
  `materialsbeta.cdb` (shipped inside `Data\Starfield - Materials.ba2`). It contains the compiled
  graphs for *every* vanilla material plus precomputed path hashes. A **loose `.mat`** in
  `Data\Materials\…` overrides/extends the database entry with the matching path. Its on-disk binary
  layout — and the v4 change that breaks older readers — is documented in
  [The `.cdb` binary format](starfield-cdb-format.md).

**A loose `.mat` is sufficient — you never need to write the `.cdb`** (verified against fo76utils
NifSkope, nifly, and Outfit Studio source). The game/CK load loose JSON `.mat` files at runtime, and
NifSkope's material export (`sfmatexport.cpp`) serializes a `CE2Material` straight to a **loose JSON
`.mat`** (minting fresh resource IDs) — there is **no `.cdb` writer anywhere** in these codebases
(the `.cdb` parsers are strictly read-only). So authoring a custom skin/fur material means emitting a
loose `.mat`; the compiled database is only ever *read*, to resolve vanilla materials by path hash.
Each loose node carries its own resource IDs and `Parent` links into the shared root templates.
(The exact loose-vs-`.cdb` *precedence* rule — full replace vs merge — is still undocumented, but
doesn't block authoring: a complete loose graph works.)

### Where things live (all paths relative to `Data\`)

| What | Location |
|---|---|
| Compiled material DB | `Data\Starfield - Materials.ba2` → `materials\materialsbeta.cdb` |
| Loose material overrides | `Data\Materials\<subfolders>\<name>.mat` |
| Shader-model templates (loose, shipped) | `Data\EditorFiles\RuleTemplates\ShaderModels\*.json` |
| Root/base material graphs referenced by `Parent` | `Data\Materials\Layered\Root\*.mat` (e.g. `LayeredMaterials.mat`, `Layers.mat`, `Materials.mat`, `TextureSets.mat`, `UVStreams.mat`) — inside the Materials `.ba2` |
| Textures | `Data\Textures\<subfolders>\*.dds` |

**Note:** BA2 archives do **not** contain loose `.mat` files — only the compiled `.cdb`. Ready-to-edit
loose `.mat` files are distributed separately (Bethesda's `Tools\ContentResources.zip`, or extracted
by community tools such as the fo76utils NifSkope fork / SFME / Gibbed.Starfield).

---

## 2. The `.mat` JSON format (worked example)

A `.mat` is a JSON document with a top-level `Filename`, an optional `Import` list (referenced
external resources by hash), and an `Objects` array. Each object is a graph node with:

- `Components` — the typed data payloads (name, IDs, texture files, colors, floats, settings blocks).
- `Edges` — links to other nodes (`BSComponentDB2::OuterEdge`, with a `To` target and `EdgeIndex`).
- `ID` — a resource id `res:AAAAAAAA:BBBBBBBB:CCCCCCCC` (three 32-bit hashes).
- `Parent` — the template/root graph this node derives from (e.g. `…\Root\Layers.mat`).

Every typed payload is `{ "Data": {...}, "Index": n, "Type": "BSMaterial::Xxx" }`. The `Index`
disambiguates repeated components (e.g. texture slot index within a set).

> For a **complete, line-by-line annotated real material** — a shipped 2-layer skin with SSS,
> a blend mask, and a tiled detail-normal layer — see
> [**the `.mat` worked example**](starfield-material-worked-example.md).

### Real skeleton (abridged from a shipped material)

```jsonc
{
  "Filename": "MATERIALS\\SetDressing\\VaultBoyBobbleheads\\VaultBoy.mat",
  "Import": [ "res:03F7ADED:0846A6FF:0074616D" ],
  "Objects": [
    {                                             // ── root layered-material node
      "Components": [
        { "Data": { "Name": "VaultBoy" }, "Index": 0, "Type": "BSComponentDB::CTName" },
        { "Data": { "ID": "res:B5EBFC45:000639FF:A4D136CD" }, "Index": 0, "Type": "BSMaterial::LayerID" },
        { "Data": { "ID": "res:FEED12D6:0005DAFE:A64340C8" }, "Index": 0, "Type": "BSMaterial::LODMaterialID" }
      ],
      "Parent": "Data\\Materials\\Layered\\Root\\LayeredMaterials.mat"
    },
    {                                             // ── Layer1: references a Material + a UV stream
      "Components": [
        { "Data": { "Name": "VaultBoy_Layer1" }, "Index": 0, "Type": "BSComponentDB::CTName" },
        { "Data": { "ID": "res:B5EBFC49:000639FF:A4D136CD" }, "Index": 0, "Type": "BSMaterial::MaterialID" },
        { "Data": { "ID": "res:B5EBFC48:000639FF:A4D136CD" }, "Index": 0, "Type": "BSMaterial::UVStreamID" }
      ],
      "Edges": [ { "EdgeIndex": 0, "To": "<this>", "Type": "BSComponentDB2::OuterEdge" } ],
      "ID": "res:B5EBFC45:000639FF:A4D136CD",
      "Parent": "Data\\Materials\\Layered\\Root\\Layers.mat"
    },
    {                                             // ── Material1: points at a TextureSet
      "Components": [
        { "Data": { "Name": "VaultBoy_Material1" }, "Index": 0, "Type": "BSComponentDB::CTName" },
        { "Data": { "ID": "res:D46A0E9F:000639FF:A4D136CD" }, "Index": 0, "Type": "BSMaterial::TextureSetID", "Version": 3 }
      ],
      "Edges": [ { "EdgeIndex": 0, "To": "res:B5EBFC45:000639FF:A4D136CD", "Type": "BSComponentDB2::OuterEdge" } ],
      "ID": "res:B5EBFC49:000639FF:A4D136CD",
      "Parent": "Data\\Materials\\Layered\\Root\\Materials.mat"
    },
    {                                             // ── TextureSet: the actual DDS slots
      "Components": [
        { "Data": { "Name": "VaultBoy_TextureSet2" }, "Index": 0, "Type": "BSComponentDB::CTName" },
        { "Data": { "ResolutionHint": "Tiling" }, "Index": 0, "Type": "BSMaterial::TextureResolutionSetting" },
        { "Data": { "DisableMipBiasHint": "false" }, "Index": 0, "Type": "BSMaterial::MipBiasSetting" },
        { "Data": { "Value": "MetalRough" }, "Index": 0, "Type": "BSMaterial::TextureSetKindComponent" },

        { "Data": { "FileName": "Data\\Textures\\...\\VaultBoy_d.DDS" },  "Index": 0, "Type": "BSMaterial::MRTextureFile", "Version": 2 },  // albedo
        { "Data": { "FileName": "Data\\Textures\\...\\VaultBoy_n.DDS" },  "Index": 1, "Type": "BSMaterial::MRTextureFile", "Version": 2 },  // normal
        { "Data": { "FileName": "" },                                    "Index": 2, "Type": "BSMaterial::MRTextureFile", "Version": 2 },  // opacity (empty)
        { "Data": { "FileName": "Data\\Textures\\...\\VaultBoy_s.DDS" },  "Index": 3, "Type": "BSMaterial::MRTextureFile", "Version": 2 },  // roughness
        // … indices 4–20 (mostly empty in this simple material)

        // Optional per-slot override tint when a texture is absent:
        { "Data": { "Enabled": "false",
                    "Color": { "Data": { "Value": { "Data": { "x":"0.5","y":"0.5","z":"1","w":"1" },
                                                    "Type": "XMFLOAT4" } },
                               "Type": "BSMaterial::Color", "Version": 1 } },
          "Index": 1, "Type": "BSMaterial::TextureReplacement" },

        { "Data": { "Value": 1.0 }, "Index": 0, "Type": "BSMaterial::MaterialParamFloat" }
      ],
      "Edges": [ { "EdgeIndex": 0, "To": "res:B5EBFC49:000639FF:A4D136CD", "Type": "BSComponentDB2::OuterEdge" } ],
      "ID": "res:D46A0E9F:000639FF:A4D136CD"
    }
  ]
}
```

Notes:
- `TextureReplacement` supplies a **flat fallback color** (an `XMFLOAT4` RGBA) used when a slot's
  `FileName` is empty, with `Enabled` toggling it. The `{0.5,0.5,1,1}` value above is the classic
  flat-normal default.
- `TextureSetKindComponent = "MetalRough"` declares the PBR convention (metal/rough workflow).
- The example above uses legacy `_d/_n/_s` suffixes (a ported asset). Native Starfield assets use
  the `_color/_normal/_rough/_metal/_ao/_opacity` suffixes — see §5.
- Resource IDs (`res:…`) must be unique; when tools clone a material they randomly regenerate these
  to avoid database collisions.

---

## 3. Shader models (material templates)

The material's *shape* (which layers, which slots, which component blocks are present) is chosen from
a **shader model / rule template**. Bethesda ships these loose as JSON in
`Data\EditorFiles\RuleTemplates\ShaderModels\`. Each template is a list of `TemplateRules` that
`Add`/`Remove`/`Move`/`MakeConst` nodes on the base `BSMaterial::LayeredMaterialID`, i.e. it prunes the
full DOM down to just the slots a given shader uses. Reading them is the fastest way to learn the DOM.

Selected models (the `DisplayName` is what the Creation Kit / NifSkope shows):

| Template file | DisplayName | Notes |
|---|---|---|
| `BaseMaterial.json` | *(locked base)* | Root DOM every model derives from |
| `1LayerStandard.json` | `Standard1Layer` | Most opaque props; 1 layer |
| `TwoSided1Layer.json` | `StandardTwoSided1Layer` | Double-sided |
| `2LayerStandard.json` / `3LayerStandard.json` / `4LayerStandard.json` | `Standard2/3/4Layer` | Multi-layer blends |
| `ColorEmissive.json` | `ColorEmissive` | Flat color + emissive |
| `*Effect*.json`, `TranslucentThin1Layer.json`, `Water*.json` | — | `[FO4]`-`BGEM`-equivalent effect/translucent shaders |
| **`BodySkin1Layer.json`** | `BodySkin1Layer` | Body skin, SSS via TranslucencySettings |
| **`Skin5Layer.json`** | `CharacterSkin5Layer` | Face/character skin, up to 6 blended layers |
| **`Character2/3/4Layer.json`** | — | Layered character skin variants |
| **`Hair1Layer.json`** | `CharacterHair1Layer` | Anisotropic hair (`HairSettings`) |
| `Eye1Layer.json`, `EyeWetness1Layer.json`, `1LayerEyebrow.json`, `1LayerMouth.json` | — | Face parts |

`MetaData.ComplexityCost` gauges shader expense; `DisableLOD` / `Locked` are authoring hints.

**Implication for a custom furry race:** the skin path should start from `Skin5Layer` /
`BodySkin1Layer` (SSS + multi-layer) and hair/fur from `Hair1Layer` (anisotropic + backscatter).
Fur that is *painted into skin* can be a blend layer; fur that is *card/shell geometry* is a separate
`Hair1Layer` material.

---

## 4. Layers, blenders, and component blocks

### Layer / Blender DOM (paths as seen in the templates)

```
LayeredMaterial
├─ Layer1 / Layer2 / … / Layer6
│    └─ Material
│         ├─ UseVertexColorAsTint, Color Tint, Override Color Blend Type, FlipBookComp
│         └─ TextureSet
│              └─ (slots — see §5)
├─ Blender1 … Blender5          (Blender_N sits "above" Layer_(N+1))
│    ├─ BlendMode               (e.g. Linear, Additive, PositionContrast, Skin)
│    ├─ UseVertexColor, VertexColorChannel
│    ├─ Blend Albedo / Blend Metal / Blend Roughness / Blend Ambient Occlusion
│    ├─ BlendTextureNormal, Blend Normals additively
│    └─ UseDetailBlendMask
├─ AlphaSettings ─ Blender ─ { Mode, VertexColorChannel, UseDetailBlendMask }, AlphaBlendEnabled
├─ DetailBlenderSettings ─ { IsDetailBlendMaskSupported, … }
├─ TranslucencySettings  (skin/SSS)   — see below
├─ HairSettings          (hair/fur)   — see below
├─ DecalSettings         (decals/parallax)
├─ EffectSettings        (BGEM-style effects: falloff, backlight, frosting)
├─ TerrainTintSettings, MaterialNoiseComponent, CollisionSettings, DissolveComponent
```

Blenders expose **per-channel blend toggles** (blend albedo/metal/roughness/AO/normal
independently) plus a mask source (detail-blend mask, vertex-color channel, or height). The **Blender
blend-mode enum** is (fo76utils `material.hpp`): `0 Linear, 1 Additive, 2 PositionContrast, 3 None,
4 CharacterCombine, 5 Skin`. Note Starfield has **several distinct blend enums** — don't conflate
them: `Material.alphaBlendMode` (Linear/Additive/PositionContrast/None), `EffectSettings.blendMode`
(8 values: AlphaBlend/Additive/…/None), the Opacity/LayeredEmissive modes
(Lerp/Additive/Subtractive/Multiplicative), and `DecalSettings.blendMode` (None/Additive). NifSkope's
renderer supports up to **6** layers.

### Fur/skin-critical component fields

`TranslucencySettings` (subsurface scattering — the core of believable skin/fur):
`isEnabled, isThin, flipBackFaceNormalsInVS, useSSS, sssWidth, sssStrength, transmissiveScale,
transmittanceWidth, specLobe0RoughnessScale, specLobe1RoughnessScale, sourceLayer`.
(The skin templates rename these to friendly labels: *Subsurface Scattering Width/Strength*, *Scale*,
*Transmittance Width*, *SpecLobe 1/2 Roughness Scale*, *Transmittance Source Layer*.)

`HairSettings` (anisotropic strand/fur shading):
`isEnabled, isSpikyHair, depthOffsetMaskVertexColorChannel, aoVertexColorChannel, specScale,
specularTransmissionScale, directTransmissionScale, diffuseTransmissionScale, roughness,
contactShadowSoftening, backscatterStrength, backscatterWrap, variationStrength,
indirectSpecularScale, indirectSpecularTransmissionScale, indirectSpecRoughness, edgeMaskContrast,
edgeMaskMin, edgeMaskDistanceMin/Max, ditherScale, ditherDistanceMin/Max, tangent, maxDepthOffset`.

`EffectSettings` (the `[FO4]` `BGEM` analogue):
`flags, blendMode, falloffStart/StopAngle, falloffStart/StopOpacity, alphaThreshold,
softFalloffDepth, frostingBgndBlend, frostingBlurBias, materialAlpha, backlightScale,
backlightSharpness, backlightTransparency, backlightTintColor, depthBias`.

!!! tip "CK gotcha: effect materials invisible above opaque surfaces"
    An animated/effect (`EffectSettings`) material can render correctly in NifSkope yet
    turn **invisible in-game whenever it is drawn on top of an opaque material** — while
    looking fine anywhere it is *not* over opaque geometry. Two toggles in the CK Material
    Editor → **Effect Settings** control this (they map to `EffectSettings` flags):

    - **Soft Effect → disable it.** With Soft Effect *enabled* (any value) the effect
      vanishes over opaque surfaces; *disabled*, it draws correctly on top of them. **This
      is the key fix.**
    - **ZTest → enable it** so the effect is properly occluded by opaque geometry
      (depth-tested). With ZTest *disabled* the effect renders *through* occluding opaque
      surfaces (always-on-top).

    So **Soft Effect off + ZTest on** = visible above opaque *and* correctly occluded.
    Blend mode, the normal map, `Render before IOT`, and `Is Glass` were all found not to
    affect this (some combinations can even CTD the CK). Community finding — the CK ships
    no help text for these parameters.

### Component representation in the `.mat`/cdb (authoring names)

The field names above are the **runtime** (CommonLibSF) names. The names actually stored in a loose
`.mat` / the `materialsbeta.cdb` are **PascalCase**, and translucency is wrapped in a
component-plus-`Settings` envelope. A cdb/`.mat` reader (fo76utils `sfmatexport`, PyNifly) sees these
class field sets (verified against the cdb class registry):

- **`TranslucencySettingsComponent`** = `Enabled` + a nested `Settings` →
  **`TranslucencySettings`** = `Thin, FlipBackFaceNormalsInViewSpace, UseSSS, SSSWidth, SSSStrength,
  TransmissiveScale, TransmittanceWidth, SpecLobe0RoughnessScale, SpecLobe1RoughnessScale,
  TransmittanceSourceLayer`. `Enabled` and `UseSSS` are **two separate gates** — the component can be
  on with SSS off (thin translucency vs subsurface). `SpecLobe0/1RoughnessScale` are the skin
  **dual-specular-lobe** roughness multipliers (sharp + soft highlight), not scatter depth.
- **`HairSettingsComponent`** = fields directly: `Enabled, IsSpikyHair, SpecScale,
  SpecularTransmissionScale, DirectTransmissionScale, DiffuseTransmissionScale, Roughness,
  ContactShadowSoftening, BackscatterStrength, BackscatterWrap, VariationStrength,
  IndirectSpecularScale, IndirectSpecularTransmissionScale, IndirectSpecRoughness, EdgeMaskContrast,
  EdgeMaskMin, EdgeMaskDistanceMin/Max, MaxDepthOffset, DitherScale, DitherDistanceMin/Max,
  Tangent (XMFLOAT3), TangentBend, DepthOffsetMaskVertexColorChannel, AOVertexColorChannel`.
- **`AlphaSettingsComponent`** = `HasOpacity, AlphaTestThreshold, OpacitySourceLayer, Blender
  (→ AlphaBlenderSettings), UseDitheredTransparency`. Surface alpha is a **test/clip** at
  `AlphaTestThreshold` — there is no none/test/blend enum; `UseDitheredTransparency` selects dithered
  coverage (hair) vs straight blend. The nested `Blender` (`AlphaBlenderSettings` = `Mode,
  UseDetailBlendMask, UseVertexColor, VertexColorChannel, OpacityUVStream, HeightBlendThreshold,
  HeightBlendFactor, Position, Contrast`) governs **layer** alpha-blend, distinct from surface alpha.
- **`LayeredEmissivityComponent`** = up to three layers + two blenders + adaptive emittance:
  `Enabled, FirstLayerIndex, FirstLayerTint, FirstLayerMaskIndex, SecondLayerActive/Index/Tint/…,
  FirstBlenderIndex, FirstBlenderMode, ThirdLayer…, SecondBlender…, EmissiveClipThreshold,
  AdaptiveEmittance, LuminousEmittance, ExposureOffset, EnableAdaptiveLimits, Max/MinOffsetEmittance,
  IgnoresFog`.
- **`ShaderModelComponent`** = `FileName` (the template name, e.g. `BodySkin2Layer`, `Hair1Layer`).

Two reader gotchas:

- **Only *changed* fields are stored.** The cdb keeps per-object diffs against the template default,
  so a shipped material lists only the fields it overrode — a skin `TranslucencySettings` may carry
  just `UseSSS` + the two `SpecLobe*RoughnessScale`s; a hair `AlphaSettingsComponent` may carry only
  `HasOpacity`. An absent field means *template default*, not zero. To recover a field's default you
  need the shader-model template (§3) or the class definition, not the material instance.
- **Values are strings; colors are nested `XMFLOAT4`.** Every scalar/bool is a string (`"true"`,
  `"0.93"`); a color is `{ Value: { Type: "XMFLOAT4", Data: { x, y, z, w } } }`. (See the cdb-format
  page.)

**Hair carries no Normal.** A hair material typically omits slot 1 — strand shading comes from the
mesh's **geometry normals** + the anisotropic `HairSettings` model + the ID map (slot 20); the
`_zoffset` (slot 12) pairs with `MaxDepthOffset`/`DepthOffsetMaskVertexColorChannel` to sort
overlapping hair cards, not to bump the surface. Skin materials, by contrast, do ship a real slot-1
normal.

---

## 5. TextureSet slots & DDS conventions

### Slot index → map (authoritative order, per fo76utils `material.hpp`)

Each `BSMaterial::MRTextureFile` in a TextureSet carries an `Index` selecting the slot:

| Index | Map | Native suffix | DDS format | Color space |
|---:|---|---|---|---|
| 0 | Albedo / base color | `_color` (`_d`) | BC7_UNORM_SRGB (or BC1) | **sRGB** |
| 1 | Normal (tangent) | `_normal` (`_n`) | BC5_SNORM (2-ch XY) | linear |
| 2 | Opacity / alpha | `_opacity` | BC4_UNORM | linear |
| 3 | Roughness | `_rough` (`_s`*) | BC4_UNORM | linear |
| 4 | Metalness | `_metal` | BC4_UNORM | linear |
| 5 | Ambient occlusion | `_ao` | BC4_UNORM | linear |
| 6 | Height / parallax | `_height` | BC4_UNORM | linear |
| 7 | Emissive / glow | `_emissive` | BC7/BC1 SRGB | **sRGB** |
| 8 | Transmissive (translucency) | `_transmissive` | BC4_UNORM | linear |
| 9 | Curvature | `_curvature` | BC4_UNORM | linear |
| 10 | Mask | `_mask` | BC4_UNORM | linear |
| 12 | Depth/Z offset | `_zoffset` | BC4_UNORM | linear |
| 14 | Overlay color | — | BC7 | sRGB |
| 15 | Overlay roughness | — | BC4 | linear |
| 16 | Overlay metalness | — | BC4 | linear |
| 20 | HairID / id mask | `_id` | BC4/BC7 | linear |

\* The legacy `_s` in ported assets is read into the roughness slot; don't confuse with `[FO4]`'s
packed specular.

The slot table above is confirmed verbatim against fo76utils `material.hpp` (`maxTexturePaths = 21`,
indices 0–20). **Indices 11, 13, 17, 18, 19 are undefined gaps** (no map). Names like
`NormalIntensity`, `Flow`, `Frost`, `Secondary Opacity`, `ScatteringDirections/ForwardAlpha`, and
`Overlay AO` are **not texture slots** — e.g. `NormalIntensity` is a `TextureSet` **float parameter**
(scales the normal map's RG in-shader), and the others are settings-block fields, not `MRTextureFile`
paths. Don't allocate texture slots for them.

### The big shift from `[FO4]`: **one property per texture**

Starfield does **not** pack roughness+metal+AO into a single texture the way `[FO4]`'s `_s` /
Skyrim's specular did. Each scalar PBR property is its own **single-channel BC4** DDS. Rules of thumb:

- `_color`, `_emissive`, overlays → **BC7 (or BC1) `_SRGB`**.
- `_normal` → **BC5_SNORM**, storing X/Y only; Z is reconstructed in-shader (so a "flat" pixel is
  `(0.5, 0.5)` in R/G). No blue/alpha channel to rely on.
- `_rough`, `_metal`, `_ao`, `_opacity`, `_height`, `_mask`, `_transmissive`, `_curvature`,
  `_zoffset`, `_id` → **BC4_UNORM** grayscale, **linear**.
- All textures ship with mipmaps (same requirement as `[FO4]`/`[Skyrim]`).
- Texture paths in the `.mat` are stored **with** `Data\` prefix and **with** the `.DDS` extension —
  unlike NIF texture-set paths in older games, which omitted both. (Community tools accept either.)

!!! warning "Starfield normals are BC5_**SNORM** — Blender can't decode them"
    Starfield `_normal` maps use **BC5_SNORM** (signed) with a **DX10-header** DDS (`dxgiFormat` 84).
    `[FO4]` normals, by contrast, are **BC5_UNORM** with the legacy `ATI2` fourCC. Blender's DDS
    reader (through at least 5.1) handles the FO4 flavor but **not** the DX10 BC5_SNORM one — it
    loads such a file as a **0×0 image with no data**, so any in-shader Z-reconstruction runs on
    nothing and the normal renders as garbage (a tell-tale symptom is a hard seam where mirrored
    front/back UVs meet). The BC1/BC4 color/rough/ao maps load fine; only the SNORM normal fails.
    Until Blender adds BC5_SNORM support, **convert the normal to PNG** (e.g. Texture Toolbox,
    `texconv`) — a reconstructed full-RGB normal set to **Non-Color** — and use that. The block
    *layout* is identical to FO4's BC5; only the value convention (signed) and header differ.

**Fur/skin-relevant maps:** subsurface look is driven by `TranslucencySettings` (a numeric block),
not a dedicated "SSS map" — though a per-pixel mask can come via `_transmissive` (slot 8) and
`sourceLayer`. Fur "fuzz"/sheen comes from `HairSettings` backscatter params, optionally masked by an
`_id`/`_mask` texture. There is no single `[Skyrim]`-style `_sk` skin-tint slot; tinting is done with
`Color Tint` / `UseVertexColorAsTint` on a layer.

---

## 6. Mapping to a Blender shader

A faithful **import** for the common `Standard1Layer` case (Principled BSDF v2 in Blender 4.x):

| Starfield slot | Blender wiring |
|---|---|
| Albedo `_color` (sRGB) | Image (Color Space **sRGB**) → **Base Color** |
| Normal `_normal` (BC5, XY) | Image (**Non-Color**) → *reconstruct Z* → Normal Map node → **Normal** |
| Roughness `_rough` | Image (**Non-Color**) → **Roughness** |
| Metalness `_metal` | Image (**Non-Color**) → **Metallic** |
| AO `_ao` | Multiply into Base Color (or MixRGB/`AO` in a custom group) |
| Opacity `_opacity` | Image (**Non-Color**) → **Alpha**; set material blend/clip per `AlphaSettings` |
| Emissive `_emissive` (sRGB) | Image → **Emission Color**; strength from emissive params |
| Transmissive / SSS block | **Subsurface Weight/Radius** driven by `sssStrength`/`sssWidth` (approx.) |
| Hair block | Anisotropy/sheen approximation, or a dedicated hair node group |

Because `_normal` is **XY-only BC5**, the importer must **reconstruct Z**
(`z = sqrt(1 - x² - y²)`) with a small node group before the Normal Map node — a plain image → Normal
Map will read blue≈0 and give wrong lighting. Also handle the **green-channel convention**: Starfield
normals are DirectX-style (Y-down); Blender expects OpenGL (Y-up), so **invert green** on import (and
re-invert on export).

For **multi-layer** materials, no single Principled node suffices: build one Principled per layer and
composite with Mix nodes driven by each `Blender_N`'s mask/vertex-color channel, honoring the
per-channel `Blend Albedo/Metal/Roughness/AO/Normal` toggles. For a first pass, importing **Layer1
only** (plus a note) is a reasonable MVP.

### What must be authored to **export** a working Starfield material

1. A NIF whose `BSLightingShaderProperty.Name` = `Materials\<path>\<name>.mat`.
2. A `.mat` graph: root LayeredMaterial → Layer(s) → Material → TextureSet, with unique `res:` IDs
   and correct `Parent` links to the shipped `…\Root\*.mat` templates.
3. Per-layer TextureSet `MRTextureFile` entries at the correct **indices** (0=albedo, 1=normal, …).
4. Correct component blocks for the shader model chosen (e.g. `TranslucencySettings` for skin,
   `HairSettings` for fur), plus `TextureSetKindComponent = "MetalRough"`.
5. DDS files in the right formats/color spaces (§5), with mipmaps, under `Data\Textures\…`.
6. Ship the loose `.mat` — this is sufficient; **no `.cdb` compile step is needed** (the game loads
   loose JSON `.mat` at runtime).

**Practical shortcut:** rather than emit the full graph from scratch, PyNifly can **clone a shipped
template `.mat`** (regenerating `res:` IDs) and rewrite the `CTName`, `MRTextureFile` filenames, and
the numeric component fields — the approach NifSkope's "Clone and Copy to Clipboard" spell uses.

---

## 7. Contrast with `[FO4]` BGSM/BGEM (quick reference)

| Aspect | `[FO4]` BGSM/BGEM | Starfield `.mat` |
|---|---|---|
| Format | Flat JSON-ish, fixed field list | Graph of typed nodes/edges (JSON) |
| Layers | Single material | 1–6 blended layers + blenders |
| Storage | Loose `.bgsm`/`.bgem` in `Data\Materials\` | Loose `.mat` **and** compiled `materialsbeta.cdb` |
| Mesh link | `BSLightingShaderProperty.Name` → `.bgsm` | Same field → `.mat` |
| PBR packing | Specular/gloss packed (`_s`) | **One texture per property** (BC4), metal/rough workflow |
| Normal | BC7/BC5, Z present | **BC5 XY-only**, Z reconstructed, DirectX green |
| SSS/skin | Backlight map + flags | `TranslucencySettings` numeric block (+ optional transmissive map) |
| Effects | Separate `.bgem` (`Shader:"Effect"`) | `EffectSettings` component / effect shader models |
| Editor | CK Material Editor (BGSM) | CK Material Editor, NifSkope (fo76utils fork), Material Editor Lite, SFME |

---

## 8. Open questions / uncertainties

- ~~**`.cdb` write path.**~~ **RESOLVED:** a loose `.mat` is sufficient for shipping — the game/CK
  load loose JSON `.mat` at runtime, and no tool (NifSkope/nifly/Outfit Studio) writes a `.cdb` at
  all; NifSkope authors a loose JSON `.mat` directly. No `.cdb` compile step is required, including
  for the character/skin path. (Remaining minor unknown: exact loose-vs-`.cdb` *precedence*, which
  doesn't block authoring.)
- **Exact slot indices** for the non-core slots (`NormalIntensity`, `Flow`, `Frost`, `Secondary
  Opacity`, `ScatteringDirections/ForwardAlpha`, `Overlay AO`, `AmbientOcclusion`) — the fo76utils
  index list and the CK template names don't fully line up; needs a byte-level check against a real
  character `.mat`.
- **Loose-vs-`.cdb` override semantics** (full replace vs merge) — undocumented.
- **Blend-mode enumeration** (Linear/Additive/Skin/PositionContrast and any others) and their exact
  compositing math — inferred from renderer support, not from official docs.
- **How the skin/hair numeric params map to Blender's Principled v2** (SSS radius units, backscatter →
  sheen) — needs perceptual calibration against in-game reference.

---

## Sources

- Starfield Geometry Bridge — Material (.mat) file: https://starfieldgeometrybridge.github.io/docs/tips/material/
- Nexus — "Creating A CUSTOM material for your Mod in Starfield": https://www.nexusmods.com/starfield/articles/411
- Nexus forums — "Starfield's .cdb Material Database" discussion: https://forums.nexusmods.com/topic/13361451-starfields-cdb-material-database/
- fo76utils NifSkope fork — CHANGELOG (Starfield material handling): https://github.com/fo76utils/nifskope/blob/develop/CHANGELOG.md
- fo76utils NifSkope — `lib/libfo76utils/src/material.hpp` (texture slot order, settings structs): https://github.com/fo76utils/nifskope/blob/develop/lib/libfo76utils/src/material.hpp
- fo76utils NifSkope — `src/spells/sfmatexport.cpp`, `src/matcomps.cpp`, `src/bsrefl.cpp` (material JSON export): https://github.com/fo76utils/nifskope
- Gibbed.Starfield (.cdb tooling): https://github.com/gibbed/Gibbed.Starfield
- fo76utils / ce2utils (material dump, mat_names.txt): https://github.com/fo76utils/ce2utils
- Starfield Material Exporter (SFME): https://github.com/maximusmaxy/SFME and https://www.nexusmods.com/starfield/mods/7830
- Material Editor Lite: https://www.nexusmods.com/starfield/mods/14659
- Step Mods — "Starfield Texture Formats" (BC7/BC5/BC4 conventions, suffixes): https://stepmodifications.org/forum/topic/19037-starfield-texture-formats/
- Allmods — "Organization of Starfield's Meshes and Related Assets": https://allmods.net/starfield-mods/starfield-miscellaneous/organization-of-starfields-meshes-and-related-assets/
- Real shipped `.mat` example: HelixTechGroup/HTG-Regenesys-Character `…\VaultBoyBobbleheads\VaultBoy.mat`: https://github.com/HelixTechGroup/HTG-Regenesys-Character
- Local game data: `Data\EditorFiles\RuleTemplates\ShaderModels\*.json` (shader-model templates), `Data\Starfield - Materials.ba2` (`materialsbeta.cdb`)

_Draft 2026-07-06 — not yet reviewed_
