import sys
import os
import pkg_resources

def check_dependencies():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    req_file = os.path.join(backend_dir, "requirements.txt")
    
    if not os.path.exists(req_file):
        print(f"Error: {req_file} not found.")
        sys.exit(1)

    print("Checking backend dependencies...")
    with open(req_file, "r") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    missing = []
    for req in requirements:
        try:
            pkg_resources.require(req)
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            missing.append(req)

    if missing:
        print(f"Error: Missing or outdated dependencies: {', '.join(missing)}")
        print(f"Please run: pip install -r backend/requirements.txt")
        sys.exit(1)
    else:
        print("✓ All backend dependencies are satisfied.")

if __name__ == "__main__":
    check_dependencies()
