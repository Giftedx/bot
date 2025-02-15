#!/usr/bin/env python3
"""Project Analysis Tool for Developer Handover
A comprehensive tool for analyzing and documenting Python projects to facilitate developer handover.
"""

import argparse
import ast
import sys
import os
import json
import re
import datetime
import logging
from typing import Dict, Any, Tuple, Optional, List, Set
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
from mimetypes import guess_type

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ProjectHandover')

@dataclass
class CodeMetrics:
    """Class to hold comprehensive code metrics for a Python file."""
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    imports: int = 0
    classes: int = 0
    functions: int = 0
    complexity: int = 0
    maintainability_index: float = 0.0
    documentation_coverage: float = 0.0

def ast_unparse(node: ast.AST) -> str:
    """Compatibility function for ast.unparse() (Python 3.9+)."""
    if hasattr(ast, 'unparse'):
        return ast.unparse(node)
    
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Constant):
        return repr(node.value)
    elif isinstance(node, ast.Str):
        return repr(node.s)
    elif isinstance(node, ast.Num):
        return str(node.n)
    elif isinstance(node, ast.arg):
        return node.arg
    elif isinstance(node, ast.Return):
        return f"return {ast_unparse(node.value) if node.value else ''}"
    elif isinstance(node, ast.Call):
        func = ast_unparse(node.func)
        args = [ast_unparse(arg) for arg in node.args]
        kwargs = [f"{kw.arg}={ast_unparse(kw.value)}" for kw in node.keywords]
        return f"{func}({', '.join(args + kwargs)})"
    else:
        return f"<{node.__class__.__name__}>"

