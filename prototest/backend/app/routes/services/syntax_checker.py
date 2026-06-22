import ast
import re


def check_syntax(file_path: str, content: str) -> dict:
    ext = file_path.split('.')[-1].lower()

    if ext == 'py':
        try:
            ast.parse(content)
            return {"status": "pass", "message": "No syntax errors found."}
        except SyntaxError as e:
            return {"status": "fail", "message": f"Syntax error on line {e.lineno}: {e.msg}"}

    if ext in ['js', 'jsx', 'ts', 'tsx']:
        errors = []
        if content.count('{') != content.count('}'):
            errors.append("Unmatched curly braces { }")
        if content.count('(') != content.count(')'):
            errors.append("Unmatched parentheses ( )")
        if re.search(r'console\.log\(', content):
            errors.append("console.log() found - remove before production")
        if errors:
            return {"status": "warn", "message": " | ".join(errors)}
        return {"status": "pass", "message": "No obvious issues found."}

    if ext == 'json':
        import json
        try:
            json.loads(content)
            return {"status": "pass", "message": "Valid JSON."}
        except json.JSONDecodeError as e:
            return {"status": "fail", "message": f"Invalid JSON: {e.msg} at line {e.lineno}"}

    return {"status": "skip", "message": "File type not checked."}
