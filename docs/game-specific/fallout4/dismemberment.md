# Dismemberment (Fallout 4)

Fallout 4 can sever a limb from a skinned actor at runtime — the limb separates,
gore appears at the cut, and the detached piece becomes a physics object. This is
driven by data baked into the body's NIF (the `BSSubIndexTriShape` segmentation)
plus an external `.ssf` file. Skyrim has no equivalent runtime dismemberment of
arbitrary skinned meshes; this is a Creation Engine (FO4+) feature.

> **Status:** Parts of this document are *verified from raw NIF bytes* (the
> segment structure and cut-offset layout, read directly from vanilla
> `MaleBody.nif`). The runtime *behaviour* — how the engine chooses a cut plane
> and slices the mesh — is *inferred* from that data plus the known field
> semantics, not from engine code. Inferred claims are flagged **(inferred)**.

## The pieces involved

| Piece | Where it lives | Role |
|-------|----------------|------|
| `BSSubIndexTriShape` (SSITS) | The body NIF | A skinned tri shape that additionally carries **segmentation**: every triangle belongs to a segment/subsegment, tagged by body part. |
| Segment / subsegment table | Inside the SSITS block | Groups triangles by body part, tags each group with a **dismember-material ID** (the "Bone ID" in NifSkope — a fixed body-part-class constant) and a **user index**. |
| Cut offsets | Inside the SSITS per-segment shared data | Per-subsegment list of **slice-plane positions along the bone**. This is the data that actually enables a cut. |
| `.ssf` file | Loose / BA2, path stored in the NIF | External JSON listing, per dismemberable part, which skeleton bones get a "delta" (hide/scale) applied when that part is severed. |

All four must agree for dismemberment to work. The NIF stores the *path* to the
`.ssf`; the `.ssf` is a separate file on disk.

## The `BSSubIndexTriShape` segmentation

A skinned FO4 body is a `BSSubIndexTriShape` (SSITS) rather than a plain
`BSTriShape`. Beyond the usual verts/tris/skin data it carries a segmentation
structure with two parallel halves:

### 1. Segment topology (which triangles belong where)

A flat list of **segments**, each with an ordered list of **subsegments**. Each
(sub)segment owns a contiguous run of the triangle array:

| Field | Type | Meaning |
|-------|------|---------|
| Start Index | uint | Byte/triangle offset where this group's triangles begin |
| Num Primitives | uint | Triangle count in this group |
| Array Index | uint | This group's position in the flattened (segments + subsegments) order |
| (subsegments) | list | Child subsegments of a segment |

Because each group is a *range*, the triangles must be **physically sorted by
segment** in the triangle array. Tools that write SSITS shapes re-sort the
triangle list so each segment's tris are contiguous.

Bodypart segment layout is fixed. If a segment is not used in a nif, it is present and empty to hold the slot: 

```
Seg 0  (always empty)
Seg 1  (head; empty in the human body nif; usually no subsegments)
Seg 2  (Right arm)
Seg 3  (torso; usually no subsegments)
Seg 4  (Left arm)
Seg 5  (Right leg)
Seg 6  (Left leg)
```

Any segments that are unused in a nif **must exist** — they hold the
limb segments at fixed indices, which the `.ssf` references by
position (see below). But trailing empty segments can be omitted.

### 2. Per-segment shared data (the dismember tags + cut offsets)

A second array, one record per flattened (sub)segment, in the same order as the
topology. Each record:

| Field | Type | Meaning |
|-------|------|---------|
| User Index | uint | **Segment** record (Bone ID `0xFFFFFFFF`): the segment's own index (0,1,2…). **Subsegment** record: a positional counter starting at 1 within its segment (1,2,3…) — *not* a body-part id, just a sequence number — **unless** the subsegment is a biped-object attachment, in which case it's that biped slot. The discriminator is the value: `< 30` = positional filler (tools normalize it to 0 on read); `≥ 30` = a real biped slot preserved verbatim (e.g. Pip-Boy = 60, Pip-Boy Cap = 160). |
| Bone ID | uint | A fixed **dismemberment-material / body-part-class ID** (the "material"). nif.xml calls it "a hash of the bone name string," but it is **not** a hash of the *skeleton* bone name: the same value is reused for the equivalent part across different creatures with different skeletons (e.g. `0xB2E2764F` tags the upper-right-arm class on both human and supermutant; `0x9AF9D18C` on both deathclaw and feral ghoul). Small values are literal biped-slot numbers (synth parts use 40/50/80/90). So it functions as an opaque constant identifying a dismember class — not reproducible from the bone name; tools carry a fixed lookup table. `0xFFFFFFFF` on plain segments. |
| Num Cut Offsets | uint (0–8) | How many cut planes follow. |
| Cut Offsets | float × N | The slice-plane positions. **See below.** |

This block ends with the `.ssf` file path (a length-prefixed string).

Example dismember material hashes (vanilla male body):

