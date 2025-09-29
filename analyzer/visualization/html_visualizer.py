"""
HTML Interactive Visualizer - Atlas Project Trees

Generates beautiful, interactive HTML visualizations that can be opened in any browser.
Self-contained single-file output with embedded CSS and JavaScript.
"""

import json
from typing import Dict, Any, List


class HTMLVisualizer:
    """Generates interactive HTML visualizations of Atlas project trees."""
    
    def __init__(self):
        pass
    
    def generate(self, project_node) -> str:
        """
        Generate a complete HTML document for the project tree.
        
        Args:
            project_node: The root ProjectNode to visualize
            
        Returns:
            Complete HTML string that can be saved to a file
        """
        # Convert tree to JSON structure
        tree_data = self._convert_to_dict(project_node)
        
        # Generate complete HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Atlas Visualization - {project_node.name}</title>
    {self._get_styles()}
</head>
<body>
    <div id="root"></div>
    <script>
        const TREE_DATA = {json.dumps(tree_data, indent=2)};
    </script>
    {self._get_javascript()}
</body>
</html>"""
        return html
    
    def save(self, project_node, filepath: str = "atlas_visualization.html"):
        """
        Generate and save HTML visualization to a file.
        
        Args:
            project_node: The root ProjectNode to visualize
            filepath: Path where HTML file should be saved
        """
        html = self.generate(project_node)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✓ Interactive visualization saved to: {filepath}")
        print(f"  Open in browser to explore the tree")
    
    def _convert_to_dict(self, node) -> Dict[str, Any]:
        """Convert an Atlas node to a dictionary structure for JSON serialization."""
        node_type = node.__class__.__name__.replace('Node', '')
        
        # Extract name based on node type
        if hasattr(node, 'name'):
            node_name = node.name
        elif node_type == 'StateContainer':
            node_name = 'module_state'
        elif node_type == 'Type':
            # TypeNode might not have a name, use repr or something sensible
            node_name = repr(node).replace('Type(', '').replace(')', '') if hasattr(node, '__repr__') else 'type'
        else:
            node_name = node_type.lower()
        
        result = {
            'type': node_type,
            'name': node_name,
            'line': node.line_number if hasattr(node, 'line_number') else None,
            'children': []
        }
        
        # Check for violations
        if hasattr(node, '_violations') and node._violations:
            result['hasViolation'] = True
            result['violations'] = [
                {
                    'type': v.__class__.__name__,
                    'message': str(v)
                }
                for v in node._violations
            ]
        
        # Check for type information
        if hasattr(node, '_type') and node._type is not None:
            result['hasType'] = True
        
        # Collect children from all possible collections
        children = self._get_all_children(node)
        result['children'] = [self._convert_to_dict(child) for child in children]
        
        return result
    
    def _get_all_children(self, node) -> List:
        """Get all children from various collection attributes."""
        children = []
        
        # Check all possible collection attributes
        # These are the actual attribute names used in Atlas nodes
        collection_attrs = [
            '_packages',
            '_modules', 
            '_classes',
            '_functions',
            '_arguments',
            '_class_attributes',
            '_instance_attributes',
            '_imports',
            '_from_imports',
            '_state'
        ]
        
        for attr in collection_attrs:
            if hasattr(node, attr):
                collection = getattr(node, attr)
                if isinstance(collection, list) and collection:
                    children.extend(collection)
        
        # Single children (like return)
        if hasattr(node, '_return') and node._return is not None:
            children.append(node._return)
        
        # Type child
        if hasattr(node, '_type') and node._type is not None:
            children.append(node._type)
        
        return children
    
    def _get_styles(self) -> str:
        """Return embedded CSS styles."""
        return """<style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #e5e7eb;
            line-height: 1.6;
        }
        
        #root {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .header {
            margin-bottom: 2rem;
        }
        
        .title {
            font-size: 2rem;
            font-weight: bold;
            color: white;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .subtitle {
            color: #9ca3af;
            font-size: 0.875rem;
        }
        
        .stats {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }
        
        .stat-card {
            background: #1a1a24;
            border: 1px solid #2d2d3a;
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .stat-value {
            font-size: 1.5rem;
            font-weight: 600;
            margin-top: 0.25rem;
        }
        
        .controls {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }
        
        .search-box {
            flex: 1;
            min-width: 300px;
            position: relative;
        }
        
        .search-input {
            width: 100%;
            background: #1a1a24;
            border: 1px solid #2d2d3a;
            border-radius: 0.5rem;
            padding: 0.625rem 0.75rem 0.625rem 2.5rem;
            color: #e5e7eb;
            font-size: 0.875rem;
        }
        
        .search-input:focus {
            outline: none;
            border-color: #8b5cf6;
        }
        
        .search-icon {
            position: absolute;
            left: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            color: #6b7280;
        }
        
        .filter-btn {
            padding: 0.625rem 1rem;
            background: #1a1a24;
            border: 1px solid #2d2d3a;
            border-radius: 0.5rem;
            color: #9ca3af;
            cursor: pointer;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.2s;
        }
        
        .filter-btn:hover {
            border-color: #3d3d4a;
        }
        
        .filter-btn.active {
            background: rgba(239, 68, 68, 0.1);
            border-color: #7f1d1d;
            color: #f87171;
        }
        
        .tree-container {
            background: #1a1a24;
            border: 1px solid #2d2d3a;
            border-radius: 0.5rem;
            padding: 1rem;
            max-height: 70vh;
            overflow: auto;
        }
        
        .tree-node {
            user-select: none;
        }
        
        .node-content {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.375rem 0.5rem;
            border-radius: 0.375rem;
            cursor: pointer;
            transition: background 0.15s;
        }
        
        .node-content:hover {
            background: #2d2d3a;
        }
        
        .node-content.has-violation {
            background: rgba(127, 29, 29, 0.2);
        }
        
        .chevron {
            width: 1rem;
            height: 1rem;
            color: #6b7280;
            flex-shrink: 0;
        }
        
        .node-icon {
            width: 1rem;
            height: 1rem;
            flex-shrink: 0;
        }
        
        .node-name {
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.875rem;
        }
        
        .node-name.violation {
            color: #f87171;
        }
        
        .node-line {
            margin-left: auto;
            font-size: 0.75rem;
            color: #6b7280;
        }
        
        .badge {
            font-size: 0.75rem;
            padding: 0.125rem 0.375rem;
            border-radius: 0.25rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }
        
        .badge-typed {
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
        }
        
        .badge-violation {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
        }
        
        .badge-count {
            background: rgba(239, 68, 68, 0.1);
            color: #fca5a5;
            margin-left: auto;
        }
        
        .children {
            margin-left: 1.25rem;
        }
        
        .legend {
            margin-top: 1.5rem;
            background: #1a1a24;
            border: 1px solid #2d2d3a;
            border-radius: 0.5rem;
            padding: 1rem;
        }
        
        .legend-title {
            font-size: 0.875rem;
            font-weight: 600;
            color: #d1d5db;
            margin-bottom: 0.75rem;
        }
        
        .legend-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.75rem;
            font-size: 0.75rem;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #9ca3af;
        }
        
        /* Icon colors */
        .icon-project { color: #a78bfa; }
        .icon-package { color: #60a5fa; }
        .icon-module { color: #34d399; }
        .icon-class { color: #fbbf24; }
        .icon-function { color: #fb923c; }
        .icon-argument { color: #9ca3af; }
        .icon-attribute { color: #22d3ee; }
        </style>"""
    
    def _get_javascript(self) -> str:
        """Return embedded JavaScript code."""
        return """<script>
        class TreeNode {
            constructor(data, level = 0) {
                this.data = data;
                this.level = level;
                this.isExpanded = level < 2;
            }
            
            render(container, searchTerm, showViolationsOnly) {
                const hasChildren = this.data.children && this.data.children.length > 0;
                const hasViolation = this.data.hasViolation;
                const matchesSearch = !searchTerm || 
                    this.data.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    this.data.type.toLowerCase().includes(searchTerm.toLowerCase());
                
                if (!matchesSearch && this.level > 0) return;
                if (showViolationsOnly && !hasViolation && this.level > 0) return;
                
                const nodeDiv = document.createElement('div');
                nodeDiv.className = 'tree-node';
                
                const contentDiv = document.createElement('div');
                contentDiv.className = `node-content ${hasViolation ? 'has-violation' : ''}`;
                contentDiv.style.paddingLeft = `${this.level * 1.25 + 0.5}rem`;
                
                if (hasChildren) {
                    const chevron = this.createChevron();
                    contentDiv.appendChild(chevron);
                    contentDiv.onclick = () => {
                        this.isExpanded = !this.isExpanded;
                        this.render(container, searchTerm, showViolationsOnly);
                    };
                } else {
                    const spacer = document.createElement('div');
                    spacer.style.width = '1rem';
                    contentDiv.appendChild(spacer);
                }
                
                contentDiv.appendChild(this.createIcon());
                
                const nameSpan = document.createElement('span');
                nameSpan.className = `node-name ${hasViolation ? 'violation' : ''}`;
                nameSpan.textContent = this.data.name;
                contentDiv.appendChild(nameSpan);
                
                if (this.data.line) {
                    const lineSpan = document.createElement('span');
                    lineSpan.className = 'node-line';
                    lineSpan.textContent = `:${this.data.line}`;
                    contentDiv.appendChild(lineSpan);
                }
                
                if (this.data.hasType) {
                    const typeBadge = document.createElement('span');
                    typeBadge.className = 'badge badge-typed';
                    typeBadge.textContent = 'typed';
                    contentDiv.appendChild(typeBadge);
                }
                
                if (hasViolation && this.data.violations) {
                    const violationBadge = document.createElement('span');
                    violationBadge.className = 'badge badge-violation';
                    violationBadge.innerHTML = '⚠ ' + this.data.violations[0].type.replace('Missing', '').replace('TypeHint', '');
                    contentDiv.appendChild(violationBadge);
                }
                
                nodeDiv.appendChild(contentDiv);
                
                if (hasChildren && this.isExpanded) {
                    const childrenDiv = document.createElement('div');
                    childrenDiv.className = 'children';
                    this.data.children.forEach(childData => {
                        const childNode = new TreeNode(childData, this.level + 1);
                        childNode.render(childrenDiv, searchTerm, showViolationsOnly);
                    });
                    nodeDiv.appendChild(childrenDiv);
                }
                
                container.innerHTML = '';
                container.appendChild(nodeDiv);
            }
            
            createChevron() {
                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.setAttribute('class', 'chevron');
                svg.setAttribute('viewBox', '0 0 24 24');
                svg.setAttribute('fill', 'none');
                svg.setAttribute('stroke', 'currentColor');
                svg.setAttribute('stroke-width', '2');
                
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                if (this.isExpanded) {
                    path.setAttribute('d', 'M19 9l-7 7-7-7');
                } else {
                    path.setAttribute('d', 'M9 5l7 7-7 7');
                }
                svg.appendChild(path);
                return svg;
            }
            
            createIcon() {
                const iconMap = {
                    'Project': '📦',
                    'Package': '📁',
                    'Module': '📄',
                    'Class': '🏛️',
                    'Function': '⚡',
                    'Argument': '◦',
                    'ClassAttribute': '🔷',
                    'InstanceAttribute': '🔶',
                    'Return': '↩️',
                    'Type': '🏷️',
                    'Import': '📥',
                    'ImportFrom': '📥',
                    'Alias': '🔗',
                    'State': '📊',
                    'StateContainer': '📦'
                };
                
                const span = document.createElement('span');
                span.className = 'node-icon';
                span.textContent = iconMap[this.data.type] || '•';
                return span;
            }
        }
        
        function countNodes(node, acc = {}) {
            const type = node.type;
            acc[type] = (acc[type] || 0) + 1;
            if (node.hasViolation) {
                acc.violations = (acc.violations || 0) + 1;
            }
            if (node.children) {
                node.children.forEach(child => countNodes(child, acc));
            }
            return acc;
        }
        
        function renderApp() {
            const stats = countNodes(TREE_DATA);
            
            const root = document.getElementById('root');
            root.innerHTML = `
                <div class="header">
                    <div class="title">
                        📦 Atlas Project Visualizer
                    </div>
                    <div class="subtitle">Interactive tree exploration with type analysis</div>
                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-label">Modules</div>
                            <div class="stat-value" style="color: #34d399;">${stats.Module || 0}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Classes</div>
                            <div class="stat-value" style="color: #fbbf24;">${stats.Class || 0}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Functions</div>
                            <div class="stat-value" style="color: #fb923c;">${stats.Function || 0}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Violations</div>
                            <div class="stat-value" style="color: #f87171;">${stats.violations || 0}</div>
                        </div>
                    </div>
                </div>
                
                <div class="controls">
                    <div class="search-box">
                        <span class="search-icon">🔍</span>
                        <input type="text" id="searchInput" class="search-input" placeholder="Search nodes...">
                    </div>
                    <button id="filterBtn" class="filter-btn">
                        🔴 Violations Only
                    </button>
                </div>
                
                <div class="tree-container" id="treeContainer"></div>
                
                <div class="legend">
                    <div class="legend-title">Legend</div>
                    <div class="legend-grid">
                        <div class="legend-item"><span>📦</span> Project</div>
                        <div class="legend-item"><span>📁</span> Package</div>
                        <div class="legend-item"><span>📄</span> Module</div>
                        <div class="legend-item"><span>🏛️</span> Class</div>
                        <div class="legend-item"><span>⚡</span> Function/Method</div>
                        <div class="legend-item"><span>◦</span> Argument</div>
                        <div class="legend-item"><span>🔷</span> Class Attribute</div>
                        <div class="legend-item"><span>🔶</span> Instance Attribute</div>
                        <div class="legend-item"><span>↩️</span> Return</div>
                        <div class="legend-item"><span>🏷️</span> Type</div>
                    </div>
                </div>
            `;
            
            let searchTerm = '';
            let showViolationsOnly = false;
            const treeContainer = document.getElementById('treeContainer');
            const rootNode = new TreeNode(TREE_DATA);
            
            function update() {
                rootNode.render(treeContainer, searchTerm, showViolationsOnly);
            }
            
            document.getElementById('searchInput').addEventListener('input', (e) => {
                searchTerm = e.target.value;
                update();
            });
            
            document.getElementById('filterBtn').addEventListener('click', (e) => {
                showViolationsOnly = !showViolationsOnly;
                e.target.classList.toggle('active');
                update();
            });
            
            update();
        }
        
        renderApp();
        </script>"""