import struct
from pathlib import Path

data_dir = Path(r"C:\Steam\steamapps\common\Skyrim Special Edition\Data")

# Valid record types (partial list)
VALID_TYPES = {'ARMA', 'ARMO', 'WEAP', 'NPC_', 'CELL', 'REFR', 'ACHR', 'LVLI', 'LVLN', 
               'SPEL', 'ENCH', 'MGEF', 'PERK', 'QUST', 'DIAL', 'GMST', 'GLOB', 'KYWD',
               'FLST', 'TXST', 'MATT', 'SNDR', 'SOUN', 'ALCH', 'BOOK', 'MISC', 'AMMO',
               'KEYM', 'RACE', 'FACT', 'WRLD', 'NAVM', 'INFO', 'GRUP'}

def is_valid_record_type(type_str):
    """Check if this looks like a valid record type"""
    return type_str in VALID_TYPES or (len(type_str) == 4 and type_str.isascii())

# Try multiple ESP files
esp_files = [
    "BaboYgnordPatch.esp",
    "BadDogSchlongCore.esp",
    "alternate start - live another life.esp"
]

for esp_name in esp_files:
    esp_file = data_dir / esp_name
    if not esp_file.exists():
        print(f"SKIP: {esp_name} not found\n")
        continue
    
    print(f"\n{'='*70}")
    print(f"Examining: {esp_file.name}")
    print('='*70)
    
    with open(esp_file, 'rb') as f:
        # Skip TES4
        f.read(4)  # TES4
        tes4_size = struct.unpack('I', f.read(4))[0]
        f.read(16)
        f.seek(24 + tes4_size)
        
        found_overrides = 0
        max_iterations = 1000
        iterations = 0
        
        while found_overrides < 3 and iterations < max_iterations:
            iterations += 1
            pos = f.tell()
            
            type_bytes = f.read(4)
            if len(type_bytes) < 4:
                break
            
            rec_type = type_bytes.decode('ascii', errors='ignore')
            
            if not is_valid_record_type(rec_type):
                # Invalid, skip ahead
                f.seek(pos + 1)
                continue
            
            rec_size = struct.unpack('I', f.read(4))[0]
            rec_flags = struct.unpack('I', f.read(4))[0]
            rec_formid = struct.unpack('I', f.read(4))[0]
            f.read(12)
            
            # Sanity check on size
            if rec_size > 10000000:  # 10MB is way too big for a single record
                f.seek(pos + 1)
                continue
            
            if rec_type == 'GRUP':
                # Skip into group content
                continue
            
            # Check master index
            master_idx = (rec_formid >> 24) & 0xFF
            
            if master_idx > 0:  # This is an override
                found_overrides += 1
                print(f"\nOverride #{found_overrides}: {rec_type}")
                print(f"  FormID: 0x{rec_formid:08X} (master index={master_idx})")
                print(f"  Flags: 0x{rec_flags:08X}")
                print(f"  Data size: {rec_size} bytes")
                
                # Try to read subrecords
                data_start = f.tell()
                bytes_read = 0
                subrecords = []
                
                while bytes_read < rec_size and bytes_read < 10000:  # Safety limit
                    if rec_size - bytes_read < 6:
                        break
                    
                    sub_pos = f.tell()
                    sub_type_bytes = f.read(4)
                    if len(sub_type_bytes) < 4:
                        break
                    sub_type = sub_type_bytes.decode('ascii', errors='replace')
                    
                    sub_size_bytes = f.read(2)
                    if len(sub_size_bytes) < 2:
                        break
                    sub_size = struct.unpack('H', sub_size_bytes)[0]
                    
                    if bytes_read + 6 + sub_size > rec_size or sub_size > 50000:
                        break
                    
                    f.read(sub_size)  # Skip data
                    subrecords.append((sub_type, sub_size))
                    bytes_read += 6 + sub_size
                
                print(f"  Subrecords found: {len(subrecords)}")
                for sub_type, sub_size in subrecords[:15]:  # Show first 15
                    print(f"    - {sub_type}: {sub_size} bytes")
                if len(subrecords) > 15:
                    print(f"    ... and {len(subrecords) - 15} more")
                
                # Seek to end of record
                f.seek(data_start + rec_size)
            else:
                # Skip new record
                f.seek(rec_size, 1)
    
    if found_overrides == 0:
        print("  No override records found")

print(f"\n{'='*70}")
