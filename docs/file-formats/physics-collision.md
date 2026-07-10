# Physics & Collision

Bethesda games use Havok physics for collision detection and dynamic simulation. There are two main physics systems:

1. **Havok Collision** - Rigid body physics for objects and characters (embedded in NIF)
2. **HDT-SMP** - Skinned mesh physics for cloth, hair, tails (external XML configs)

## Havok Collision (NIF-Embedded)

### Overview

Havok collision data is embedded directly in NIF files. It defines:
- Collision shapes (how objects physically interact)
- Rigid body properties (mass, friction, motion type)
- Constraints (hinges, ragdolls, etc.)

**Havok versions:**
- **Skyrim LE/SE:** hk_2010.2.0-r1 (32-bit for LE, 64-bit for SE)
- **Fallout 4:** hk_2014.1.0-r1 (64-bit, packfile format)

### Collision Block Types (Skyrim)

#### bhkCollisionObject
Top-level collision attachment to scene nodes.

**Properties:**
- Target: Which NiNode this collision belongs to
- Flags: Collision enabled/disabled
- Body reference: Points to bhkRigidBody

#### bhkRigidBody
Physics body with mass, motion, and collision shape.

**Motion types** (from Havok's `hkpMotion::MotionType` enum):
- `MO_SYS_INVALID` (0)
- `MO_SYS_DYNAMIC` (1) - Responds to forces (boxes, ragdolls, dropped items)
- `MO_SYS_SPHERE_INERTIA` (2) / `MO_SYS_SPHERE_STABILIZED` (3) - Spherical inertia approximations
- `MO_SYS_BOX_INERTIA` (4) / `MO_SYS_BOX_STABILIZED` (5) - Box inertia approximations
- `MO_SYS_KEYFRAMED` (6) - Controlled by animation/script (moving platforms, doors)
- `MO_SYS_FIXED` (7) - Static, never moves (walls, floors, world geometry)
- `MO_SYS_THIN_BOX` (8) - Thin-box optimization
- `MO_SYS_CHARACTER` (9) - Character controller

**Key properties:**
- Mass (kg) - Higher = harder to move
- Friction (0.0-1.0) - Surface drag
- Restitution (0.0-1.0) - Bounciness (0 = no bounce, 1 = perfectly elastic)
- Linear damping - Slows down movement
- Angular damping - Slows down rotation
- Max linear velocity - Speed cap
- Max angular velocity - Rotation speed cap
- Gravity factor - Multiplier for gravity (1.0 = normal, 0.0 = weightless)

**Layer/Filter:**
- Collision layer - What category this object belongs to
- Collision filter - Which layers it collides with

#### bhkRigidBodyT
Variant of `bhkRigidBody` with a built-in transform (translation + rotation) baked into the body itself. Used (in both Skyrim and FO4) when the collision body needs to sit at an offset from its target node without an intermediate NiNode. The "T" stands for "transform," not Fallout-specific.

### Collision Shapes

#### bhkBoxShape
Rectangular box collision.

**Properties:**
- Dimensions: Half-extents (X, Y, Z)
- Material: Surface type (stone, wood, flesh, etc.)

**Use cases:** Crates, walls, furniture

#### bhkSphereShape
Spherical collision.

**Properties:**
- Radius: Distance from center
- Material: Surface type

**Use cases:** Balls, heads, simple round objects

#### bhkCapsuleShape
Cylinder with hemispherical ends (pill shape).

**Properties:**
- Point 1, Point 2: Endpoints of central axis
- Radius 1, Radius 2: Radii at each end (usually same)
- Material: Surface type

**Use cases:** Arms, legs, tails, rope, staves

#### bhkConvexVerticesShape
Convex hull defined by vertices.

**Properties:**
- Vertices: List of 3D points
- Normals: Surface normals
- Material: Surface type

**Constraints:**
- Must be **convex** (no indentations)
- Max 255 vertices (practical limit ~64 for performance)

**Use cases:** Simple organic shapes, rocks

#### bhkMoppBvTreeShape
Mesh collision using Memory-Optimized Partial Polytope Bounding Volume Tree.

**Structure:**
- Contains multiple sub-shapes (triangles)
- Pre-computed acceleration structure for fast collision queries

**Use cases:** Complex static meshes (architecture, terrain)

**Warning:** Expensive for moving objects - use simpler shapes when possible.

#### bhkListShape
Container for multiple collision shapes.

**Use cases:** Combining shapes (e.g., multiple boxes for furniture)

### Havok Materials

Material types affect friction and sound:
- HAV_MAT_STONE
- HAV_MAT_WOOD
- HAV_MAT_METAL
- HAV_MAT_FLESH
- HAV_MAT_CLOTH
- HAV_MAT_SKIN (for creatures)
- HAV_MAT_DRAGON
- (many more...)

Each material has default friction/restitution values.

### Fallout 4 Physics

FO4 uses Havok packfile format (hkpPhysicsSystem) instead of individual blocks.

**Key differences:**
- Physics data stored in bhkPhysicsSystem block
- Properties use float16 (truncated precision)
- bhkNPCollisionObject instead of bhkCollisionObject
- Collision shapes encoded in packfile

**Common issue:** FO4 collision is more finicky to edit - prefer using Creation Kit's Havok export or copying from working examples.

## HDT-SMP (Skinned Mesh Physics)

### Overview

`[Skyrim]` HDT-SMP (Skinned Mesh Physics) adds dynamic cloth/hair/tail physics using external XML configuration files. The system simulates bones as spring-connected masses that respond to movement and collisions. There is no equivalent in Fallout 4.

**SKSE Plugin:** HDT-SMP.dll (required at runtime)  
**Config location:** `Data/SKSE/Plugins/hdtSkinnedMeshConfigs/*.xml`  
**Mesh markers:** NiStringExtraData "HDT" in NIF points to XML config

**Use cases:**
- Hair
- Capes, cloaks, scarves
- Tails
- Breast/butt physics
- Dangling accessories

### XML Configuration Structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<system>
    <!-- Collision meshes MUST come first -->
    <per-triangle-shape name="VirtualGround">
        <margin>5</margin>
        <prenetration>1</prenetration>
        <tag>ground</tag>
    </per-triangle-shape>
    
    <!-- Bone definitions -->
    <bone name="TailBone01">
        <inertia x="0" y="0" z="0"/>
        <mass>5</mass>
        <linearDamping>0.5</linearDamping>
        <angularDamping>0.5</angularDamping>
        <gravityFactor>1</gravityFactor>
        
        <!-- Bone collision shape -->
        <capsule-shape>
            <margin>5</margin>
            <radius>2</radius>
            <length>15</length>
        </capsule-shape>
        
        <!-- Constraints -->
        <constraint>
            <stiffness>10</stiffness>
            <maxAngle>45</maxAngle>
        </constraint>
    </bone>
    
    <!-- More bones... -->
</system>
```

### Critical: Collision Mesh Order

**BLOCKING REQUIREMENT:** `<per-triangle-shape>` collision meshes **MUST** be defined **BEFORE** any `<bone>` elements.

**Wrong (causes collision failure):**
```xml
<system>
    <bone name="TailBone01">...</bone>  <!-- Defined first -->
    <per-triangle-shape name="VirtualGround">...</per-triangle-shape>  <!-- Too late! -->
</system>
```

**Correct:**
```xml
<system>
    <per-triangle-shape name="VirtualGround">...</per-triangle-shape>  <!-- First! -->
    <bone name="TailBone01">...</bone>  <!-- After collision -->
</system>
```

**Symptom if wrong:** Physics bones clip through ground despite correct mesh geometry.

### Per-Triangle Collision

Defines collision meshes that physics bones interact with.

#### VirtualGround
Prevents physics from clipping through the ground.

**Configuration:**
```xml
<per-triangle-shape name="VirtualGround">
    <margin>5</margin>
    <prenetration>1</prenetration>
    <tag>ground</tag>
</per-triangle-shape>
```

**Requirements:**
- Must be NiTriShape named "VirtualGround" in NIF
- Weighted to `NPC Root [Root]` bone
- Horizontal plane at character's feet

**Properties:**
- `margin` - Collision boundary thickness (5 = default)
- `prenetration` - How much to push back when penetrating (1 = default)
- `tag` - Identifier (use "ground" for floor collision)

**Known issue:** VirtualGround rotates with NPC Root during ragdoll, which can affect nearby living characters.

#### BodyCollision
Defines collision with body mesh for cloaks/clothing.

**Configuration:**
```xml
<per-triangle-shape name="BodyCollision">
    <margin>3</margin>
    <prenetration>0.5</prenetration>
</per-triangle-shape>
```

**Requirements:**
- NiTriShape in NIF (simplified body mesh)
- Lower poly than render mesh for performance

### Bone Configuration

Each physics bone needs:

#### Physical Properties

**Mass:**
```xml
<mass>5</mass>
```
- Higher = harder to move, more momentum
- Typical: 1-10 (hair lighter, tails heavier)

**Damping:**
```xml
<linearDamping>0.5</linearDamping>
<angularDamping>0.5</angularDamping>
```
- Controls how quickly movement slows down
- Higher = stops faster, less swing
- Range: 0.0-1.0
- Typical: 0.3-0.7

**Gravity:**
```xml
<gravityFactor>1</gravityFactor>
```
- Multiplier for gravity effect
- 1 = normal gravity, 0 = weightless, 2 = double gravity

**Inertia:**
```xml
<inertia x="0" y="0" z="0"/>
```
- Resistance to rotation on each axis
- Usually leave at 0 for automatic calculation

#### Collision Shape

Each bone needs a collision shape to interact with world and other bones.

**Capsule (most common):**
```xml
<capsule-shape>
    <margin>5</margin>
    <radius>2</radius>
    <length>15</length>
</capsule-shape>
```
- Cylinder with rounded ends
- Good for hair strands, tails, rope

**Sphere:**
```xml
<sphere-shape>
    <margin>5</margin>
    <radius>5</radius>
</sphere-shape>
```
- Ball shape
- Good for beads, joints, simple shapes

**Box:**
```xml
<box-shape>
    <margin>5</margin>
    <halfExtents x="5" y="5" z="5"/>
</box-shape>
```
- Rectangular box
- Good for flat cloth panels

**Margin:** Collision padding in game units. Larger = more conservative collisions.

#### Constraints

Constraints limit how bones can rotate relative to their parent.

**Basic constraint:**
```xml
<constraint>
    <stiffness>10</stiffness>
    <maxAngle>45</maxAngle>
</constraint>
```

**Stiffness:**
- How strongly bone resists bending
- Higher = stiffer, less flexible
- Range: 0-100+
- Typical: 5-20 (hair), 10-40 (tails), 50+ (rigid cloth)

**MaxAngle:**
- Maximum angle bone can bend from rest position (degrees)
- Smaller = more restricted movement
- Typical: 30-60 degrees

**Cone constraint (advanced):**
```xml
<constraint>
    <stiffness>10</stiffness>
    <coneAngle>30</coneAngle>
    <twistAngle>15</twistAngle>
</constraint>
```
- `coneAngle` - Side-to-side bend limit
- `twistAngle` - Rotation around bone axis

### Mesh Weight Requirements

**Critical for tails:** Root tail bone (e.g., TailBone01) should **NOT** be weighted to any tail bones in the mesh. Weighting should skip the first physics bone.

**Example weighting (female feline tail):**
- Tail root mesh → Weighted to NPC Pelvis [Pelv] or NPC Spine2 [Spn2]
- Mid-tail mesh → Weighted to TailBone02, TailBone03, etc.
- **NOT** → TailBone01 (first physics bone stays unweighted)

**Reason:** Prevents fighting between skeleton animation and physics simulation.

### Common Configurations

#### Hair Physics
```xml
<bone name="HairBone01">
    <mass>1</mass>
    <linearDamping>0.5</linearDamping>
    <angularDamping>0.5</angularDamping>
    <gravityFactor>0.8</gravityFactor>
    
    <capsule-shape>
        <margin>3</margin>
        <radius>1</radius>
        <length>10</length>
    </capsule-shape>
    
    <constraint>
        <stiffness>5</stiffness>
        <maxAngle>45</maxAngle>
    </constraint>
</bone>
```

**Key values:**
- Light mass (1)
- Moderate damping (0.5)
- Slightly reduced gravity (0.8)
- Flexible stiffness (5)

#### Tail Physics
```xml
<bone name="TailBone02">
    <mass>5</mass>
    <linearDamping>0.3</linearDamping>
    <angularDamping>0.3</angularDamping>
    <gravityFactor>1</gravityFactor>
    
    <capsule-shape>
        <margin>5</margin>
        <radius>3</radius>
        <length>20</length>
    </capsule-shape>
    
    <constraint>
        <stiffness>15</stiffness>
        <maxAngle>40</maxAngle>
    </constraint>
</bone>
```

**Key values:**
- Heavier mass (5)
- Lower damping for more swing (0.3)
- Normal gravity (1.0)
- Moderate stiffness (15)

#### Cape/Cloak Physics
```xml
<bone name="CapeBone01">
    <mass>3</mass>
    <linearDamping>0.6</linearDamping>
    <angularDamping>0.6</angularDamping>
    <gravityFactor>1</gravityFactor>
    
    <box-shape>
        <margin>5</margin>
        <halfExtents x="10" y="2" z="15"/>
    </box-shape>
    
    <constraint>
        <stiffness>20</stiffness>
        <maxAngle>35</maxAngle>
    </constraint>
</bone>
```

**Key values:**
- Moderate mass (3)
- Higher damping for cloth behavior (0.6)
- Box shape for flat panels
- Higher stiffness (20)

### NIF Requirements

For HDT-SMP to work, the NIF must have:

1. **NiStringExtraData "HDT"**
   - Attached to scene root or skeleton root
   - String value: Path to XML config (e.g., "hdtSkinnedMeshConfigs/MyTail.xml")

2. **Physics bones in skeleton**
   - Bones referenced in XML must exist as NiNode in NIF
   - Proper parent-child hierarchy

3. **Mesh skinned to physics bones**
   - Vertices weighted to physics bones
   - Max 4 bones per vertex

4. **Collision meshes (if used)**
   - VirtualGround: NiTriShape at ground level
   - BodyCollision: Simplified body mesh

### Debugging Physics Issues

**Symptoms:** Physics not working, clipping through ground, jittery movement

**Checklist:**
1. ✅ HDT-SMP.dll installed and enabled
2. ✅ XML config in correct location
3. ✅ NIF has NiStringExtraData "HDT" pointing to XML
4. ✅ Collision meshes defined **before** bones in XML
5. ✅ `<prenetration>` spelled correctly (not "penetration")
6. ✅ Bone names in XML match bone names in NIF exactly
7. ✅ VirtualGround mesh exists and is named correctly
8. ✅ VirtualGround weighted to NPC Root [Root]
9. ✅ Physics bones exist in skeleton hierarchy
10. ✅ Mesh vertices actually weighted to physics bones

**Common mistakes:**
- Defining collision meshes after bones → Move to top of XML
- Using `<penetration>` instead of `<prenetration>` → Fix tag name
- Misspelled bone names → Check exact capitalization and spacing
- VirtualGround not weighted → Paint weights to NPC Root [Root]
- FSMP MCM auto-reset causing crashes → Disable FSMP MCM

See [Physics Issues Debugging](../debugging/physics-issues.md) [TBD] for more troubleshooting.

## Tools

**NifSkope:** View/edit Havok collision blocks in NIFs

**PyNifly:** Export NIFs with collision from Blender
```python
from pyn import pynifly

nif = pynifly.NifFile('mesh.nif')
# Check for collision
for node in nif.nodes.values():
    if 'bhk' in node.blockname:
        print(f"Collision block: {node.blockname}")
```

**Creation Kit:** Generate Havok collision for objects (PhysX → Havok export)

**HDT-SMP Visualizer:** In-game debug mode (shows collision shapes, bone connections)

**SSEEdit/FO4Edit:** Check FormID references to physics-enabled meshes in plugins

## See Also

- [NIF Files](nif-files.md) - bhkCollisionObject and physics block structure
- [Mesh Workflows](../workflows/physics-collisions.md) [TBD] - Setting up physics in Blender
- [Physics Debugging](../debugging/physics-issues.md) [TBD] - Troubleshooting collision issues
