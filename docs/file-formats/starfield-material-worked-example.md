# Starfield `.mat` — Annotated Worked Example (a real 2-layer skin material)

This is a **complete, shipped** Starfield material read straight out of the game's compiled
material database — `Materials\Actors\Human\Naked_Body\Male\Naked_M_Body.mat` (the naked male
body skin). It was reconstructed from `materialsbeta.cdb` (game build 1.16.244.0) by PyNifly's
`pyn/sf_cdb.py` reader, which emits the same loose `.mat` JSON the Creation Kit and community
tools produce.

It's a good teaching example because it exercises most of the layered-material system in one
file: two material **layers** combined by a **blender**, subsurface scattering, a base-skin
**texture set** plus a tiled **detail-normal** texture set, per-layer **UV streams**, and the
template **inheritance** chain. Read [starfield-materials.md](starfield-materials.md) first for
the format overview; this page walks the file top to bottom.

> **How to read the JSON.** Every typed value is `{ "Type": "...", "Data": {...} }`. Numbers and
> booleans are stored as **strings** (`"0.5"`, `"true"`) — that's how the database serializes
> them, not a quirk of the extractor. A `.mat` is a flat list of **objects**, each a bag of
> **components**; objects reference each other by `res:DIR:FILE:EXT` **resource IDs**, so the
> file is really a small graph. `Index` disambiguates repeated components (e.g. one
> `MRTextureFile` per texture slot). `Parent` names the template material this object derives
> from — anything not overridden here is inherited from that template.

## The shape of it

Ten objects, wired like this (arrows = a component that references another object by `res:` ID):

```
Naked_M_Body                      (root: the LayeredMaterial)
├─ BlenderID  ─────────────▶ Blender1        mask = NakedBodyM_mask, mode = Skin
├─ LayerID[0] ─────────────▶ Layer1
│                              ├─ MaterialID ─▶ Material1  (tint) ─ TextureSetID ─▶ TextureSet1
│                              │                                      color / normal / rough / ao  (base skin)
│                              └─ UVStreamID ─▶ UVStreamA   (default UVs)
├─ LayerID[1] ─────────────▶ Layer2
│                              ├─ MaterialID ─▶ Material2 ─ TextureSetID ─▶ TextureSet2
│                              │                                      detail normal (cheek pores)
│                              └─ UVStreamID ─▶ UVStreamB   (Scale 50×50 → tiles the detail)
├─ TranslucencySettings        UseSSS = true                 (skin subsurface)
└─ ShaderModel = BodySkin2Layer
```

The engine renders it by starting at the root, walking those references, and blending Layer 2
over Layer 1 through the blender.

---

## Object 0 — the root LayeredMaterial

```jsonc
{
  "Components": [
    { "Type": "BSComponentDB::CTName", "Index": 0,
      "Data": { "Name": "Naked_M_Body" } },
```
`CTName` is just the object's human name. Every object has one; it's for tooling, not the engine.

```jsonc
    { "Type": "BSBind::DirectoryComponent", "Index": 0,
      "Data": { "upDir": { "Type": "<ref>", "Data": { "Type": "BSBind::Directory",
        "Data": { "Name": "", "Children": { "Type": "<collection>",
          "ElementType": "StdMapType::Pair", "Data": [] }, "SourceDirectoryHash": "0" } } } } },
    { "Type": "BSBind::ControllerComponent", "Index": 0,
      "Data": { "upControllers": { "Type": "<ref>", "Data": { "Type": "BSBind::Controllers",
        "Data": { "MappingsA": { "Type": "<collection>", "Data": [] },
          "UseRandomOffset": "false" } } } } },
```
The two `BSBind::*` components are the **animation-binding** plumbing — how a material parameter
could be driven by a controller at runtime. Here both are empty (`Children` / `MappingsA` are
empty collections), i.e. **nothing is animated**. Notes on the encoding:
- `"Type": "<ref>"` is a **pointer** to an inline sub-object — read the nested `Data`.
- `"Type": "<collection>"` is a list or map; `ElementType: "StdMapType::Pair"` marks a map.
  Empty here, so there's nothing to see, but this is where a driven material would list its
  bindings.

