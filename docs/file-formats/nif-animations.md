# NIF Animations

NIF files can contain self-contained animations that run on the scene-graph nodes within a single mesh — distinct from the HKX skeleton/animation system used for characters and creatures. NIF animations cover doors swinging, banners flapping, mill wheels turning, weapon enchantment glow, particle effects, and similar object-level motion.

For character and creature skeleton animation, see [HKX Animations](animations.md). The two systems share almost no implementation; don't confuse them.

## Controller System Overview

NIF animations are driven by a chain of blocks rooted at a `NiControllerManager`:

```
NiControllerManager  (top-level orchestrator)
  └── NiControllerSequence  (one named animation, e.g. "Open")
        └── ControlledBlock array
              ├── Target node name
              ├── Controller class (NiTransformController, etc.)
              └── NiTransformInterpolator
                    └── NiTransformData (keyframe data)
```

A NIF can contain multiple sequences (e.g. a door has "Open" and "Close" sequences). The Creation Kit and Papyrus reference sequences by name.

## Block Types

### NiControllerManager

Top-level animation coordinator. Required when a NIF needs more than one named sequence.

**Key fields:**
- **Cumulative** (bool) — whether sequences accumulate effects (rarely used; usually false)
- **Controller Sequences** (array) — references to child `NiControllerSequence` blocks
- **Object Palette** — symbol table mapping node-name strings to block references; lets sequences address targets by name without holding hard references

### NiControllerSequence

A single named animation.

**Key fields:**
- **Name** (string) — unique identifier the engine looks up (e.g. "Open", "Close", "Forward")
- **Cycle Type:**
  - `CYCLE_LOOP` — repeats indefinitely
  - `CYCLE_REVERSE` — ping-pong (forward, then back)
  - `CYCLE_CLAMP` — plays once, holds last frame
- **Frequency** — playback speed multiplier (1.0 = normal)
- **Start Time / Stop Time** — sequence duration boundaries in seconds
- **Text Keys** — embedded events (see below)
- **Controlled Blocks** (array) — what this sequence animates

### ControlledBlock

Each entry binds an interpolator to a target.

**Key fields:**
- **Interpolator** — usually `NiTransformInterpolator`, but can be alpha/float/color etc.
- **Controller Type** — class-name string (`"NiTransformController"`, `"NiAlphaController"`, …)
- **Target Node Name** — which node receives the animation (resolved via the manager's Object Palette)
- **Property Type** — string used by material/shader controllers to identify which property to drive

### NiTransformController

Animates the transform (translate / rotate / scale) of a target node. The most common controller type for object animation.

### NiTransformInterpolator

Produces interpolated transform values over time, sampling from a `NiTransformData`. Holds the default pose for the target plus a reference to the keyframe data.

### NiTransformData

The actual keyframe data: arrays of position keys, rotation keys (quaternion), and scale keys, each with their own interpolation modes (linear, quadratic, TBC). Same internal structure as the older `NiKeyframeData`.

## Common Controller Types

| Block | Animates | Typical use |
|-------|----------|-------------|
| `NiTransformController` | Node transform | Doors, levers, gears, banners |
| `NiVisController` | Node visibility | Hiding/showing parts |
| `NiAlphaController` | Alpha property | Fading in/out |
| `NiFloatController` (base) | Single float | Generic animated value |
| `BSLightingShaderPropertyFloatController` | Shader float | Glow strength, refraction strength, env-map scale |
| `BSLightingShaderPropertyColorController` | Shader color | Emissive tint, glow color |
| `BSEffectShaderPropertyFloatController` | Effect-shader float | Magic effect intensity |
| `NiPSysEmitterCtlr` | Particle emitter | Particle birth rate, lifetime |
| `NiPSysModifierActiveCtlr` | Particle modifier | Toggle modifier on/off over time |

## Text Keys (Events)

Sequences can embed named events that fire at specific times. Useful for triggering sounds, scripts, or game logic in sync with the animation.

**Structure:**
- **Time** (float, seconds)
- **Value** (string) — event name

**Common conventions:**
- `"start"` — fires at sequence beginning
- `"end"` — fires at sequence end
- Custom strings — game-specific events (e.g., `"sound_creak"` for a door)

Papyrus and the behavior graph can hook these for synchronizing audio and scripted actions.

## Multi-Sequence NIFs (Doors, Activators)

A typical Skyrim door NIF contains:
- One `NiControllerManager` at the root
- Two or more `NiControllerSequence` blocks (`"Open"`, `"Close"`)
- Each sequence references the same target nodes (the door's pivot) but with different keyframe data

The Papyrus `Activate()` call (or behavior graph) selects a sequence by name and plays it. The engine handles transitioning between sequences — usually by halting the current one and starting the new.

Activators (ACTI), furniture (FURN), and movable statics (MSTT) can all use the same pattern.

## Older Controller Flow (Pre-Manager)

Legacy NIFs use `NiKeyframeController` / `NiKeyframeData` attached directly to nodes, with no `NiControllerManager`. Found in:

- Older Skyrim assets ported from Oblivion
- Single-animation NIFs (e.g., a banner that just flaps continuously with one cycle)

NifSkope can convert legacy flow → manager flow if multiple sequences become necessary.

## Particle System Controllers

NIFs with particle effects use:

- `NiParticleSystem` — the emitter geometry / particle data
- `NiPSysEmitterCtlr` — controls emit rate over time
- `NiPSysModifier*` — modifiers (gravity, drag, color over life, size over life, etc.)
- Each modifier may have its own controller for time-varying parameters

Common in: weapon enchantment effects, magical impacts, environmental effects (smoke, sparks, embers).

## Editing in NifSkope

NifSkope is the primary tool:

- Right-click `NiControllerManager` → ControllerManager → Add Sequence
- Edit keyframes by expanding `NiTransformData` → Translations / Rotations / Scales
- Cycle through sequences with the playback controls at the bottom
- For complex edits, export to XML (Save As → XML), edit, re-import

## Common Issues

### Animation not playing
- Sequence name doesn't match what the engine expects (case-sensitive — `"Open"` ≠ `"open"`)
- ControlledBlock target node name doesn't match an actual `NiNode` in the NIF
- `NiControllerManager` not at the root, or missing entirely

### Animation plays once then freezes
- Cycle type is `CYCLE_CLAMP` — change to `CYCLE_LOOP` for continuous motion

### Keyframes drift past the end
- Stop Time not set correctly — keyframes beyond Stop Time are clipped silently

### Multiple sequences interfere with each other
- `Cumulative` flag enabled when sequences should be exclusive — disable it
- Sequences targeting overlapping nodes — partition the controlled blocks per sequence

## See Also

- [NIF Files](nif-files.md) — block hierarchy and scene structure
- [HKX Animations](animations.md) — character/creature skeleton animation (different system)
- [Plugin Files](plugins.md) — ACTI, FURN, MSTT records that reference animated NIFs
