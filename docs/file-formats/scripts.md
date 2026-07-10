# Scripts (PEX Files)

PEX (Papyrus Executable) files are compiled Papyrus scripts that control game logic and behavior.

## Overview

**Extension:** `.pex`  
**Format:** Compiled binary (from `.psc` source)  
**Language:** Papyrus scripting language  
**Location:** `Data/Scripts/`

**Purpose:**
- Game logic (quests, mechanics)
- Object behavior (doors, traps, activators)
- NPC AI extensions
- Spell/ability effects
- Custom systems

**Games:** Skyrim LE/SE, Fallout 4, Fallout 76, Starfield

## Papyrus Overview

**Papyrus:** Object-oriented scripting language for Bethesda games.

**Features:**
- Event-driven (OnActivate, OnUpdate, OnHit, etc.)
- State machines
- Native functions (game engine integration)
- Properties (exposed to Creation Kit)
- Type system (int, float, bool, string, Object references)

**Not included in this library:** Full Papyrus language reference. See official Creation Kit wiki for language details.

**Focus here:** PEX format, VMAD record structure, debugging.

## Source vs. Compiled

### PSC (Source)

**Extension:** `.psc`  
**Format:** Plain text  
**Editable:** Yes (any text editor)

**Location (source):** Not distributed with game - create yourself or extract from CK.

**Example:**
```papyrus
Scriptname MyCustomScript extends ObjectReference

; Properties (set in Creation Kit)
Int Property MyValue Auto
Actor Property PlayerRef Auto

; Event handler
Event OnActivate(ObjectReference akActionRef)
    if akActionRef == PlayerRef
        Debug.Notification("Player activated me!")
        MyValue += 1
    endif
EndEvent
```

### PEX (Compiled)

**Extension:** `.pex`  
**Format:** Binary bytecode  
**Editable:** No (must decompile to PSC, edit, recompile)

**Location:** `Data/Scripts/*.pex`

**Compilation:** Creation Kit Papyrus Compiler or command-line compiler.

## PEX File Structure

```
PEX File
├── Header
│   ├── Magic bytes (0xFA57C0DE)
│   ├── Compiler version
│   ├── Game ID
│   ├── Time compiled
│   └── Source filename
├── String Table
│   └── All strings used in script
├── Debug Info (optional)
│   ├── Function line numbers
│   └── Local variable names
├── User Flags
│   └── Custom flags
├── Objects (classes)
│   ├── Object name
│   ├── Parent object (extends)
│   ├── Properties
│   ├── Variables
│   ├── States
│   └── Functions
│       ├── Function name
│       ├── Return type
│       ├── Parameters
│       ├── Locals
│       └── Bytecode instructions
└── (repeat for each object)
```

## VMAD (Plugin Integration)

**VMAD:** Virtual Machine Adapter - embeds scripts in plugin records.

**Location:** Subrecord in ESP/ESM records (QUST, REFR, ACTI, etc.).

**Structure:**
```
VMAD subrecord
├── Version
├── Object format
├── Scripts (array)
│   ├── Script name (references PEX)
│   ├── Flags
│   └── Properties (array)
│       ├── Property name
│       ├── Property type
│       ├── Property status
│       └── Property value (FormID, int, float, string, etc.)
└── (repeat for each script)
```

**Example (pseudo-structure):**
```
ObjectReference "MyDoor"
  VMAD:
    Script: "MyCustomDoorScript"
      Property: "IsLocked" (bool) = True
      Property: "KeyRequired" (FormID) = 0x00012345
    Script: "DefaultOpenDoorScript"  
      Property: "OpenSound" (FormID) = 0x00098765
```

## Property Types

**Simple types:**
- **Bool:** true/false
- **Int:** 32-bit integer
- **Float:** 32-bit float
- **String:** Text

**Reference types:**
- **Object:** Any game object (FormID reference)
- **Actor:** NPC/creature (FormID)
- **ObjectReference:** Placed object (FormID)
- **Form:** Any form (FormID)
- **Specific types:** Weapon, Armor, Spell, etc. (FormID)

**Array types:**
- **Int[]**, **Float[]**, **Bool[]**, **String[]**
- **Object[]**, **Actor[]**, etc.

**Property flags:**
- **Auto:** Auto-variable (no separate variable needed)
- **AutoReadOnly:** Read-only auto property
- **Conditional:** Property only active if condition met

