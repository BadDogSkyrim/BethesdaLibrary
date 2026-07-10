import struct
from pathlib import Path

data_dir = Path(r"C:\Steam\steamapps\common\Skyrim Special Edition\Data")
filepath = data_dir / "Skyrim.esm"

print("Checking first 50 actual FormIDs in Skyrim.esm...")
print("="*60)

with open(filepath, 'rb') as f:
    # Read TES4 header
    rec_type = f.read(4).decode('ascii')
    rec_size = struct.unpack('I', f.read(4))[0]
    rec_flags = struct.unpack('I', f.read(4))[0]
    rec_formid = struct.unpack('I', f.read(4))[0]
    f.read(12)  # Skip rest of header
    
    print(f"TES4 FormID: 0x{rec_formid:08X}")
    
    # Skip TES4 data
    f.seek(24 + rec_size)
    
    # Read next records
    for i in range(50):
        start_pos = f.tell()
        rec_type = f.read(4)
        if len(rec_type) < 4:
            break
        rec_type = rec_type.decode('ascii', errors='ignore')
        rec_size = struct.unpack('I', f.read(4))[0]
        rec_flags = struct.unpack('I', f.read(4))[0]
        rec_formid = struct.unpack('I', f.read(4))[0]
        f.read(12)  # Skip rest of header
        
        # Check if it's a group
        if rec_type == 'GRUP':
            print(f"{i:2}. GRUP at 0x{start_pos:08X}, size={rec_size}")
            # Skip to next
            f.seek(start_pos + rec_size)
            continue
        
        # Extract parts of FormID
        master_idx = (rec_formid >> 24) & 0xFF
        local_full = rec_formid & 0xFFFFFF
        local_12bit = rec_formid & 0xFFF
        
        print(f"{i:2}. {rec_type} FormID: 0x{rec_formid:08X} " +
              f"(master={master_idx:02X}, local_full=0x{local_full:06X}, " +
              f"local_12bit=0x{local_12bit:03X})")
        
        # Skip record data
        if rec_size > 0:
            f.seek(rec_size, 1)

print("\n" + "="*60)