| Hash | Bone (FO4 skeleton) |
|------|---------------------|
| `0xb2e2764f` | RArm_UpperArm |
| `0x6fc3fbb2` | RArm_ForeArm1 |
| `0xbf3a3cc5` | RLeg_Thigh |
| `0x22324321` | RLeg_Calf |
| `0xc7e6bc92` | RLeg_Foot |

(…and left-side equivalents: `LArm_UpperArm`, `LArm_ForeArm1`, `LLeg_Thigh`,
`LLeg_Calf`, `LLeg_Foot`.)

## Cut offsets — the key to dismemberment

The **cut offsets** cut the long bones to make a part severable. A subsegment with zero cut
offsets cannot be cut; a body whose every subsegment has `Num Cut Offsets = 0`
will not dismember at all even though its segment structure looks complete.

### Structure

Each cut offset list is monotonically increasing (probably required), and every value is an integer multiple
`k · step` of a per-bone step — so the cuts are evenly spaced (though some cuts are skipped in some meshes). Likely the even spacing is not required, though it may relate to the size of the cuff on the meatcap.

For vanilla `MaleBody.nif`:

| Bone | n | step | k values present |
|------|---|------|------------------|
| RArm_UpperArm | 4 | 1.9014 | 4, 5, 6, 7 |
| RArm_ForeArm1 | 5 | 1.8678 | 3, 4, 5, 6, 7 |
| RLeg_Thigh | 4 | 3.2392 | 4, 5, 6, 7 |
| RLeg_Calf | 5 | 3.5662 | 2, 3, 4, 5, 6 |
| LLeg_Calf | 6 | 3.5662 | 1, 2, 3, 4, 5, 6 |

Observations that are *certain*:

- Values are floats in the same units as vertex coordinates (NIF world units).
- Cut points in vanilla meshes use consistent values of `k · step` for integer `k` on a per-bone grid. Some meshes, such as FatiguesM.nif, omit some cuts. (In the case of ArmyFatiguesM, the cut would land right at the top of the boot where the pants crumple up - probably the modeler decided a cut there would look bad.) 
- When multiple subsegments map to one bone, generally only one subsegment has cuts--but generally only one subsegment is long enough to need them. 

### Attachment slots can carry cut offsets too

`FatiguesM.nif` attaches a Pip-Boy via biped-object subsegments (`User Index` =
the biped slot, ≥ 30, not the renumbered 1,2,3… of a dismember subsegment). The
Pip-Boy proper (slot 60, on `LArm_ForeArm1`) carries its own 5 cut offsets on the
same forearm grid, so it detaches when the lower-left arm is severed; the cosmetic
Pip-Boy Cap (slot 160) carries none. So cut offsets are not exclusive to the nude
dismember parts — any subsegment riding a dismemberable bone may carry them.

### A cut offset is a distance along the bone (verified against the skeleton)

- **A cut offset is a distance measured along the bone from its joint (pivot).**
  Every cut offset falls strictly within the bone's joint→child length (max ratio
  ~0.74), exactly as a slice position along the limb must.
- "Along the bone" means along the line segment that starts with the bone and proceeds in the direction the bone points (+X in the nif).
- **The step is roughly `bone_length / 9.5`** (length ÷ step ≈ 9–10 across all
  four bones). The bone is sampled at a near-constant density into ~9–10 slabs,
  and each part carries the slab positions within its own stretch. 
- It's possible to have cuts on the final bone in a limb, so there is no child bone.

#### Bearer bone vs. skeleton bones (multi-bone chains)

The "bone" the cut offset is measured from is the **dismember bearer** — the
single bone that the dismember-material hash maps to (e.g. `RArm_ForeArm1` for
the whole forearm). The actual skeleton typically splits a limb into several
physical bones for twist/skinning purposes (`RArm_ForeArm1`, `RArm_ForeArm2`,
`RArm_ForeArm3`, `RArm_Hand`), but the dismember system treats the chain as one
unit: cuts are anchored at the **chain head's head_local** (the elbow joint for
the forearm), even if subseg verts skin predominantly to a mid-chain or
distal-chain bone.

This is why the per-bone lengths in the table above (e.g. `RArm_ForeArm1` =
18.46) are joint-to-joint along the *dismember* chain (elbow→wrist), not the
short physical sub-bones in between. 

### How cut offsets are actually used — best working model

> **Unconfirmed but checked in game** (limbs severing at varying mid-shaft positions across runs,
> and never severing at joints) on top of the byte-level structure. Treat it as a
> strong working hypothesis rather than a verified fact.

**Cuts are the runtime severance positions along the bone shaft.** When a limb
takes a dismembering hit, the engine picks one of the bearer subsegment's cut
offsets and uses it to determine which triangles vanish — everything distal to
the chosen cut is removed (along with the joint-adjacent subsegments further out),
and a meat-cap mesh is fitted at the cut plane.

Three things that fit:

