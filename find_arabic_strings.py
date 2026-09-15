import os
import re
import ast

def contains_arabic(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))

class StringVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.found = False

    def visit_Str(self, node):
        if contains_arabic(node.s):
            self.found = True
        self.generic_visit(node)
        
    def visit_Constant(self, node):
        if isinstance(node.value, str) and contains_arabic(node.value):
            self.found = True
        self.generic_visit(node)

files_with_arabic_strings = []

for root, _, files in os.walk('.'):
    if 'node_modules' in root or '.git' in root or 'venv' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                    visitor = StringVisitor(path)
                    visitor.visit(tree)
                    if visitor.found:
                        files_with_arabic_strings.append(path)
            except Exception as e:
                pass

print("Python files with Arabic strings:")
for f in files_with_arabic_strings:
    print(f)

