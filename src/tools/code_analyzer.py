"""Script to analyze collected code for patterns and implementations."""
import ast
import logging
import os
from typing import Dict, List, Set
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """Analyze code for patterns and implementations."""
    
    def __init__(self, base_path: str = "repos"):
        """Initialize analyzer with base path."""
        self.base_path = Path(base_path)
        
    def analyze_all(self) -> Dict[str, Dict]:
        """Analyze all repositories in base path."""
        results = {}
        
        for repo_dir in self.base_path.iterdir():
            if repo_dir.is_dir() and not repo_dir.name.startswith('.'):
                logger.info(f"Analyzing repository: {repo_dir.name}")
                try:
                    results[repo_dir.name] = self.analyze_repository(repo_dir)
                except Exception as e:
                    logger.error(f"Failed to analyze {repo_dir.name}: {e}")
                    
        return results
    
    def analyze_repository(self, repo_path: Path) -> Dict:
        """Analyze a single repository."""
        patterns = {
            'minigames': self.find_minigame_patterns(repo_path),
            'combat': self.find_combat_patterns(repo_path),
            'skills': self.find_skill_patterns(repo_path),
            'items': self.find_item_patterns(repo_path),
            'npcs': self.find_npc_patterns(repo_path)
        }
        
        # Log findings
        for category, findings in patterns.items():
            logger.info(f"Found {len(findings)} {category} patterns")
            
        return patterns
    
    def find_minigame_patterns(self, path: Path) -> List[Dict]:
        """Find minigame implementation patterns."""
        patterns = []
        
        for file_path in self._find_relevant_files(path, {'minigame', 'game', 'activity'}):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if self._is_minigame_class(node):
                            patterns.append({
                                'file': str(file_path),
                                'class': node.name,
                                'methods': self._extract_methods(node)
                            })
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                
        return patterns
    
    def find_combat_patterns(self, path: Path) -> List[Dict]:
        """Find combat system implementation patterns."""
        patterns = []
        
        for file_path in self._find_relevant_files(path, {'combat', 'battle', 'fight'}):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                        if self._is_combat_related(node):
                            patterns.append({
                                'file': str(file_path),
                                'type': 'class' if isinstance(node, ast.ClassDef) else 'function',
                                'name': node.name,
                                'methods': self._extract_methods(node) if isinstance(node, ast.ClassDef) else None
                            })
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                
        return patterns
    
    def find_skill_patterns(self, path: Path) -> List[Dict]:
        """Find skill implementation patterns."""
        patterns = []
        
        for file_path in self._find_relevant_files(path, {'skill', 'level', 'experience'}):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if self._is_skill_class(node):
                            patterns.append({
                                'file': str(file_path),
                                'class': node.name,
                                'methods': self._extract_methods(node)
                            })
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                
        return patterns
    
    def find_item_patterns(self, path: Path) -> List[Dict]:
        """Find item system implementation patterns."""
        patterns = []
        
        for file_path in self._find_relevant_files(path, {'item', 'inventory', 'equipment'}):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if self._is_item_class(node):
                            patterns.append({
                                'file': str(file_path),
                                'class': node.name,
                                'methods': self._extract_methods(node)
                            })
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                
        return patterns
    
    def find_npc_patterns(self, path: Path) -> List[Dict]:
        """Find NPC implementation patterns."""
        patterns = []
        
        for file_path in self._find_relevant_files(path, {'npc', 'monster', 'mob'}):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if self._is_npc_class(node):
                            patterns.append({
                                'file': str(file_path),
                                'class': node.name,
                                'methods': self._extract_methods(node)
                            })
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                
        return patterns
    
    def _find_relevant_files(self, path: Path, keywords: Set[str]) -> List[Path]:
        """Find files that might contain relevant code."""
        relevant_files = []
        
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(('.py', '.js', '.java')):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            if any(keyword in content for keyword in keywords):
                                relevant_files.append(file_path)
                    except Exception as e:
                        logger.error(f"Failed to read {file_path}: {e}")
                        
        return relevant_files
    
    def _is_minigame_class(self, node: ast.ClassDef) -> bool:
        """Check if a class is a minigame implementation."""
        name = node.name.lower()
        return any(term in name for term in ['minigame', 'game', 'activity'])
    
    def _is_combat_related(self, node: ast.AST) -> bool:
        """Check if a node is combat-related."""
        name = getattr(node, 'name', '').lower()
        return any(term in name for term in ['combat', 'battle', 'fight', 'attack'])
    
    def _is_skill_class(self, node: ast.ClassDef) -> bool:
        """Check if a class is a skill implementation."""
        name = node.name.lower()
        return any(term in name for term in ['skill', 'level', 'experience'])
    
    def _is_item_class(self, node: ast.ClassDef) -> bool:
        """Check if a class is an item implementation."""
        name = node.name.lower()
        return any(term in name for term in ['item', 'inventory', 'equipment'])
    
    def _is_npc_class(self, node: ast.ClassDef) -> bool:
        """Check if a class is an NPC implementation."""
        name = node.name.lower()
        return any(term in name for term in ['npc', 'monster', 'mob'])
    
    def _extract_methods(self, node: ast.ClassDef) -> List[str]:
        """Extract method names from a class."""
        return [n.name for n in node.body if isinstance(n, ast.FunctionDef)]

def main():
    """Main entry point."""
    analyzer = CodeAnalyzer()
    results = analyzer.analyze_all()
    
    # Print summary
    print("\nAnalysis Results:")
    for repo, patterns in results.items():
        print(f"\n{repo}:")
        for category, findings in patterns.items():
            print(f"  {category}: {len(findings)} patterns found")

if __name__ == "__main__":
    main() 