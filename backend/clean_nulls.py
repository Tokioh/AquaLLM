import os

def clean_null_bytes(file_path):
    """Remove null bytes from a file"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Remove null bytes
        clean_content = content.replace(b'\x00', b'')
        
        # Write back the clean content
        with open(file_path, 'wb') as f:
            f.write(clean_content)
        
        print(f"Cleaned null bytes from {file_path}")
        return True
    except Exception as e:
        print(f"Error cleaning {file_path}: {e}")
        return False

# Clean the main application files
files_to_clean = [
    "app/main.py",
    "app/services/database.py",
    "app/models/schemas.py",
    "app/services/llm.py"
]

for file_path in files_to_clean:
    if os.path.exists(file_path):
        clean_null_bytes(file_path)
    else:
        print(f"File not found: {file_path}")

print("Cleaning completed!")
