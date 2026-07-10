import struct
from pathlib import Path
import zlib

data_dir = Path(r"C:\Steam\steamapps\common\Skyrim Special Edition\Data")

def read_record_recursive(f, end_pos, depth=0):
    """Recursively read records and groups"""
    results = []
    
    while f.tell() < end_pos:
        start_pos = f.tell()
        if start_pos + 24 > end_pos:
            break
        
        # Read header
        type_bytes = f.read(4)
        if len(type_bytes) < 4:
            break
        rec_type = type_bytes.decode('ascii', errors='ignore')
        rec_size = struct.unpack('I', f.read(4))[0]
        rec_flags = struct.unpack('I', f.read(4))[0]
        rec_formid = struct.unpack('I', f.read(4))[0]
        f.read(12)
        
        if rec_type == 'GRUP':
            # Recursively read group contents
            group_end = start_pos + rec_size
            results.extend(read_record_recursive(f, group_end, depth + 1))
        else:
            # Actual record
            master_idx = (rec_formid >> 24) & 0xFF
            if master_idx > 0:  # Override record
                # Read subrecords
                data_start = f.tell()
                record_data = f.read(rec_size)
                
                # Check if compressed
                if rec_flags & 0x00040000:
                    # Decompress
                    decompressed_size = struct.unpack('I', record_data[:4])[0]
                    record_data = zlib.decompress(record_data[4:])
                
                # Parse subrecords
                subrecords = []
                offset = 0
                while offset + 6 <= len(record_data):
                    sub_type = record_data[offset:offset+4].decode('ascii', errors='replace')
                    sub_size = struct.unpack('H', record_data[offset+4:offset+6])[0]
                    if offset + 6 + sub_size > len(record_data):
                        break
                    subrecords.append((sub_type, sub_size))
                    offset += 6 + sub_size
                
                results.append({
                    'type': rec_type,
                    'formid': rec_formid,
                    'master_idx': master_idx,
                    'flags': rec_flags,
                    'size': rec_size,
                    'subrecords': subrecords
                })
                
                if len(results) >= 10:  # Stop after finding 10
                    return results
            else:
                # Skip new record
                f.seek(rec_size, 1)
    
    return results

# Check Dawnguard.esm (should have overrides of Skyrim.esm)
print("Checking Dawnguard.esm for override records...")
print("="*70)

dgn_file = data_dir / "Dawnguard.esm"
if dgn_file.exists():
    with open(dgn_file, 'rb') as f:
        # Skip TES4
        f.read(4)
        tes4_size = struct.unpack('I', f.read(4))[0]
        f.read(16)
        f.seek(24 + tes4_size)
        
        # Get file size
        f.seek(0, 2)
        file_size = f.tell()
        f.seek(24 + tes4_size)
        
        overrides = read_record_recursive(f, file_size)
        
        print(f"\nFound {len(overrides)} override records\n")
        
        for i, rec in enumerate(overrides[:5], 1):
            print(f"Override #{i}: {rec['type']}")
            print(f"  FormID: 0x{rec['formid']:08X} (master={rec['master_idx']})")
            print(f"  Flags: 0x{rec['flags']:08X}")
            print(f"  Data size: {rec['size']} bytes")
            print(f"  Subrecords: {len(rec['subrecords'])}")
            for sub_type, sub_size in rec['subrecords'][:20]:
                print(f"    - {sub_type}: {sub_size} bytes")
            if len(rec['subrecords']) > 20:
                print(f"    ... and {len(rec['subrecords']) - 20} more")
            print()
else:
    print("Dawnguard.esm not found")
