import struct
from pathlib import Path

data_dir = Path(r"C:\Steam\steamapps\common\Skyrim Special Edition\Data")

# Check actual ESL files
files_to_check = [
    "ccBGSSSE037-Curios.esl",
    "ccQDRSSE001-SurvivalMode.esl",
    "_ResourcePack.esl"
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
    
    with open(filepath, 'rb') as f:
        # Read TES4 header
        tes4 = read_record_header(f)
        print(f"TES4 Flags: 0x{tes4['flags']:08X}")
        is_esl = (tes4['flags'] & 0x00000200) != 0
        print(f"ESL-flagged: {is_esl}")
        
        # Skip TES4 data
        f.seek(24 + tes4['size'])
        
        # Track records by FormID
        formids_by_range = {
            'regular': [],
            'esl_low': [],   # 0xFE???000-0xFE???7FF
            'esl_high': []   # 0xFE???800-0xFE???FFF
        }
        
        # Scan all records
        count = 0
        while count < 500:  # Limit to avoid hanging
            rec = read_record_header(f)
            if not rec or rec['type'] in ['GRUP']:
                if rec:
                    f.seek(rec['size'] - 24, 1)  # Skip group
                count += 1
                continue
            
            formid = rec['formid']
            
            # Categorize FormID
            if (formid >> 24) == 0xFE:
                local_id = formid & 0xFFF
                if local_id < 0x800:
                    formids_by_range['esl_low'].append(formid)
                else:
                    formids_by_range['esl_high'].append(formid)
            else:
                formids_by_range['regular'].append(formid)
            
            # Skip record data
            if rec['size'] > 0:
                f.seek(rec['size'], 1)
            
            count += 1
        
        # Print summary
        print(f"\nFormID distribution (scanned {count} records):")
        print(f"  Regular FormIDs: {len(formids_by_range['regular'])}")
        print(f"  ESL Low range (0x000-0x7FF): {len(formids_by_range['esl_low'])}")
        print(f"  ESL High range (0x800-0xFFF): {len(formids_by_range['esl_high'])}")
        
        if formids_by_range['esl_low']:
            print(f"\n  First 5 LOW range FormIDs:")
            for fid in formids_by_range['esl_low'][:5]:
                local = fid & 0xFFF
                print(f"    0x{fid:08X} (local: 0x{local:03X})")
        
        if formids_by_range['esl_high']:
            print(f"\n  First 5 HIGH range FormIDs:")
            for fid in formids_by_range['esl_high'][:5]:
                local = fid & 0xFFF
                print(f"    0x{fid:08X} (local: 0x{local:03X})")

print("\n" + "="*60)
