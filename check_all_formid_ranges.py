import struct
from pathlib import Path

data_dir = Path(r"C:\Steam\steamapps\common\Skyrim Special Edition\Data")

# Check master files
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
        'formid': rec_formid
    }

for filename in files_to_check:
    filepath = data_dir / filename
    if not filepath.exists():
        print(f"Skipping {filename} (not found)")
        continue
    
    print(f"\n{'='*60}")
    print(f"{filename}")
    print(f"{'='*60}")
    
    # Track FormIDs by bottom 12 bits
    low_range = []   # Bottom 12 bits in 0x000-0x7FF
    high_range = []  # Bottom 12 bits in 0x800-0xFFF
    
    with open(filepath, 'rb') as f:
        # Read TES4 header
        tes4 = read_record_header(f)
        
        # Skip TES4 data
        f.seek(24 + tes4['size'])
        
        # Scan records
        count = 0
        max_records = 1000  # Check first 1000 records
        
        while count < max_records:
            rec = read_record_header(f)
            if not rec:
                break
            
            # Skip group headers
            if rec['type'] == 'GRUP':
                if rec['size'] > 24:
                    f.seek(rec['size'] - 24, 1)
                count += 1
                continue
            
            formid = rec['formid']
            
            # Look at bottom 12 bits (like ESL local ID)
            local_12bit = formid & 0xFFF
            
            if local_12bit < 0x800:
                low_range.append((formid, local_12bit))
            else:
                high_range.append((formid, local_12bit))
            
            # Skip record data
            if rec['size'] > 0:
                f.seek(rec['size'], 1)
            
            count += 1
    
    print(f"Scanned {count} records")
    print(f"  Bottom 12 bits in 0x000-0x7FF: {len(low_range)}")
    print(f"  Bottom 12 bits in 0x800-0xFFF: {len(high_range)}")
    
    if low_range:
        print(f"\nFirst 5 with LOW range (0x000-0x7FF) in bottom 12 bits:")
        for formid, local in low_range[:5]:
            print(f"  FormID: 0x{formid:08X}, bottom 12 bits: 0x{local:03X}")
    
    if high_range:
        print(f"\nFirst 5 with HIGH range (0x800-0xFFF) in bottom 12 bits:")
        for formid, local in high_range[:5]:
            print(f"  FormID: 0x{formid:08X}, bottom 12 bits: 0x{local:03X}")

print("\n" + "="*60)
print("Analysis complete")
