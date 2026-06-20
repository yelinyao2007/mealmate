import os
import shutil

# Clear pycache
for root, dirs, files in os.walk('backend/app/routers'):
    for d in dirs:
        if d == '__pycache__':
            path = os.path.join(root, d)
            print(f"Removing {path}")
            shutil.rmtree(path)

print("Done!")