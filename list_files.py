import os
import sys
import platform
from datetime import datetime

# Open output file in write mode
with open('output.txt', 'w', encoding='utf-8') as f:
    def write_log(msg):
        """Write to both console and file"""
        print(msg, flush=True)
        f.write(f"{msg}\n")
        f.flush()

    write_log(f"=== System Check: {datetime.now()} ===")
    write_log(f"OS: {platform.system()} {platform.release()}")
    write_log(f"Python: {sys.version}")
    write_log(f"Working Directory: {os.getcwd()}")
    write_log(f"Script Location: {__file__}")
    write_log("\nDirectory Contents:")
    
    try:
        for item in os.listdir('.'):
            path = os.path.abspath(item)
            if os.path.isfile(path):
                size = os.path.getsize(path)
                write_log(f"FILE: {item} ({size} bytes)")
            else:
                write_log(f"DIR:  {item}")
                try:
                    subitems = os.listdir(item)
                    for subitem in subitems:
                        write_log(f"  - {subitem}")
                except Exception as e:
                    write_log(f"  Error reading {item}: {e}")
    except Exception as e:
        write_log(f"Error scanning directory: {e}")

    write_log("\n=== Scan Complete ===")
