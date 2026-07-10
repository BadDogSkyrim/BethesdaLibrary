# Connect Points (Fallout 4)

Connect points are an FO4-specific NIF mechanism for runtime attachment of one mesh to another. The engine reads named attachment points on a parent NIF and snaps a child NIF's matching point to align with it. Used for:

- **Weapon mods** — scopes, barrels, stocks, magazines, muzzle devices attaching to a receiver
- **Power armor** — helmet, torso, arm, and leg pieces attaching to the frame
- **Workshop building** — snap-together construction (walls to floors, roofs to walls, etc.)
- **Some creature/NPC attachments** — robotic limbs, prosthetics

Skyrim has nothing equivalent at the NIF level — this is a Creation Engine (FO4+) feature. Skyrim achieves similar results via skeleton bones and BipedObject attachment slots instead.

## Block Types

Two NIF blocks define the system:

### `BSConnectPoint::Parents`

Declares attachment points this NIF **offers** — places where other NIFs can attach.

**Per-entry fields:**

| Field | Type | Meaning |
|-------|------|---------|
| Parent | string | Name of the bone / `NiNode` in this NIF that the connect point rides on. Empty string = root NiNode. |
| Name | string | The connect point's unique name within this NIF (e.g., `"P-Scope"`, `"P-Barrel"`). Children reference this name when attaching. |
| Translation | Vec3 | Local offset from the parent node |
| Rotation | Quaternion | Local orientation |
| Scale | float | Usually 1.0 |
| Variable Name | string | Optional grouping tag the engine uses to determine which points may snap to which |

A single NIF may declare many parent points. A weapon receiver typically exposes Scope, Barrel, Stock, Magazine, Grip, and Muzzle points all on one mesh.

### `BSConnectPoint::Children`

Declares this NIF as a **child** that attaches to a specific parent point on another NIF.

**Per-entry fields:**

| Field | Type | Meaning |
|-------|------|---------|
| Name | string | Parent connect point name to attach to (e.g., `"P-Scope"`) |
| Skinned | bool | Whether the child is skinned to the parent's skeleton (true for power armor parts; false for most weapon mods) |

Most child NIFs declare exactly one entry: "I attach to a point named X." The engine looks up X in the parent NIF's `BSConnectPoint::Parents` list and aligns accordingly.

## Naming Convention

Bethesda uses a `P-` prefix on parent connect points in source files. The OMOD (Object Modification) record's prefix system can replace `P-` with a per-weapon prefix at runtime, so the same mod NIF can serve multiple base weapons.

**Common weapon parent points (source-side names):**

| Name | Purpose |
|------|---------|
| `P-Mag` | Magazine attachment |
| `P-Scope` | Sights / scope |
| `P-Barrel` | Barrel |
| `P-Stock` | Stock / shoulder rest |
| `P-Grip` | Grip / handle |
| `P-Receiver` | Receiver (the base of the weapon) |
| `P-Muzzle` | Muzzle device (suppressor, brake, compensator) |

If an OMOD specifies the prefix `"ap_gun"`, the runtime point name becomes `"ap_gun_Scope"`, `"ap_gun_Mag"`, etc. The mod NIF's `BSConnectPoint::Children` entries must match the *post-prefix* names.

Power armor and workshop pieces use their own naming conventions (frame slots, snap categories) — same mechanism, different vocabulary.

## Snap Behavior

When the engine attaches a child NIF to a parent at runtime:

1. **Parent lookup** — find the `BSConnectPoint::Parents` entry whose Name matches the child's declared attach name.
2. **Bone resolution** — locate the parent NIF node named in that entry's Parent field (root NiNode if empty).
3. **Transform composition** — the child is placed at:
   `parent_bone_world_transform × parent_connect_point_local_transform`
4. **Child placement** — the child NIF's root is positioned at the resulting world transform; any local offset on the child's `BSConnectPoint::Children` entry is applied on top.

Because the child rides on a parent bone, animations on the parent (recoil, equip, reload) carry through to attached mods automatically — no separate animation logic needed.

## Workshop Building

Workshop pieces use connect points for snap-together construction. Differences from weapon mods:

- Connect points represent **socket geometry** (corners, edges, ceilings) rather than just pivot offsets
- The engine matches points across pieces by both **name and orientation**
- The **Variable Name** field gates compatibility — a `"WallSnap"` point won't connect to a `"FloorSnap"` point even if positions align
- Workshop categories (electrical, structural, foundation, etc.) further constrain which points can connect

The workshop system layers on top of the NIF mechanism via WRKS records and the workshop snap script.

## OMOD Integration

Object Modifications (OMOD records) describe how a mod NIF integrates with a base item. For connect points specifically:

- **Attach Point** field on the OMOD names the parent connect point on the base NIF
- The mod NIF's `BSConnectPoint::Children` must include a matching name entry
- OMOD applies the prefix transformation (e.g., `"P-Mag"` with prefix `"ap_gun"` becomes `"ap_gun_Mag"`)
- A single weapon can have many OMODs simultaneously (one per attach slot), each contributing its own mod NIF

## Editing in NifSkope

**Adding a parent point:**

1. Right-click root NiNode → Block → Insert → `BSConnectPoint::Parents`
2. Expand the new block; set Num Connect Points to your count
3. For each entry, set Name (e.g., `"P-Scope"`), Parent (bone name or empty), Translation, Rotation
4. Use NifSkope's Connect Points view (View menu, in 2.0+) to visualize alignment

**Adding child attachment:**

1. Right-click root → Block → Insert → `BSConnectPoint::Children`
2. Set Name to match the parent point you're attaching to (post-prefix if OMOD applies one)
3. Set Skinned: false for most weapon mods, true if the mod is weighted to the parent's skeleton

**Visual alignment:**

NifSkope (2.0.0 Pre-alpha 5+) renders connect points as colored arrows in the 3D view. Open the parent and child NIFs side by side, then position/rotate the child point to align with where the mod should sit.

## Common Issues

### Mod doesn't attach in-game
- Name mismatch: parent has `"P-Scope"`, child has `"Scope"` (case- and prefix-sensitive)
- `BSConnectPoint::Parents` missing on the base weapon NIF
- OMOD doesn't reference the right connect point name

### Mod attaches in the wrong position
- Parent point's Translation / Rotation incorrect
- Child point's local offset stacking on top of the parent's
- Fix: load both NIFs in NifSkope, visualize the connect points, adjust until aligned

### Mod disappears when other mods are attached
- Variable Name conflict — two mods claiming overlapping slots
- OMOD's Attach Parent Slots not exclusive

### NifSkope crashes on "Refresh Connect Points"
- Known issue in some pre-alpha versions ([nifskope#94](https://github.com/niftools/nifskope/issues/94)) — update NifSkope or avoid that menu action

## See Also

- [NIF Files](../../file-formats/nif-files.md) — overall NIF block structure
- [Plugin Files](../../file-formats/plugins.md) — OMOD, WEAP, ARMA records