## Compiling Scripts

### Creation Kit Compiler

**Built-in compiler** (GUI).

**Workflow:**
1. Write `.psc` file
2. Place in `Data/Scripts/Source/`
3. **Creation Kit → Gameplay → Papyrus Script Manager**
4. Select script
5. **Compile**
6. Output: `Data/Scripts/<scriptname>.pex`

**Limitations:**
- Slow for batch compilation
- No command-line options
- Requires full CK load

### Command-line Compiler

**Faster batch compilation.**

**Location:** `<CK Path>/Papyrus Compiler/PapyrusCompiler.exe`

**Usage:**
```powershell
PapyrusCompiler.exe "MyScript.psc" -i="C:\Path\To\Scripts\Source" -o="C:\Output\Scripts" -f="TESV_Papyrus_Flags.flg"
```

**Flags:**
- `-i=<path>` - Import directories (source script folders)
- `-o=<path>` - Output directory (where PEX goes)
- `-f=<file>` - Flag file (defines compiler behavior)
- `-a` - Compile all scripts in directory

**Batch compile:**
```powershell
PapyrusCompiler.exe "C:\MyScripts\Source" -i="C:\SourceDir" -o="C:\MyScripts\Output" -a
```

### Caprica Compiler (Community)

**Faster, more modern compiler** (compatible with PapyrusCompiler).

**Features:**
- Much faster compilation
- Better error messages
- Cross-platform (Windows, Linux, Mac)
- Supports Skyrim, FO4, Starfield

**Usage:** Same as PapyrusCompiler.exe (drop-in replacement).

## Decompiling Scripts

**PEX files can be decompiled** to recover source (with some loss).

### Champollion

**PEX decompiler.**

**Usage:**
```powershell
Champollion.exe "MyScript.pex" -o "Output"
```

**Output:** `MyScript.psc` (reconstructed source)

**Limitations:**
- Comments lost
- Variable names may be generic (var1, var2) if debug info missing
- Some complex expressions simplified

**Use case:** Understanding vanilla scripts, recovering lost source.

### Legal Note

**Vanilla scripts:** Decompiling for learning is fine. Don't redistribute Bethesda's source code.

**Mod scripts:** Respect mod author licenses. Some forbid decompilation.

## Debugging Scripts

### Papyrus Logs

**Log location:**
- **Skyrim LE/SE:** `Documents/My Games/Skyrim/Logs/Script/Papyrus.0.log`
- **Fallout 4:** `Documents/My Games/Fallout4/Logs/Script/Papyrus.0.log`

**Enable logging (Skyrim.ini / Fallout4.ini):**
```ini
[Papyrus]
bEnableLogging=1
bEnableTrace=1
bLoadDebugInformation=1
```

**Log content:**
- Script compilation errors
- Runtime errors (null references, type mismatches)
- Debug.Trace() output
- Stack dumps

### Debug Functions

**In scripts:**

```papyrus
; Print to log
Debug.Trace("MyScript: Variable value = " + MyVar)

; Show in-game notification
Debug.Notification("Quest started!")

; Show message box
Debug.MessageBox("Are you sure?")

; Assertions
Debug.Assert(PlayerRef != None, "PlayerRef is None!")
```

### Common Errors

**None/Null reference:**
```
ERROR: Cannot call <function> on a None object
```
- **Cause:** Property not filled or object deleted
- **Fix:** Check property values in Creation Kit, verify object exists

**Type mismatch:**
```
ERROR: Cannot cast a <TypeA> to a <TypeB>
```
- **Cause:** Wrong type passed to function/property
- **Fix:** Check types, cast explicitly if needed

**Stack overflow:**
```
ERROR: Stack dump: (stack dump follows)
```
- **Cause:** Infinite loop or excessive recursion
- **Fix:** Check event loops, avoid infinite RegisterForUpdate

**Suspended stack:**
```
WARNING: Saving a suspended stack. <script>.<function>
```
- **Cause:** Script in middle of execution during save (Latent functions)
- **Usually harmless**, but can indicate slow script

## Performance Tips

**Avoid OnUpdate spam:**
```papyrus
; Bad - runs every frame
Event OnUpdate()
    ; Do something
    RegisterForSingleUpdate(0.01)  ; BAD: Too fast
EndEvent

; Good - runs occasionally
Event OnUpdate()
    ; Do something
    RegisterForSingleUpdate(5.0)  ; GOOD: Every 5 seconds
EndEvent
```

