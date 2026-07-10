import struct
import os
from pathlib import Path

data_dir = Path(r"C:\Steam\steamapps\common\Skyrim Special Edition\Data")

# Check Skyrim.esm and DLCs
files_to_check = [
    "Skyrim.esm",
    "Update.esm",
    "Dawnguard.esm",
    "HearthFires.esm",
    "Dragonborn.esm"
]

def read_record_header(f):
    """Read a 24-byte record header"""
    rec_type = f.read(4)
    if len(rec_type) < 4:
        return None
    rec_type = rec_type.decode('ascii', errors='ignore')
    rec_size = struct.unpack('I', f.read(4))[0]
    rec_flags = struct.unpack('I', f.read(4))[0]
    rec_formid = struct.unpack('I', f.read(4))[0]
    rec_revision = struct.unpack('I', f.read(4))[0]
    rec_version = struct.unpack('H', f.read(2))[0]
    rec_unknown = struct.unpack('H', f.read(2))[0]
    
    return {
        'type': rec_type,
        'size': rec_size,
        'flags': rec_flags,
        'formid': rec_formid,
        'revision': rec_revision,
        'version': rec_version
    }

for filename in files_to_check:
    filepath = data_dir / filename
    if not filepath.exists():
        print(f"Skipping {filename} (not found)")
        continue
    
    print(f"\n{'='*60}")
    print(f"Checking: {filename}")
    print(f"{'='*60}")
    
    with open(filepath, 'rb') as f:
        # Read TES4 header first
        tes4 = read_record_header(f)
        if tes4['type'] != 'TES4':
            print(f"ERROR: Not a valid plugin (no TES4 header)")
            continue
        
        print(f"TES4 Flags: 0x{tes4['flags']:08X}")
        is_esl = (tes4['flags'] & 0x00000200) != 0
        print(f"ESL-flagged: {is_esl}")
        
        # Skip TES4 data
        f.seek(24 + tes4['size'])
        
        # Track ESL FormID ranges
        esl_formids = []
        low_range_count = 0  # 0xFE???000-0xFE???7FF
        high_range_count = 0  # 0xFE???800-0xFE???FFF
        
        # Scan first 100 records
        for i in range(100):
            rec = read_record_header(f)
            if not rec:
                break
            
            formid = rec['formid']
            
            # Check if it's an ESL FormID (0xFE??????)
            if (formid >> 24) == 0xFE:
                esl_formids.append(formid)
                local_id = formid & 0xFFF  # Bottom 12 bits
                
                if local_id < 0x800:
                    low_range_count += 1
                    if low_range_count <= 5:  # Show first few
                        print(f"  Found ESL FormID in LOW range: 0x{formid:08X} (local: 0x{local_id:03X})")
                else:
                    high_range_count += 1
            
            # Skip record data
            if rec['size'] > 0:
                f.seek(rec['size'], 1)
        
        if esl_formids:
            print(f"\nESL FormIDs found: {len(esl_formids)}")
            print(f"  Low range (0x000-0x7FF): {low_range_count}")
            print(f"  High range (0x800-0xFFF): {high_range_count}")
        else:
            print("No ESL FormIDs found in first 100 records")

print("\n" + "="*60)
print("Analysis complete")
