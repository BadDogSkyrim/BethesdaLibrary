import struct
from pathlib import Path

data_dir = Path(r"C:\Steam\steamapps\common\Skyrim Special Edition\Data")
filepath = data_dir / "Skyrim.esm"

print("Finding actual records with FormIDs in Skyrim.esm...")
print("="*60)

def read_records_recursive(f, end_pos, depth=0):
    """Recursively read records, diving into groups"""
    records_found = []
    
    while f.tell() < end_pos:
        start_pos = f.tell()
        if start_pos >= end_pos:
            break
            
        rec_type = f.read(4)
        if len(rec_type) < 4:
            break
        rec_type = rec_type.decode('ascii', errors='ignore')
        rec_size = struct.unpack('I', f.read(4))[0]
        rec_flags = struct.unpack('I', f.read(4))[0]
        rec_formid = struct.unpack('I', f.read(4))[0]
        f.read(12)  # Skip rest of header
        
        if rec_type == 'GRUP':
            # Dive into group
            group_end = start_pos + rec_size
            records_found.extend(read_records_recursive(f, group_end, depth+1))
        else:
            # Actual record with FormID
            records_found.append({
                'type': rec_type,
                'formid': rec_formid,
                'pos': start_pos
            })
            
            # Skip record data
            if rec_size > 0:
                f.seek(rec_size, 1)
        
        if len(records_found) >= 100:  # Stop after finding 100
            break
    
    return records_found

with open(filepath, 'rb') as f:
    # Read and skip TES4 header
    f.read(4)  # TES4
    rec_size = struct.unpack('I', f.read(4))[0]
    f.read(16)  # Skip rest of header
    f.seek(24 + rec_size)  # Skip TES4 data
    
    # Get file size
    f.seek(0, 2)
    file_size = f.tell()
    f.seek(24 + rec_size)
    
    # Find records
    records = read_records_recursive(f, file_size)
    
    print(f"Found {len(records)} records\n")
    
    # Analyze FormID patterns
    low_range = []   # Bottom 12 bits in 0x000-0x7FF
    high_range = []  # Bottom 12 bits in 0x800-0xFFF
    
    for rec in records:
        formid = rec['formid']
        local_12bit = formid & 0xFFF
        
        if local_12bit < 0x800:
            low_range.append(rec)
        else:
            high_range.append(rec)
    
    print(f"Bottom 12 bits in 0x000-0x7FF: {len(low_range)}")
    print(f"Bottom 12 bits in 0x800-0xFFF: {len(high_range)}\n")
    
    if low_range:
        print("First 10 with LOW range (0x000-0x7FF):")
        for rec in low_range[:10]:
            local_12 = rec['formid'] & 0xFFF
            print(f"  {rec['type']} FormID: 0x{rec['formid']:08X} (bottom 12: 0x{local_12:03X})")
    
    if high_range:
        print("\nFirst 10 with HIGH range (0x800-0xFFF):")
        for rec in high_range[:10]:
            local_12 = rec['formid'] & 0xFFF
            print(f"  {rec['type']} FormID: 0x{rec['formid']:08X} (bottom 12: 0x{local_12:03X})")

print("\n" + "="*60)
