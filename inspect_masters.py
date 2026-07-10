import sys
import struct

# Read raw plugin file to examine TES4 header
plugin_path = r"C:\Steam\steamapps\common\Skyrim Special Edition\Data\BDHimboSkimpyGear.esp"

with open(plugin_path, 'rb') as f:
    # Read TES4 record header (24 bytes)
    rec_type = f.read(4).decode('ascii')
    rec_size = struct.unpack('I', f.read(4))[0]
    rec_flags = struct.unpack('I', f.read(4))[0]
    rec_formid = struct.unpack('I', f.read(4))[0]
    rec_revision = struct.unpack('I', f.read(4))[0]
    rec_version = struct.unpack('H', f.read(2))[0]
    rec_unknown = struct.unpack('H', f.read(2))[0]
    
    print(f"Record Type: {rec_type}")
    print(f"Record Size: {rec_size}")
    print(f"Flags: 0x{rec_flags:08X}")
    print(f"FormID: 0x{rec_formid:08X}")
    print()
    
    # Read subrecords from TES4 record data
    bytes_read = 0
    master_count = 0
    
    while bytes_read < rec_size:
        subr_type = f.read(4).decode('ascii')
        subr_size = struct.unpack('H', f.read(2))[0]
        subr_data = f.read(subr_size)
        bytes_read += 6 + subr_size
        
        if subr_type == 'MAST':
            master_count += 1
            master_name = subr_data.rstrip(b'\x00').decode('ascii')
            print(f"MAST #{master_count}: {master_name}")
            print(f"  Size: {subr_size} bytes")
            
        elif subr_type == 'DATA':
            print(f"DATA (after MAST #{master_count}):")
            print(f"  Size: {subr_size} bytes")
            print(f"  Raw hex: {subr_data.hex()}")
            if subr_size == 8:
                value = struct.unpack('Q', subr_data)[0]
                print(f"  As uint64: {value}")
            elif subr_size == 4:
                value = struct.unpack('I', subr_data)[0]
                print(f"  As uint32: {value}")
            print()
        
        if master_count >= 3:  # Just check first few
            break

print(f"\nTotal masters found: {master_count}")