**Use OnUpdateGameTime for slow checks:**
```papyrus
; Runs on game time (not real time) - more efficient for non-urgent tasks
Event OnUpdateGameTime()
    ; Check something
    RegisterForSingleUpdateGameTime(2.0)  ; Every 2 game hours
EndEvent
```

**Unregister when done:**
```papyrus
; Stop updates when no longer needed
UnregisterForUpdate()
UnregisterForUpdateGameTime()
```

**Cache references:**
```papyrus
; Bad - searches every time
Event OnUpdate()
    Game.GetPlayer().AddItem(Gold001, 10)  ; Expensive lookup
EndEvent

; Good - cache once
Actor Property PlayerRef Auto  ; Set in CK

Event OnUpdate()
    PlayerRef.AddItem(Gold001, 10)  ; Fast property access
EndEvent
```

**Avoid Latent functions in tight loops:**
```papyrus
; Latent functions suspend execution (Utility.Wait, ObjectReference.MoveTo, etc.)
; Avoid calling repeatedly
```

## Game-Specific Differences

### Skyrim LE/SE

**Papyrus version:** 2.0

**Key systems:**
- Quest stages and objectives
- Scene dialogue
- Magic effects
- ActiveMagicEffect scripts
- Alias scripts (quest aliases)

**SKSE:** Skyrim Script Extender adds 100+ functions (F4SE for FO4).

**Common scripts:**
- `Actor.psc` - NPC/creature behavior
- `ObjectReference.psc` - Placed object base
- `Quest.psc` - Quest control
- `ActiveMagicEffect.psc` - Spell effects

### Fallout 4

**Papyrus version:** 2.1

**Key systems:**
- Workshop system
- Companion affinity
- Settlement management
- Weapon/armor mods (OMODs)

**F4SE:** Fallout 4 Script Extender (similar to SKSE).

**New base scripts:**
- `WorkshopFramework:MainQuest`
- `WorkshopParentScript`

**Differences from Skyrim:**
- Struct types (custom data structures)
- var keyword (type inference)
- CustomEvent system

## Distribution

**Include PEX only:** Distribute compiled `.pex` files in `Data/Scripts/`.

**Optional source:** Include `.psc` in `Data/Scripts/Source/` for other modders.

**VMAD in plugin:** Scripts attached to records travel with ESP/ESM.

**Loose vs. BSA:** PEX files can go in BSA or loose (loose overrides BSA).

## Common Issues

### Script Not Running
- **PEX not installed:** File missing from Data/Scripts/
- **Not attached:** Script not in VMAD record
- **Property not filled:** Required property empty (causes script suspension)
- **Fix:** Install PEX, attach script in CK, fill properties

### Property "X" Not Found
- **Version mismatch:** Script recompiled with different properties, save has old version
- **Missing master:** Script references plugin that's not loaded
- **Fix:** Clean save (remove script, save, re-add) or regenerate properties

### Compile Error
- **Syntax error:** Check line number in error message
- **Missing import:** Script extends unknown base (missing source)
- **Wrong compiler version:** Using FO4 compiler for Skyrim (or vice versa)
- **Fix:** Fix syntax, add import paths, use correct compiler

### Performance Issues
- **Update spam:** OnUpdate with short interval
- **Infinite loops:** Script stuck in While loop
- **Too many scripts:** Hundreds of scripts running simultaneously
- **Fix:** Increase update interval, add loop breaks, disable unused scripts

## Tools

**Creation Kit:** Built-in script editor and compiler.

**Papyrus Compiler:** Command-line compiler (ships with CK).

**Caprica:** Modern faster compiler (community, drop-in replacement).

**Champollion:** Decompiler (PEX → PSC).

**Sublime Text + Papyrus plugin:** Syntax highlighting, autocomplete.

**VSCode + Papyrus extension:** IDE features for Papyrus.

**SSEEdit/FO4Edit:** View VMAD records in plugins.

## See Also

- [Plugin Files](plugins.md) - VMAD subrecords
- [Creation Kit](../tools/other-tools.md#creation-kit) [TBD] - Script editor
- [Debugging Scripts](../debugging/plugin-issues.md#script-errors) [TBD] - Troubleshooting Papyrus errors
- [Plugin Workflows](../workflows/plugin-editing.md) [TBD] - Attaching scripts to records
