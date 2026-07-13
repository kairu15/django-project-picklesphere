"""Remove inline imports from views files - keeps only top-level imports."""
import re

files = [
    "dashboard/views.py",
    "organizations/views.py", 
    "payments/views.py",
]

# Pattern for inline imports (indented from/import lines)
inline_import_pattern = re.compile(r'^\s+(from\s+\S+\s+import|import\s+\S+)')

# Also track openpyxl imports that need to stay (inside try/except)
for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    removed = 0
    for line in lines:
        # Skip inline imports (indented lines starting with from/import)
        if inline_import_pattern.match(line):
            removed += 1
            continue
        new_lines.append(line)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"{filepath}: removed {removed} inline imports")
