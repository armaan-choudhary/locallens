import sys
import os
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # For Python < 3.8
    try:
        from importlib_metadata import version, PackageNotFoundError
    except ImportError:
        version = None

def check_dependencies():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    req_file = os.path.join(backend_dir, "requirements.txt")
    
    if not os.path.exists(req_file):
        print(f"Error: {req_file} not found.")
        sys.exit(1)

    print("Checking backend dependencies...")
    with open(req_file, "r") as f:
        # Simple parser for requirements.txt (ignores versions/comments for quick check)
        requirements = []
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Extract package name (everything before <, >, =, #)
            name = line.split('=')[0].split('<')[0].split('>')[0].split('#')[0].strip()
            if name:
                requirements.append(name)

    missing = []
    for req in requirements:
        if version is None:
            # Fallback for very old python or missing importlib_metadata
            continue
        try:
            # Check if the package is installed
            version(req)
        except PackageNotFoundError:
            missing.append(req)

    if missing:
        print(f"Error: Missing or outdated dependencies: {', '.join(missing)}")
        print(f"Please run: pip install -r backend/requirements.txt")
        sys.exit(1)
    else:
        print("✓ All backend dependencies are satisfied.")

if __name__ == "__main__":
    check_dependencies()