class ProjectHandoverAnalyzer:
    """Enhanced analyzer for helping developers take over existing Python projects."""
    
    def __init__(self, ignore_patterns: List[str] = None):
        self.ignore_patterns = ignore_patterns or [
            '.git', '__pycache__', '.pyc$', '.env$', 'venv',
            'build', 'dist', '.egg-info$', '.pytest_cache'
        ]
        self.metrics = CodeMetrics()
        self.entry_points = []
        self.config_files = []
        self.dependencies = defaultdict(dict)
        self.core_modules = set()
        self.test_files = set()
        self.other_files = defaultdict(list)  # New: Track non-Python files by extension
        self.critical_patterns = {
            'security': [
                r'password', r'secret', r'token', r'key', r'auth', r'credential'
            ],
            'configuration': [
                r'config[^/]*\.py$', r'settings[^/]*\.py$', r'\.env',
                r'\.ini$', r'\.yaml$', r'\.yml$', r'\.json$', r'\.toml$', r'\.conf$'
            ],
            'entry_points': [
                r'main\.py$', r'app\.py$', r'run\.py$', r'manage\.py$',
                r'wsgi\.py$', r'asgi\.py$'
            ],
            'core_logic': [
                r'models\.py$', r'views\.py$', r'controllers\.py$',
                r'services\.py$', r'database\.py$'
            ]
        }
        # Enhanced file categories
        self.file_categories : Dict[str, List[str]] = {
            'documentation': ['.md', '.rst', '.txt', '.doc', '.docx', '.pdf', '.rtf'],
            'configuration': ['.yml', '.yaml', '.json', '.toml',
                              '.ini', '.cfg', '.conf', '.env'],
            'frontend': ['.js', '.ts', '.jsx', '.tsx', '.vue',
                         '.html', '.css', '.scss', '.sass', '.less'],
            'assets': ['.jpg', '.jpeg', '.png', '.gif',
                       '.svg', '.ico', '.ttf', '.woff', '.woff2'],
            'data': ['.csv', '.json', '.xml', '.yaml', '.yml', '.sqlite', '.db', '.sql'],
            'docker': ['Dockerfile', '.dockerignore', 'docker-compose.yml'],
            'git': ['.gitignore', '.gitattributes', '.gitmodules'],
            'scripts': ['.sh', '.bat', '.ps1', '.cmd', '.bash'],
            'package': ['requirements.txt', 'Pipfile', 'pyproject.toml', 'setup.py', 'package.json'],
            'ci_cd': ['.travis.yml', '.github', 'azure-pipelines.yml', '.gitlab-ci.yml', 'Jenkinsfile'],
            'binary': ['.exe', '.dll', '.so', '.dylib', '.bin'],
            'archive': ['.zip', '.tar', '.gz', '.7z', '.rar'],
            'media': ['.mp3', '.mp4', '.wav', '.avi', '.mov'],
            'office': ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
            'logs': ['.log', '.logs'],
            'misc': []
        }

    def analyze_file_complexity(self, node: ast.AST) -> int:
        """Calculate cognitive complexity of code."""
        complexity = 0
        nesting_level = 0
        
        class ComplexityVisitor(ast.NodeVisitor):
            def generic_control_flow_visit(self, node):
                nonlocal complexity, nesting_level
                complexity += 1 + nesting_level
                nesting_level += 1
                self.generic_visit(node)
                nesting_level -= 1
            
            visit_If = visit_For = visit_While = visit_Try = generic_control_flow_visit

        ComplexityVisitor().visit(node)
        return complexity

    def analyze_file(self, file_path: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Analyze a single Python file with focus on maintainability."""
        if not os.path.exists(file_path):
            return None, f"File not found: {file_path}"
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
                
            lines = source_code.splitlines()
            tree = ast.parse(source_code)
            
            metrics = CodeMetrics()
            metrics.total_lines = len(lines)
            metrics.blank_lines = sum(1 for line in lines if not line.strip())
            metrics.comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            metrics.code_lines = metrics.total_lines - metrics.blank_lines - metrics.comment_lines
            
            file_data = {
                'filename': file_path,
                'metrics': self._calculate_metrics(metrics, tree),
                'structure': {
                    'imports': [],
                    'from_imports': [],
                    'classes': [],
                    'functions': [],
                    'global_variables': [],
                },
                'documentation': {
                    'module_docstring': ast.get_docstring(tree),
                    'todos': [],
                    'security_concerns': [],
                },
                'dependencies': set(),
                'critical_sections': [],
                'type_hints': self._analyze_type_hints(tree)
            }

            # Analyze critical patterns
            for category, patterns in self.critical_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, source_code, re.IGNORECASE):
                        file_data['critical_sections'].append({
                            'category': category,
                            'pattern': pattern,
                            'context': self._get_context(source_code, pattern)
                        })

            # Parse docstrings and code structure
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        file_data['structure']['imports'].append(alias.name)
                        file_data['dependencies'].add(alias.name.split('.')[0])
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_names = [alias.name for alias in node.names]
                        file_data['structure']['from_imports'].append({
                            'module': node.module,
                            'names': imported_names
                        })
                        file_data['dependencies'].add(node.module.split('.')[0])

                elif isinstance(node, ast.ClassDef):
                    class_info = self._analyze_class(node)
                    file_data['structure']['classes'].append(class_info)

                elif isinstance(node, ast.FunctionDef):
                    func_info = self._analyze_function(node)
                    file_data['structure']['functions'].append(func_info)

            file_data['dependencies'] = list(file_data['dependencies'])
            return file_data, None

        except UnicodeDecodeError:
            return None, f"Unable to read {file_path}: Invalid encoding"
        except SyntaxError as e:
            return None, f"Syntax error in {file_path}: {str(e)}"
        except Exception as e:
            return None, f"Error analyzing {file_path}: {str(e)}"

    def _calculate_metrics(self, metrics: CodeMetrics, tree: ast.AST) -> Dict[str, Any]:
        """Calculate comprehensive code metrics."""
        total_functions = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
        total_classes = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
        
        metrics.functions = total_functions
        metrics.classes = total_classes
        metrics.complexity = self.analyze_file_complexity(tree)
        
        # Calculate maintainability index
        if metrics.code_lines > 0:
            metrics.maintainability_index = max(0, min(100, 100 * (
                171 - 5.2 * float(metrics.complexity) / metrics.code_lines -
                0.23 * metrics.code_lines - 16.2 * float(metrics.comment_lines) / metrics.code_lines
            ) / 171))

        # Calculate documentation coverage
        documented_items = len([
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(node)
        ])
        total_items = total_functions + total_classes
        metrics.documentation_coverage = (documented_items / total_items * 100) if total_items > 0 else 100

        return {
            'total_lines': metrics.total_lines,
            'code_lines': metrics.code_lines,
            'comment_lines': metrics.comment_lines,
            'blank_lines': metrics.blank_lines,
            'functions': metrics.functions,
            'classes': metrics.classes,
            'complexity': metrics.complexity,
            'maintainability_index': round(metrics.maintainability_index, 2),
            'documentation_coverage': round(metrics.documentation_coverage, 2)
        }

    def _analyze_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Detailed analysis of a class definition."""
        return {
            'name': node.name,
            'bases': [ast_unparse(base) for base in node.bases],
            'docstring': ast.get_docstring(node),
            'methods': [self._analyze_function(method) for method in node.body 
                       if isinstance(method, ast.FunctionDef)],
            'properties': [self._analyze_function(prop) for prop in node.body 
                         if isinstance(prop, ast.FunctionDef) and 
                         any(isinstance(d, ast.Name) and d.id == 'property' 
                             for d in prop.decorator_list)],
            'class_variables': [{'name': target.id, 'value': ast_unparse(node.value)}
                              for item in node.body 
                              if isinstance(item, ast.Assign)
                              for target in item.targets 
                              if isinstance(target, ast.Name)],
            'complexity': self.analyze_file_complexity(node),
            'type_hints': self._analyze_type_hints(node)
        }

    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Detailed analysis of a function definition."""
        return {
            'name': node.name,
            'args': [self._analyze_argument(arg) for arg in node.args.args],
            'docstring': ast.get_docstring(node),
            'returns': ast_unparse(node.returns) if node.returns else None,
            'decorators': [ast_unparse(d) for d in node.decorator_list],
            'complexity': self.analyze_file_complexity(node),
            'has_type_hints': bool(node.returns or 
                                 any(arg.annotation for arg in node.args.args))
        }

    def _analyze_argument(self, arg: ast.arg) -> Dict[str, Any]:
        """Analyze a function argument."""
        return {
            'name': arg.arg,
            'annotation': ast_unparse(arg.annotation) if arg.annotation else None
        }

    def _analyze_type_hints(self, node: ast.AST) -> Dict[str, Any]:
        """Analyze type hints usage in code."""
        type_hints = {
            'total_annotations': 0,
            'missing_annotations': 0,
            'variables': [],
            'functions': [],
            'coverage_percentage': 0.0
        }
        
        class TypeHintVisitor(ast.NodeVisitor):
            def visit_AnnAssign(self, node):
                type_hints['total_annotations'] += 1
                type_hints['variables'].append({
                    'name': node.target.id if isinstance(node.target, ast.Name) else 'unknown',
                    'annotation': ast_unparse(node.annotation)
                })
            
            def visit_FunctionDef(self, node):
                annotations = []
                if node.returns:
                    annotations.append(('return', ast_unparse(node.returns)))
                for arg in node.args.args:
                    if arg.annotation:
                        annotations.append((arg.arg, ast_unparse(arg.annotation)))
                    else:
                        type_hints['missing_annotations'] += 1
                
                if annotations:
                    type_hints['functions'].append({
                        'name': node.name,
                        'annotations': annotations
                    })

        TypeHintVisitor().visit(node)
        total_items = type_hints['total_annotations'] + type_hints['missing_annotations']
        type_hints['coverage_percentage'] = round(
            type_hints['total_annotations'] / total_items * 100, 2
        ) if total_items > 0 else 0.0
        
        return type_hints

    def _get_context(self, source_code: str, pattern: str, context_lines: int = 2) -> List[str]:
        """Get context around matched patterns in source code."""
        lines = source_code.splitlines()
        contexts = []
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                context = lines[start:end]
                contexts.append('\n'.join(context))
        return contexts

    def analyze_project(self, project_root: str) -> Dict[str, Any]:
        """Comprehensive project analysis including structure, dependencies, and requirements."""
        project_analysis = {
            'structure_report': self.verify_project_structure(project_root),
            'structure': {
                'root': project_root,
                'entry_points': self.find_entry_points(project_root),
                'config_files': self.config_files,
                'env_variables': self.find_environment_variables(project_root),
                'test_files': list(self.test_files),
                'core_modules': list(self.core_modules),
                'other_files': self._scan_other_files(project_root)  # New: Add non-Python files
            },
            'files_data': [],
            'requirements': self._analyze_requirements(project_root)
        }

        python_files = []
        for root, _, files in os.walk(project_root):
            if any(self.should_ignore(p) for p in Path(root).parts):
                continue
            for file in files:
                if file.endswith('.py') and not self.should_ignore(file):
                    python_files.append(os.path.join(root, file))

        for file_path in python_files:
            file_data, error = self.analyze_file(file_path)
            if error:
                logger.error(f"Error processing {file_path}: {error}")
            elif file_data:
                project_analysis['files_data'].append(file_data)
                if 'test' in file_path.lower():
                    self.test_files.add(file_path)

        return project_analysis

    def _scan_other_files(self, project_root: str) -> Dict[str, List[Dict[str, Any]]]:
        """Enhanced scan of all non-Python files with detailed metadata."""
        categorized_files = defaultdict(list)
        
        for root, dirs, files in os.walk(project_root):
            if any(self.should_ignore(p) for p in Path(root).parts):
                continue

            for file in files:
                if file.endswith('.py'):  # Skip Python files as they're handled separately
                    continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_root)
                
                try:
                    stats = os.stat(file_path)
                    mime_type, encoding = guess_type(file_path)
                    
                    file_info = {
                        'path': rel_path,
                        'size': stats.st_size,
                        'last_modified': datetime.datetime.fromtimestamp(stats.st_mtime).isoformat(),
                        'created': datetime.datetime.fromtimestamp(stats.st_ctime).isoformat(),
                        'mime_type': mime_type or 'application/octet-stream',
                        'encoding': encoding,
                        'is_binary': self._is_binary_file(file_path),
                        'extension': os.path.splitext(file)[1].lower() or 'no_extension'
                    }

                    # Try to extract basic text content for non-binary files
                    if not file_info['is_binary'] and stats.st_size < 1024 * 1024:  # Skip files > 1MB
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read(1024)  # Read first 1KB
                                file_info['preview'] = content if len(content) < 1024 else content[:1021] + '...'
                        except UnicodeDecodeError:
                            file_info['preview'] = None
                    
                    # Categorize the file
                    categorized = False
                    for category, extensions in self.file_categories.items():
                        if any(file.endswith(ext) or file == ext for ext in extensions):
                            categorized_files[category].append(file_info)
                            categorized = True
                            break
                    
                    if not categorized:
                        categorized_files['misc'].append(file_info)

                except Exception as e:
                    logger.warning(f"Error processing {file_path}: {str(e)}")
                    continue

        return dict(categorized_files)

    def _is_binary_file(self, file_path: str, sample_size: int = 1024) -> bool:
        """Determine if a file is binary by reading its first few bytes."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(sample_size)
                return b'\0' in chunk  # Simple heuristic for binary files
        except Exception:
            return True

    def _analyze_requirements(self, project_root: str) -> Dict[str, str]:
        """Parse requirements.txt with version specifier support."""
        requirements_file = Path(project_root) / 'requirements.txt'
        dependencies : Dict[str, str] = {}
        if requirements_file.exists() and requirements_file.is_file():
            try:
                with open(requirements_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            match = re.match(r"([a-zA-Z0-9_-]+)([=><]=?[a-zA-Z0-9_.-]*)?",
                                              line)
                            if match:
                                package_name = match.group(1)
                                version_specifier = match.group(2) or ""
                                dependencies[package_name] = version_specifier
                            else:
                                logger.warning(f"Could not parse line in requirements.txt: '{line}'")
            except Exception as e:
                logger.error(f"Error parsing requirements.txt: {e}")
                return {}
        return dependencies

    def find_entry_points(self, project_root: str) -> List[str]:
        """Identify potential project entry points."""
        entry_points = []
        common_entries = ['main.py', 'app.py', 'run.py', 'manage.py', 'wsgi.py', 'asgi.py']
        
        for root, _, files in os.walk(project_root):
            if any(self.should_ignore(p) for p in Path(root).parts):
                continue
            
            for file in files:
                if file in common_entries:
                    entry_points.append(os.path.relpath(os.path.join(root, file), project_root))
                elif file.endswith('.py'):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            content = f.read()
                            if '__name__' in content and '__main__' in content:
                                entry_points.append(os.path.relpath(os.path.join(root, file), project_root))
                    except Exception:
                        pass
        
        return entry_points

    def find_environment_variables(self, project_root: str) -> List[str]:
        """Find environment variables used in the project."""
        env_vars = set()
        env_pattern = re.compile(r'os\.environ\.get\([\'"](\w+)[\'"]\)|os\.getenv\([\'"](\w+)[\'"]\)')
        
        for root, _, files in os.walk(project_root):
            if any(self.should_ignore(p) for p in Path(root).parts):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            content = f.read()
                            matches = env_pattern.findall(content)
                            for match in matches:
                                env_vars.add(match[0] or match[1])
                    except Exception:
                        continue
                
                elif file in ['.env.example', '.env.sample', '.env.template']:
                    try:
                        with open(os.path.join(root, file), 'r') as f:
                            for line in f:
                                if '=' in line and not line.startswith('#'):
                                    var_name = line.split('=')[0].strip()
                                    env_vars.add(var_name)
                    except Exception:
                        continue
        
        return sorted(list(env_vars))

    def should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored."""
        return any(re.search(pattern, str(path)) for pattern in self.ignore_patterns)

    def generate_handover_documentation(self, project_root: str,
                                      project_analysis: Dict[str, Any],
                                      output_file: str) -> None:
        """Generate comprehensive documentation for project handover."""
        files_data = project_analysis['files_data']
        structure_report = project_analysis['structure_report']
        requirements = project_analysis['requirements']

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Project Handover Documentation\n\n")
            f.write(f"*Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")

            # Executive Summary
            f.write("## 1. Executive Summary\n\n")
            total_files = len(files_data)
            total_lines = sum(fd['metrics']['total_lines'] for fd in files_data)
            avg_complexity = sum(fd['metrics']['complexity'] for fd in files_data) / total_files if total_files > 0 else 0
            avg_maintainability = sum(fd['metrics']['maintainability_index'] for fd in files_data) / total_files if total_files > 0 else 0
            avg_docs_coverage = sum(fd['metrics']['documentation_coverage'] for fd in files_data) / total_files if total_files > 0 else 0

            f.write("### Project Overview\n")
            f.write(f"- Total Python Files: {total_files}\n")
            f.write(f"- Total Lines of Code: {total_lines:,}\n")
            f.write(f"- Average Complexity: {avg_complexity:.2f}\n")
            f.write(f"- Average Maintainability Index: {avg_maintainability:.2f}/100\n")
            f.write(f"- Documentation Coverage: {avg_docs_coverage:.2f}%\n\n")

            # Critical Findings
            f.write("### Critical Findings\n")
            if structure_report['missing_components']:
                f.write("\n#### Missing Components:\n")
                for component in structure_report['missing_components']:
                    f.write(f"- {component}\n")

            if structure_report['security_concerns']:
                f.write("\n#### Security Concerns:\n")
                for concern in structure_report['security_concerns']:
                    f.write(f"- {concern}\n")

            # Project Structure
            f.write("\n## 2. Project Structure\n\n")
            f.write("### Directory Overview\n")

            # Create a tree structure of directories
            def print_tree(directory: Path, prefix: str = "") -> None:
                f.write(f"{prefix}└── {directory.name}/\n")
                items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                for item in items:
                    if item.is_dir() and not any(re.search(p, item.name) for p in self.ignore_patterns):
                        print_tree(item, prefix + "    ")

            project_path = Path(project_root)
            print_tree(project_path)

            # Continue with the rest of the documentation writing...
            # (the rest of the content would continue here)

    # The main() function and if __name__ == "__main__" block would follow here
# Dependencies and Requirements
            f.write("\n## 3. Dependencies and Requirements\n\n")
            if requirements:
                f.write("### Project Dependencies\n")
                for pkg, version in requirements.items():
                    f.write(f"- {pkg}{version}\n")

            # Environment Variables
            env_vars = project_analysis['structure']['env_variables']
            if env_vars:
                f.write("\n### Environment Variables\n")
                for var in env_vars:
                    f.write(f"- {var}\n")

            # Code Quality Analysis
            f.write("\n## 4. Code Quality Analysis\n\n")
            
            # Complex files
            complex_files = [f for f in files_data if f['metrics']['complexity'] > 10]
            if complex_files:
                f.write("### Complex Components\n")
                for file in complex_files:
                    f.write(f"- {os.path.basename(file['filename'])} ")
                    f.write(f"(Complexity: {file['metrics']['complexity']})\n")

            # Documentation Coverage
            f.write("\n### Documentation Coverage\n")
            poor_docs = [f for f in files_data if f['metrics']['documentation_coverage'] < 70]
            if poor_docs:
                f.write("\nFiles needing documentation improvements:\n")
                for file in poor_docs:
                    f.write(f"- {os.path.basename(file['filename'])} ")
                    f.write(f"({file['metrics']['documentation_coverage']:.1f}% covered)\n")

            # Type Hints Analysis
            f.write("\n### Type Hints Coverage\n")
            type_hint_stats = [
                (os.path.basename(f['filename']), f['type_hints']['coverage_percentage'])
                for f in files_data if f['type_hints']['total_annotations'] > 0
            ]
            if type_hint_stats:
                f.write("\n| File | Type Hint Coverage |\n")
                f.write("|------|-------------------|\n")
                for file, coverage in sorted(type_hint_stats, key=lambda x: x[1]):
                    f.write(f"| {file} | {coverage:.1f}% |\n")

            # Recommendations
            f.write("\n## 5. Recommendations\n\n")
            if structure_report['recommended_additions']:
                for rec in structure_report['recommended_additions']:
                    f.write(f"- {rec}\n")

            if avg_maintainability < 70:
                f.write("- Consider refactoring components with low maintainability scores\n")
            if avg_docs_coverage < 60:
                f.write("- Improve documentation coverage across the project\n")

            # Enhanced Other Files section
            f.write("\n## 6. Additional Project Files\n\n")
            other_files = project_analysis['structure']['other_files']
            
            total_files = sum(len(files) for files in other_files.values())
            total_size = sum(sum(f['size'] for f in files) for files in other_files.values())
            
            f.write(f"Total non-Python files: {total_files}\n")
            f.write(f"Total size: {total_size / (1024*1024):.2f} MB\n\n")
            
            for category, files in other_files.items():
                if files:
                    f.write(f"### {category.title()}\n")
                    category_size = sum(f['size'] for f in files)
                    f.write(f"Category size: {category_size / 1024:.1f}KB, Files: {len(files)}\n\n")
                    
                    for file_info in sorted(files, key=lambda x: x['path']):
                        size_kb = file_info['size'] / 1024
                        f.write(f"- **{file_info['path']}** ({size_kb:.1f}KB)\n")
                        if 'preview' in file_info and file_info['preview']:
                            preview = file_info['preview'].replace('\n', ' ')[:100]
                            f.write(f"  ```\n  {preview}...\n  ```\n")
                    f.write("\n")

    def verify_project_structure(self, project_root: str) -> Dict[str, Any]:
        """Verify the project structure and provide recommendations."""
        report = {
            'missing_components': [],
            'security_concerns': [],
            'recommended_additions': []
        }

        # Check for basic project components
        essential_files = {
            'requirements.txt': 'Project dependencies file',
            'README.md': 'Project documentation',
            '.gitignore': 'Git ignore file',
            'setup.py': 'Package configuration',
            'tests': 'Test directory'
        }

        for file, description in essential_files.items():
            if not os.path.exists(os.path.join(project_root, file)):
                report['missing_components'].append(f"Missing {description} ({file})")
                report['recommended_additions'].append(f"Add {description}")

        # Check for security concerns
        for root, _, files in os.walk(project_root):
            if any(self.should_ignore(p) for p in Path(root).parts):
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if file.endswith('.py'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            if 'password' in content and ('hardcoded' in content or 'default' in content):
                                report['security_concerns'].append(f"Potential hardcoded password in {file}")
                            if 'api_key' in content and ('hardcoded' in content or 'default' in content):
                                report['security_concerns'].append(f"Potential hardcoded API key in {file}")
                except Exception as e:
                    logger.warning(f"Could not analyze {file_path}: {str(e)}")

        # Add general recommendations
        if not report['missing_components']:
            report['recommended_additions'].extend([
                "Consider adding API documentation",
                "Consider adding code coverage reporting",
                "Consider adding continuous integration configuration"
            ])

        return report


def main() -> None:
    """Main entry point for the project handover analysis tool."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--target", required=True, help="Target project directory to analyze")
    parser.add_argument("--output", default="project_handover.md", help="Output file path (default: project_handover.md)")
    parser.add_argument("--ignore", nargs="+", help="Additional patterns to ignore (e.g., 'venv' 'test')")
    parser.add_argument("--json", action="store_true", help="Also output raw analysis data in JSON format")
    parser.add_argument("--min-complexity", type=int, default=5, help="Minimum complexity threshold for reporting")
    parser.add_argument("--min-maintainability", type=float, default=50.0, help="Minimum maintainability index threshold")
    
    args = parser.parse_args()
    
    try:
        logger.info("Starting project handover analysis...")
        analyzer = ProjectHandoverAnalyzer(ignore_patterns=args.ignore)
        
        if not os.path.isdir(args.target):
            logger.error("Target directory does not exist")
            sys.exit(1)
            
        project_analysis = analyzer.analyze_project(args.target)
        
        if not project_analysis['files_data']:
            logger.error("No Python files found in the specified directory.")
            return
        
        logger.info(f"Found {len(project_analysis['files_data'])} Python files to analyze...")
        
        logger.info("Generating handover documentation...")
        analyzer.generate_handover_documentation(
            args.target,
            project_analysis,
            args.output
        )
        logger.info(f"Documentation generated: {args.output}")
        
        if args.json:
            json_output = args.output.rsplit('.', 1)[0] + '.json'
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump({
                    'project_analysis': project_analysis,
                    'analysis_date': datetime.datetime.now().isoformat()
                }, f, indent=2, default=str)
            logger.info(f"JSON data exported to: {json_output}")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()