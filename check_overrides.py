import struct
from pathlib import Path

data_dir = Path(r"C:\Steam\steamapps\common\Skyrim Special Edition\Data")

def read_subrecords(f, data_size):
    """Read all subrecords from record data"""
    subrecords = []
    bytes_read = 0
    
    while bytes_read < data_size:
        if data_size - bytes_read < 6:
            # Not enough space for another subrecord header
            f.seek(data_size - bytes_read, 1)  # Skip remaining bytes
            break
        
        sub_type_bytes = f.read(4)
        if len(sub_type_bytes) < 4:
            break
        sub_type = sub_type_bytes.decode('ascii', errors='ignore')
        
        sub_size_bytes = f.read(2)
        if len(sub_size_bytes) < 2:
            break
        sub_size = struct.unpack('H', sub_size_bytes)[0]
        
        # Make sure we don't read past record data
        if bytes_read + 6 + sub_size > data_size:
            break
        
        sub_data = f.read(sub_size)
        
        subrecords.append({
            'type': sub_type,
            'size': sub_size
        })
        
        bytes_read += 6 + sub_size
    
    return subrecords

def find_override_records(filepath, limit=5):
    """Find records that override masters (FormID with master index > 0)"""
    overrides = []
    
    with open(filepath, 'rb') as f:
        # Skip TES4 header
        rec_type = f.read(4).decode('ascii')
        rec_size = struct.unpack('I', f.read(4))[0]
        f.read(16)
        f.seek(24 + rec_size)
        
        # Get file size
        f.seek(0, 2)
        file_size = f.tell()
        f.seek(24 + rec_size)
        
        def scan_records(end_pos, depth=0):
            while f.tell() < end_pos and len(overrides) < limit:
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
                f.read(12)
                
                if rec_type == 'GRUP':
                    scan_records(start_pos + rec_size, depth+1)
                else:
                    # Check if this is an override (master index != 0)
                    master_idx = (rec_formid >> 24) & 0xFF
                    data_start = f.tell()
                    if master_idx > 0:
                        # Read subrecords
                        subrecords = read_subrecords(f, rec_size)
                        overrides.append({
                            'type': rec_type,
                            'formid': rec_formid,
                            'master_idx': master_idx,
                            'flags': rec_flags,
                            'subrecords': subrecords,
                            'subrecord_count': len(subrecords)
                        })
                    # Skip to end of record data regardless
                    f.seek(data_start + rec_size)
        
        scan_records(file_size)
    
    return overrides

# Check DLC plugins
dlc_plugins = ['Dawnguard.esm', 'HearthFires.esm', 'Dragonborn.esm']

print("Checking DLC plugins for override record structure...")
print("="*70)

for plugin_name in dlc_plugins:
    plugin_path = data_dir / plugin_name
    if not plugin_path.exists():
        print(f"\n{plugin_name}: NOT FOUND")
        continue
    
    print(f"\n{plugin_name}:")
    print("-"*70)
    
    overrides = find_override_records(plugin_path, limit=3)
    
    for i, rec in enumerate(overrides, 1):
        print(f"\n  Override {i}: {rec['type']} FormID=0x{rec['formid']:08X} (master={rec['master_idx']:02X})")
        print(f"  Flags: 0x{rec['flags']:08X}")
        print(f"  Subrecord count: {rec['subrecord_count']}")
        print(f"  Subrecords present:")
        for sub in rec['subrecords']:
            print(f"    - {sub['type']} ({sub['size']} bytes)")

# Check a few ESP plugins
print("\n\n" + "="*70)
print("Checking ESP plugins...")
print("="*70)

esp_files = list(data_dir.glob("*.esp"))[:3]  # First 3 ESP files

for esp_path in esp_files:
    print(f"\n{esp_path.name}:")
    print("-"*70)
    
    try:
        overrides = find_override_records(esp_path, limit=2)
        
        if not overrides:
            print("  No override records found in first scan")
            continue
        
        for i, rec in enumerate(overrides, 1):
            print(f"\n  Override {i}: {rec['type']} FormID=0x{rec['formid']:08X} (master={rec['master_idx']:02X})")
            print(f"  Flags: 0x{rec['flags']:08X}")
            print(f"  Subrecord count: {rec['subrecord_count']}")
            print(f"  Subrecords present:")
            for sub in rec['subrecords']:
                print(f"    - {sub['type']} ({sub['size']} bytes)")
    except Exception as e:
        print(f"  Error reading: {e}")