```jsonc
    { "Type": "BSMaterial::BlenderID", "Index": 0,
      "Data": { "ID": "res:9FD163C7:0005F68E:A52AC310" } },
    { "Type": "BSMaterial::LayerID", "Index": 0,
      "Data": { "ID": "res:04C7A198:0005C61C:A2A909D2" } },
    { "Type": "BSMaterial::LayerID", "Index": 1,
      "Data": { "ID": "res:9FD163B7:0005F68E:A52AC310" } },
```
The **structure of the layer stack**, by reference:
- `LayerID[0]` → **Layer1** (base skin), `LayerID[1]` → **Layer2** (detail).
- `BlenderID[0]` → **Blender1**, which sits *between* the layers and controls how Layer 2 is
  combined over Layer 1. (In general `Blender_N` blends `Layer_(N+1)` onto everything below.)
- The `Index` on the `LayerID`s (0, 1) is the stack position. These `res:` IDs are resolved to
  the objects further down this same file.

```jsonc
    { "Type": "BSMaterial::TranslucencySettingsComponent", "Index": 0,
      "Data": { "Enabled": "true", "Settings": { "Type": "BSMaterial::TranslucencySettings",
        "Data": { "UseSSS": "true",
                  "SpecLobe0RoughnessScale": "0.9300000071525574",
                  "SpecLobe1RoughnessScale": "1.149999976158142" } } } },
```
**Subsurface scattering** — this is what makes skin read as skin. `UseSSS: true` turns on SSS;
the two `SpecLobe*RoughnessScale` values tune the dual-specular-lobe skin highlight (one tighter,
one broader). For a furry-race skin/fur material this is the block you'd clone and tune (see the
fur/skin notes in [starfield-materials.md](starfield-materials.md#4-layers-blenders-and-component-blocks)).

```jsonc
    { "Type": "BSMaterial::ShaderModelComponent", "Index": 0,
      "Data": { "FileName": "BodySkin2Layer" } },
```
The **shader model** (template) this material is built on: `BodySkin2Layer`. The shader model
decides *which* layers/slots/component blocks are even valid — it's the schema this material fills
in. `BodySkin2Layer` = two blended skin layers with SSS, which matches everything above.

```jsonc
    { "Type": "BSMaterial::LayeredEmissivityComponent", "Index": 0,
      "Data": { "Enabled": "false", "FirstLayerIndex": "MATERIAL_LAYER_0",
                "FirstLayerTint": { "Type": "BSMaterial::Color", "Data": { "Value": {
                  "Type": "XMFLOAT4", "Data": { "x": "1.0","y": "1.0","z": "1.0","w": "1.0" } } } },
                "FirstLayerMaskIndex": "None", "SecondLayerActive": "false", … 
                "LuminousEmittance": "432.0", "ExposureOffset": "0.0", … "IgnoresFog": "false" } }
  ],
  "Parent": "materials\\layered\\root\\layeredmaterials.mat"
}
```
Emissivity, **disabled** here (`Enabled: false`) — skin doesn't glow. It's still fully specified
because the shader model includes the block; note `LuminousEmittance: 432.0` is a leftover/default
value that does nothing while `Enabled` is false. `XMFLOAT4 {x,y,z,w}` is an RGBA color (here
white). The enum-like strings (`MATERIAL_LAYER_0`, `BLEND_LAYER_0`, `Lerp`, `None`) name layers,
blenders, and blend modes.

`"Parent": "…\\root\\layeredmaterials.mat"` — the root object inherits from the top-level
`LayeredMaterials` template; every field above is an **override** on that template's defaults.

---

## Object 1 — Blender1 (how the two layers combine)

```jsonc
{
  "ID": "res:9FD163C7:0005F68E:A52AC310",
  "Components": [
    { "Type": "BSComponentDB::CTName", "Index": 0, "Data": { "Name": "Naked_M_Body_Blender1" } },
    { "Type": "BSMaterial::UVStreamID", "Index": 0, "Data": { "ID": "" } },
    { "Type": "BSMaterial::BlendModeComponent", "Index": 0, "Data": { "Value": "Skin" } },
    { "Type": "BSMaterial::ParamBool", "Index": 0, "Data": { "Value": "false" } },
    { "Type": "BSMaterial::ParamBool", "Index": 1, "Data": { "Value": "false" } },
    { "Type": "BSMaterial::ParamBool", "Index": 2, "Data": { "Value": "false" } },
    { "Type": "BSMaterial::MRTextureFile", "Index": 0,
      "Data": { "FileName": "Data\\Textures\\Actors\\Human\\naked_body\\NakedBodyM_mask.dds" } },
    { "Type": "BSMaterial::MaterialParamFloat", "Index": 4, "Data": { "Value": "0.5" } }
  ],
  "Parent": "materials\\layered\\root\\blenders.mat"
}
```
The blender is its own object (the root pointed here via `BlenderID`). Note its `ID` matches the
root's `BlenderID` value. Key fields:
- `BlendModeComponent: "Skin"` — a skin-specific blend (not a plain Lerp), so the detail layer
  combines the way the engine expects for skin.
- `MRTextureFile[0]` = **`NakedBodyM_mask.dds`** — the blend **mask**: where (and how much) Layer 2
  shows through over Layer 1. On a blender, slot 0 is the mask, *not* an albedo.
- `MaterialParamFloat[4] = 0.5` and the three `ParamBool`s are blender knobs defined by the shader
  model (blend strength / per-channel toggles); their exact meaning is shader-model-specific.
- `UVStreamID: ""` — empty ID = **inherit** the parent template's UV stream (no per-blender UVs).

> **This is the texture the naive "first-layer-wins" parser wrongly grabs as the albedo.** It's a
> *mask*, and it's the very first `MRTextureFile` (slot 0) in document order, which is why a simple
> importer mislabels it. The real albedo lives in TextureSet1, below.

---

## Objects 2 & 3 — the two Layers

```jsonc
{ "ID": "res:04C7A198:0005C61C:A2A909D2",
  "Components": [
    { "Type": "BSComponentDB::CTName", "Index": 0, "Data": { "Name": "Naked_M_Body_Layer1" } },
    { "Type": "BSMaterial::MaterialID", "Index": 0, "Data": { "ID": "res:04C7A1AD:0005C61C:A2A909D2" } },
    { "Type": "BSMaterial::UVStreamID", "Index": 0, "Data": { "ID": "res:04C7A206:0005C61C:A2A909D2" } } ],
  "Parent": "materials\\layered\\root\\layers.mat" }

{ "ID": "res:9FD163B7:0005F68E:A52AC310",
  "Components": [
    { "Type": "BSComponentDB::CTName", "Index": 0, "Data": { "Name": "Naked_M_Body_Layer2" } },
    { "Type": "BSMaterial::MaterialID", "Index": 0, "Data": { "ID": "res:9FD163C0:0005F68E:A52AC310" } },
    { "Type": "BSMaterial::UVStreamID", "Index": 0, "Data": { "ID": "res:9FD163BE:0005F68E:A52AC310" } } ],
  "Parent": "materials\\layered\\root\\layers.mat" }
```
A **layer** is deliberately thin: it just points at a **Material** (the look) and a **UV stream**
(how that look is mapped onto the mesh). Layer1's `MaterialID` → Material1, `UVStreamID` →
UVStreamA; Layer2's → Material2 / UVStreamB. Both inherit from the `layers.mat` template.

---

## Objects 4 & 6 — the two Materials

```jsonc
{ "ID": "res:04C7A1AD:0005C61C:A2A909D2",
  "Components": [
    { "Type": "BSComponentDB::CTName", "Index": 0, "Data": { "Name": "Naked_M_Body_Material1" } },
    { "Type": "BSMaterial::TextureSetID", "Index": 0, "Data": { "ID": "res:04C7A1DF:0005C61C:A2A909D2" } },
    { "Type": "BSMaterial::MaterialOverrideColorTypeComponent", "Index": 0, "Data": { "Value": "Multiply" } },
    { "Type": "BSMaterial::Color", "Index": 0, "Data": { "Value": { "Type": "XMFLOAT4",
        "Data": { "x": "0.7372549772262573", "y": "0.7372549772262573",
                  "z": "0.7372549772262573", "w": "0.0" } } } } ],
  "Parent": "materials\\layered\\root\\materials.mat" }
```
Material1 (base skin) points at **TextureSet1** and adds a **tint**: `MaterialOverrideColorType =
Multiply` with `Color = (0.737, 0.737, 0.737, α 0)` — the albedo is multiplied by ~0.74 grey
(darkening it slightly). The `w`/alpha of `0.0` here is the tint's blend amount, not opacity.

```jsonc
{ "ID": "res:9FD163C0:0005F68E:A52AC310",
  "Components": [
    { "Type": "BSComponentDB::CTName", "Index": 0, "Data": { "Name": "Naked_M_Body_Material2" } },
    { "Type": "BSMaterial::TextureSetID", "Index": 0, "Data": { "ID": "res:9FD163C1:0005F68E:A52AC310" } } ],
  "Parent": "materials\\layered\\root\\materials.mat" }
```
Material2 (detail) is minimal — just its **TextureSet2**; everything else comes from the template.

---

## Objects 5 & 7 — the two UV Streams

```jsonc
{ "ID": "res:04C7A206:0005C61C:A2A909D2",
  "Components": [ { "Type": "BSComponentDB::CTName", "Index": 0,
                    "Data": { "Name": "Naked_M_Body_UVStreamA" } } ],
  "Parent": "materials\\layered\\root\\uvstreams.mat" }

{ "ID": "res:9FD163BE:0005F68E:A52AC310",
  "Components": [
    { "Type": "BSComponentDB::CTName", "Index": 0, "Data": { "Name": "Naked_M_Body_UVStreamB" } },
    { "Type": "BSMaterial::Scale", "Index": 0, "Data": { "Value": { "Type": "XMFLOAT2",
        "Data": { "x": "50.0", "y": "50.0" } } } } ],
  "Parent": "materials\\layered\\root\\uvstreams.mat" }
```
UVStreamA has **only** a name — it fully inherits the default 1:1 UVs from the template (the base
skin uses the mesh's real UVs). UVStreamB adds `Scale = (50, 50)`: the detail layer's UVs are
**tiled 50×**, so the small `Young_Cheek_detail_normal` texture repeats densely across the body as
fine skin detail. `XMFLOAT2` is a 2-component (u,v) value. This is the key trick that turns one
small detail texture into all-over pore detail.

---

## Objects 8 & 9 — the two Texture Sets (where the actual images live)

```jsonc
{ "ID": "res:04C7A1DF:0005C61C:A2A909D2",
  "Components": [
    { "Type": "BSComponentDB::CTName", "Index": 0, "Data": { "Name": "Naked_M_Body_TextureSet1" } },
    { "Type": "BSMaterial::TextureReplacement", "Index": 8, "Data": { "Enabled": "true" } },
    { "Type": "BSMaterial::MRTextureFile", "Index": 0,
      "Data": { "FileName": "Data\\Textures\\Actors\\human\\Naked_Body\\nakedbodym_sk3_color.dds" } },
    { "Type": "BSMaterial::MRTextureFile", "Index": 1,
      "Data": { "FileName": "Data\\Textures\\Actors\\human\\Naked_Body\\nakedbodym_normal.dds" } },
    { "Type": "BSMaterial::MRTextureFile", "Index": 3,
      "Data": { "FileName": "Data\\Textures\\Actors\\human\\Naked_Body\\nakedbodym_rough.dds" } },
    { "Type": "BSMaterial::MRTextureFile", "Index": 5,
      "Data": { "FileName": "Data\\Textures\\Actors\\human\\Naked_Body\\NakedBodyM_ao.dds" } } ],
  "Parent": "materials\\layered\\root\\texturesets.mat" }
```
**This is the base skin.** Each `MRTextureFile.Index` is a **texture slot** (see the slot table in
[starfield-materials.md](starfield-materials.md#5-textureset-slots--dds-conventions)):

| `Index` | Slot | This file |
|---|---|---|
| 0 | Albedo (`_color`, sRGB) | `nakedbodym_sk3_color.dds` |
| 1 | Normal (`_normal`, BC5 XY) | `nakedbodym_normal.dds` |
| 3 | Roughness (`_rough`, BC4) | `nakedbodym_rough.dds` |
| 5 | Ambient occlusion (`_ao`, BC4) | `NakedBodyM_ao.dds` |

Slots 2 (opacity) and 4 (metalness) are simply absent — skin isn't transparent or metallic. Note
Starfield stores **one texture per property** (no packed `_s` map like `[FO4]`). The
`TextureReplacement[8] Enabled: true` turns on the transmissive slot (index 8) for the SSS pass
without supplying a texture — it uses the setting/fallback rather than an image.

```jsonc
{ "ID": "res:9FD163C1:0005F68E:A52AC310",
  "Components": [
    { "Type": "BSComponentDB::CTName", "Index": 0, "Data": { "Name": "Naked_M_Body_TextureSet2" } },
    { "Type": "BSMaterial::TextureReplacement", "Index": 8, "Data": { "Enabled": "true" } },
    { "Type": "BSMaterial::TextureReplacement", "Index": 3, "Data": { "Color": { "Type": "BSMaterial::Color",
        "Data": { "Value": { "Type": "XMFLOAT4", "Data": { "x": "1.0","y":"1.0","z":"1.0","w":"1.0" } } } } } },
    { "Type": "BSMaterial::MRTextureFile", "Index": 1,
      "Data": { "FileName": "Data\\Textures\\Actors\\human\\faces\\FaceDetails\\Young_Cheek_detail_normal.dds" } } ],
  "Parent": "materials\\layered\\root\\texturesets.mat" }
```
**This is the detail layer**, and it's almost entirely a **normal map**: slot 1 =
`Young_Cheek_detail_normal.dds` (fine skin/pore detail, reused from the face-detail set). It has
**no albedo** — the detail layer only perturbs the surface normal; the base skin's color shows
through. The two `TextureReplacement`s stand in for the missing slots: index 8 (transmissive)
enabled, index 3 (roughness) replaced by a **flat white** color (`1,1,1,1`) since there's no
detail-roughness image. `TextureReplacement` is how a slot is filled by a constant instead of a
texture.

---

## What to take away

- **A `.mat` is a graph, not a flat list of slots.** The root LayeredMaterial references Blenders
  and Layers; each Layer references a Material and a UV stream; each Material references a Texture
  set. To find "the albedo," you follow `LayerID → MaterialID → TextureSetID → MRTextureFile[0]` —
  **not** the first `MRTextureFile` in the file (that one is the blender mask here).
- **Slots are addressed by `Index`, and gaps are normal.** Missing slots mean "this property is
  unused," or are filled by a `TextureReplacement` constant.
- **`Parent` + overrides is the whole model.** Each object states only what differs from its
  root template (`…\root\{layeredmaterials,blenders,layers,materials,uvstreams,texturesets}.mat`);
  the rest is inherited. The database stores these as *diffs*, and the reader composes the parent
  chain back into the full object you see here.
- **This exact structure is the fur/skin blueprint for a custom race:** `BodySkin2Layer` shader
  model, SSS via `TranslucencySettings`, a base-skin texture set on Layer 1, and a tiled
  detail/pattern layer on Layer 2 blended in `Skin` mode through a mask. Fur markings can ride the
  detail layer (or a third layer); the tiling (`UVStream.Scale`) controls how fine the pattern is.

---

_Source: `Materials\Actors\Human\Naked_Body\Male\Naked_M_Body.mat`, extracted from `materialsbeta.cdb`
(build 1.16.244.0) with PyNifly's `pyn/sf_cdb.py`. JSON verbatim except for reflow/eliding of
already-covered repeats._

_Draft 2026-07-10 — not yet reviewed_
