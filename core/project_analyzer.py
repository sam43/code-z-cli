import os
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple
import ast

class ProjectAnalyzer:
    def __init__(self):
        self.ignore_patterns = {
            'dirs': {
                '.git', '.svn', '.hg', '__pycache__', '.pytest_cache',
                'node_modules', 'venv', 'env', '.venv', '.env',
                'build', 'dist', '.next', '.nuxt', 'target',
                '.idea', '.vscode', 'coverage', '.coverage',
                'logs', 'tmp', 'temp', '.cache', 'sessions', 'codez_cli.egg-info', 'reports'
            },
            'files': {
                '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dylib',
                '*.log', '*.tmp', '*.temp', '*.cache',
                '*.min.js', '*.min.css', '*.bundle.js',
                '.DS_Store', 'Thumbs.db', '*.swp', '*.swo',
                '*.lock', 'package-lock.json', 'yarn.lock'
            }
        }
        self.language_extensions = {
            'python': ['.py', '.pyw'],
            'javascript': ['.js', '.mjs', '.jsx'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'cpp': ['.cpp', '.cxx', '.cc', '.c++'],
            'c': ['.c', '.h'],
            'swift': ['.swift'],
            'rust': ['.rs'],
            'go': ['.go'],
            'php': ['.php'],
            'ruby': ['.rb'],
            'html': ['.html', '.htm'],
            'css': ['.css', '.scss', '.sass', '.less'],
            'sql': ['.sql'],
            'shell': ['.sh', '.bash', '.zsh'],
            'config': ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'],
            'markdown': ['.md', '.markdown'],
            'xml': ['.xml', '.xsd', '.xsl']
        }

    def should_ignore(self, path: Path) -> bool:
        # Skip all dot-directories (e.g., .venv, .git, .mypy_cache, etc.)
        if path.is_dir():
            if path.name in self.ignore_patterns['dirs']:
                return True
            if path.name.startswith('.'):
                return True
        # Check .gitignore rules if loaded
        if hasattr(self, '_gitignore_rules') and self._gitignore_rules:
            rel_path = str(path.relative_to(self._gitignore_root)) if hasattr(self, '_gitignore_root') else str(path)
            for rule in self._gitignore_rules:
                if rule.endswith('/'):
                    # Directory rule
                    if rel_path.startswith(rule.rstrip('/')):
                        return True
                elif rule and rule in rel_path:
                    return True
        for pattern in self.ignore_patterns['files']:
            if pattern.startswith('*.'):
                if path.suffix == pattern[1:]:
                    return True
            elif path.name == pattern:
                return True
        return False

    def get_language_from_extension(self, file_path: Path) -> str:
        ext = file_path.suffix.lower()
        for lang, extensions in self.language_extensions.items():
            if ext in extensions:
                return lang
        return 'other'

    def analyze_directory(self, directory: str) -> Dict:
        root_path = Path(directory).resolve()
        if not root_path.exists():
            raise FileNotFoundError(f"Directory {directory} does not exist")
        # Load .gitignore if present
        self._gitignore_rules = []
        self._gitignore_root = root_path
        gitignore_path = root_path / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    self._gitignore_rules.append(line)
        analysis = {
            'project_name': root_path.name,
            'root_path': str(root_path),
            'total_files': 0,
            'languages': defaultdict(int),
            'file_types': defaultdict(int),
            'directory_structure': [],
            'dependencies': {
                'python': set(),
                'javascript': set(),
                'java': set(),
                'other': set()
            },
            'code_metrics': {
                'total_lines': 0,
                'lines_by_language': defaultdict(int),
                'functions_count': defaultdict(int),
                'classes_count': defaultdict(int)
            },
            'key_files': [],
            'config_files': []
        }
        for file_path in self._walk_directory(root_path):
            if self.should_ignore(file_path):
                continue
            analysis['total_files'] += 1
            language = self.get_language_from_extension(file_path)
            analysis['languages'][language] += 1
            analysis['file_types'][file_path.suffix or 'no_extension'] += 1
            try:
                self._analyze_file(file_path, language, analysis)
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        for lang in analysis['dependencies']:
            analysis['dependencies'][lang] = list(analysis['dependencies'][lang])
        return analysis

    def _walk_directory(self, root_path: Path):
        # Use os.walk for better control over directory recursion
        try:
            for dirpath, dirnames, filenames in os.walk(root_path):
                # Remove ignored directories in-place so os.walk doesn't recurse into them
                dirnames[:] = [d for d in dirnames if not self.should_ignore(Path(dirpath) / d)]
                for filename in filenames:
                    file_path = Path(dirpath) / filename
                    if not self.should_ignore(file_path):
                        yield file_path
        except PermissionError:
            print(f"Permission denied: {root_path}")

    def _analyze_file(self, file_path: Path, language: str, analysis: Dict):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                analysis['code_metrics']['total_lines'] += len(lines)
                analysis['code_metrics']['lines_by_language'][language] += len(lines)
                if language == 'python':
                    self._analyze_python_file(file_path, content, analysis)
                elif language == 'javascript':
                    self._analyze_javascript_file(file_path, content, analysis)
                elif language == 'java':
                    self._analyze_java_file(file_path, content, analysis)
                elif language == 'config':
                    analysis['config_files'].append(str(file_path.relative_to(Path(analysis['root_path']))))
                if file_path.name in ['README.md', 'main.py', 'index.js', 'App.js', 'main.java']:
                    analysis['key_files'].append(str(file_path.relative_to(Path(analysis['root_path']))))
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def _analyze_python_file(self, file_path: Path, content: str, analysis: Dict):
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis['code_metrics']['functions_count']['python'] += 1
                elif isinstance(node, ast.ClassDef):
                    analysis['code_metrics']['classes_count']['python'] += 1
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['dependencies']['python'].add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        analysis['dependencies']['python'].add(node.module.split('.')[0])
        except SyntaxError:
            imports = re.findall(r'^(?:from\s+(\S+)\s+)?import\s+(\S+)', content, re.MULTILINE)
            for from_module, import_name in imports:
                module = from_module if from_module else import_name.split('.')[0]
                analysis['dependencies']['python'].add(module)

    def _analyze_javascript_file(self, file_path: Path, content: str, analysis: Dict):
        functions = re.findall(r'function\s+\w+|const\s+\w+\s*=\s*\([^)]*\)\s*=>', content)
        analysis['code_metrics']['functions_count']['javascript'] += len(functions)
        classes = re.findall(r'class\s+\w+', content)
        analysis['code_metrics']['classes_count']['javascript'] += len(classes)
        imports = re.findall(r'import\s+.*?\s+from\s+[\'\"]([^\'\"]+)[\'\"]', content)
        requires = re.findall(r'require\s*\(\s*[\'\"]([^\'\"]+)[\'\"]\s*\)', content)
        for imp in imports + requires:
            if not imp.startswith('.'):
                analysis['dependencies']['javascript'].add(imp.split('/')[0])

    def _analyze_java_file(self, file_path: Path, content: str, analysis: Dict):
        classes = re.findall(r'class\s+\w+', content)
        methods = re.findall(r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)*\w+\s*\([^)]*\)\s*\{', content)
        analysis['code_metrics']['classes_count']['java'] += len(classes)
        analysis['code_metrics']['functions_count']['java'] += len(methods)
        imports = re.findall(r'import\s+([^;]+);', content)
        for imp in imports:
            if not imp.startswith('java.'):
                analysis['dependencies']['java'].add(imp.split('.')[0])

    def generate_summary_report(self, analysis: Dict) -> str:
        report = f"""# Project Summary: {analysis['project_name']}\n
## Overview
- **Project Path**: `{analysis['root_path']}`
- **Total Files**: {analysis['total_files']}
- **Total Lines of Code**: {analysis['code_metrics']['total_lines']:,}
- **Analysis Date**: {self._get_current_datetime()}

## Language Distribution
"""
        total_lang_files = sum(analysis['languages'].values())
        for lang, count in sorted(analysis['languages'].items(), key=lambda x: x[1], reverse=True):
            if lang != 'other':
                percentage = (count / total_lang_files) * 100
                lines = analysis['code_metrics']['lines_by_language'].get(lang, 0)
                report += f"- **{lang.title()}**: {count} files ({percentage:.1f}%) - {lines:,} lines\n"
        report += "\n## File Types\n"
        for ext, count in sorted(analysis['file_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"- `{ext}`: {count} files\n"
        report += "\n## Code Structure\n"
        for lang in ['python', 'javascript', 'java']:
            if analysis['code_metrics']['functions_count'][lang] > 0 or analysis['code_metrics']['classes_count'][lang] > 0:
                report += f"### {lang.title()}\n"
                if analysis['code_metrics']['functions_count'][lang] > 0:
                    report += f"- Functions: {analysis['code_metrics']['functions_count'][lang]}\n"
                if analysis['code_metrics']['classes_count'][lang] > 0:
                    report += f"- Classes: {analysis['code_metrics']['classes_count'][lang]}\n"
                report += "\n"
        report += "## Dependencies\n"
        for lang, deps in analysis['dependencies'].items():
            if deps and lang != 'other':
                report += f"### {lang.title()} Dependencies\n"
                for dep in sorted(deps)[:20]:
                    report += f"- `{dep}`\n"
                if len(deps) > 20:
                    report += f"- ... and {len(deps) - 20} more\n"
                report += "\n"
        if analysis['key_files']:
            report += "## Key Files\n"
            for file in analysis['key_files']:
                report += f"- `{file}`\n"
            report += "\n"
        if analysis['config_files']:
            report += "## Configuration Files\n"
            for file in analysis['config_files'][:10]:
                report += f"- `{file}`\n"
            if len(analysis['config_files']) > 10:
                report += f"- ... and {len(analysis['config_files']) - 10} more\n"
        report += "\n---\n*Generated by CodeZ CLI Project Analyzer*\n"
        return report

    def _get_current_datetime(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