- **Cuts cluster along ashaft, not at joints.** Vanilla cut spans across all four
  human limb bones sit in the 22–74% range of the bone, leaving a clear buffer at
  both the proximal and distal joints. In-game limbs likewise sever along the long
  bone, never through the joint — there's no "shoulder pop" or "knee pop"
  dismemberment, only mid-shaft slices. The geometry simply offers no cut planes
  near a joint.
- **Multiple cuts give variation.** Each bearer typically carries 4–6 cut offsets
  across its span; perhaps this lets the same limb sever at slightly different
  positions across runs rather than always at the same height.
- **Subsegments group tris by cut region, not by separable unit.** The
  subsegments don't seem to define
  the *separation* points the engine picks — the cut offsets do. The slabs
  probably exist so the bearer (mid-shaft) cleanly owns the triangles that may be
  affected by a cut, while the joint-adjacent slabs always stay with the limb on
  whichever side.
- **Subsegments can be used by the game for dismemberment** especially in decapitation. Not clear how this interacts with cut points.

## The `.ssf` file

The NIF stores a path like `Meshes\Actors\Character\CharacterAssets\MaleBody.ssf`.
The file itself is JSON. Vanilla `MaleBody.ssf` (abridged):

```json
{
  "BaseMaleBody:0" : {
    "BaseBoneName" : "DISABLED",
    "DeltaBones" : [
      { "BoneDeltaList" : [ 262400 ], "BoneName" : "LArm_UpperArm" },
      { "BoneDeltaList" : [ 131840 ], "BoneName" : "RArm_ForeArm1" }
    ],
    "uiNumDeltas" : 8
  }
}
```

Each `DeltaBones` entry names a skeleton bone and a `BoneDeltaList`. The list
values **encode a segment/subsegment reference by position**:

```
value = (segment_index << 16) | (subsegment_index << 8)
```

So `262400 = 0x040100` → segment 4, subsegment 1 → the left upper arm. This is
why the empty placeholder segments matter: the `.ssf` addresses limbs by their
**fixed segment index**, and the subsegment index picks the exact group within.

| `.ssf` entry | Decoded | Points at |
|--------------|---------|-----------|
| `RArm_UpperArm` = 131328 | seg 2, sub 1 | Right arm, 2nd `RArm_UpperArm` subseg |
| `RArm_ForeArm1` = 131840 | seg 2, sub 3 | Right arm, `RArm_ForeArm1` subseg |
| `LArm_UpperArm` = 262400 | seg 4, sub 1 | Left arm |
| `RLeg_Thigh`    = 327936 | seg 5, sub 1 | Right leg |
| `LLeg_Calf`     = 393984 | seg 6, sub 3 | Left leg |

### Why both the NIF segmentation *and* the SSF?

They look redundant but carry different halves of the picture — **geometry** vs.
**skeleton wiring**.

The NIF segmentation is geometry only: it groups triangles into separable chunks
and tags each with a dismember-**material class** (the `0xB2E2764F`-style constant).
It does **not** record which skeleton bone a chunk belongs to, nor what should
happen to the skeleton when the chunk is removed.

The SSF supplies exactly those two things, keyed to this body's actual bones:

- **Bone → chunk mapping (verified).** The game resolves damage to *bones*, but a
  NIF chunk only carries a material class — and that class is **creature-agnostic
  and reused** (`0xB2E2764F` is the upper-right-arm class on both human and
  supermutant), so it can't by itself say *which bone on this skeleton* it is.
  Each `DeltaBones` entry names a real bone and lists `(segment<<16 |
  subsegment<<8)` references into this NIF — i.e. it *is* the bone→subsegment map.
  Deriving this from skin weights wouldn't work (a chunk's verts are weighted to
  many bones).
- **Bone delta on severance (guess).** The `DeltaBones` / `BaseBoneName` naming
  implies a transform/scale applied to bones when a part is lost — retract or
  zero-scale them so no stump or floating geometry remains. **Unconfirmed**; the
  mechanic is inferred from the field names, not from engine behaviour.

In short: **the NIF says where the mesh can split; the SSF says which bone owns
each split (and, probably, how the skeleton reacts).** The engine appears to need
both. 

## Authoring checklist

For a custom skinned FO4 body to dismember:

1. Shape is a `BSSubIndexTriShape` with the segment layout the matching `.ssf`
   expects, placeholders included, triangles sorted by segment. A full nude body
   uses 7 segments (0–6); a partial garment (e.g. a sleeve) uses fewer — the
   ArmyFatigues sleeves use 5. What matters is that the segment/subsegment indices
   line up with the `.ssf`'s `BoneDeltaList` references.
2. Each limb subsegment tagged with the correct dismember material (bone hash)
   and user index.
3. **Cut offsets present** on the representative subsegment of each body part.
4. NIF references a valid `.ssf` whose `BoneDeltaList` segment/subsegment indices
   match the shape's layout.
5. The `.ssf` file actually exists at the referenced path (loose or in a BA2).

## See also

- [NIF files](../../file-formats/nif-files.md)
- [Physics & collision](../../file-formats/physics-collision.md)

*Verified 2026-05-30, Bad Dog*