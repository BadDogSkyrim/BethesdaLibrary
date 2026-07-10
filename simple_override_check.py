import struct
from pathlib import Path

data_dir = Path(r"C:\Steam\steamapps\common\Skyrim Special Edition\Data")

# Pick a small ESP that likely has overrides
esp_file = data_dir / "BaboYgnordPatch.esp"

print(f"Examining: {esp_file.name}")
print("="*70)

with open(esp_file, 'rb') as f:
    # Skip TES4
    f.read(4)  # TES4
    tes4_size = struct.unpack('I', f.read(4))[0]
    f.read(16)
    f.seek(24 + tes4_size)
    
    # Read first 20 records/groups
    found_overrides = 0
    while found_overrides < 5:
        pos = f.tell()
        type_bytes = f.read(4)
        if len(type_bytes) < 4:
            break
        
        rec_type = type_bytes.decode('ascii', errors='ignore')
        rec_size = struct.unpack('I', f.read(4))[0]
        rec_flags = struct.unpack('I', f.read(4))[0]
        rec_formid = struct.unpack('I', f.read(4))[0]
        f.read(12)
        
        if rec_type == 'GRUP':
            #print(f"\nGRUP at 0x{pos:08X}, size={rec_size}")
            # Skip to content of group (24 bytes past start)
            f.seek(pos + 24)
            continue
        
        # Check master index
        master_idx = (rec_formid >> 24) & 0xFF
        
        if master_idx > 0:  # This is an override
            found_overrides += 1
            print(f"\n{rec_type} at 0x{pos:08X}")
            print(f"  FormID: 0x{rec_formid:08X} (master index={master_idx})")
            print(f"  Flags: 0x{rec_flags:08X}")
            print(f"  Data size: {rec_size} bytes")
            
            # Read all subrecords
            print(f"  Subrecords:")
            data_start = f.tell()
            bytes_read = 0
            sub_count = 0
            while bytes_read < rec_size:
                if rec_size - bytes_read < 6:
                    break
                
                sub_type_bytes = f.read(4)
                if len(sub_type_bytes) < 4:
                    break
                sub_type = sub_type_bytes.decode('ascii', errors='ignore')
                
                sub_size_bytes = f.read(2)
                if len(sub_size_bytes) < 2:
                    break
                sub_size = struct.unpack('H', sub_size_bytes)[0]
                
                if bytes_read + 6 + sub_size > rec_size:
                    break
                
                f.read(sub_size)  # Skip data
                print(f"    {sub_type}: {sub_size} bytes")
                bytes_read += 6 + sub_size
                sub_count += 1
            
            print(f"  Total subrecords: {sub_count}")
            # Seek to end of record
            f.seek(data_start + rec_size)
        else:
            f.seek(rec_size, 1)

print("\n" + "="*70)
