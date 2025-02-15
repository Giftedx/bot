import sys
import os

def main():
    # Write directly to a file
    with open('verify.txt', 'w') as f:
        f.write("Python Environment Verification\n")
        f.write("-" * 30 + "\n")
        f.write(f"Python Version: {sys.version}\n")
        f.write(f"Executable: {sys.executable}\n")
        f.write(f"Working Dir: {os.getcwd()}\n")
        f.write("\nSystem Path:\n")
        for p in sys.path:
            f.write(f"- {p}\n")

if __name__ == "__main__":
    main()
    print("Verification complete. Check verify.txt for results.")
