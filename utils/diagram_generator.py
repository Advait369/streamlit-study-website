"""Diagram and Flowchart Generator

This module generates educational diagrams, flowcharts, and visualizations
using Mermaid, Matplotlib, and other libraries.
"""

import io
import base64
import logging
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

logger = logging.getLogger(__name__)

class DiagramGenerator:
    """
    Generates various types of educational diagrams and visualizations
    """
    
    def __init__(self):
        self.diagram_types = ['flowchart', 'concept_map', 'timeline', 'comparison', 'process']
        logger.info("Diagram generator initialized")
    
    def generate_mermaid_flowchart(self, topic: str, steps: List[str]) -> str:
        """
        Generate Mermaid flowchart syntax
        """
        mermaid_code = "graph TD\n"
        
        for i, step in enumerate(steps):
            node_id = f"A{i}"
            mermaid_code += f"    {node_id}[{step}]\n"
            if i > 0:
                mermaid_code += f"    A{i-1} --> {node_id}\n"
        
        return mermaid_code
    
    def generate_concept_map_mermaid(self, central_concept: str, related_concepts: List[str]) -> str:
        """
        Generate a concept map using Mermaid
        """
        mermaid_code = "graph LR\n"
        mermaid_code += f"    A[{central_concept}]\n"
        
        for i, concept in enumerate(related_concepts):
            node_id = f"B{i}"
            mermaid_code += f"    {node_id}[{concept}]\n"
            mermaid_code += f"    A --> {node_id}\n"
        
        return mermaid_code
    
    def generate_matplotlib_diagram(self, diagram_type: str, data: Dict) -> str:
        """
        Generate diagrams using Matplotlib and return as base64 encoded image
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if diagram_type == 'process_flow':
            self._draw_process_flow(ax, data)
        elif diagram_type == 'comparison':
            self._draw_comparison_chart(ax, data)
        elif diagram_type == 'timeline':
            self._draw_timeline(ax, data)
        else:
            self._draw_basic_diagram(ax, data)
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return img_base64
    
    def _draw_process_flow(self, ax, data: Dict):
        """
        Draw a process flow diagram
        """
        steps = data.get('steps', [])
        y_positions = np.linspace(0.9, 0.1, len(steps))
        
        for i, (step, y) in enumerate(zip(steps, y_positions)):
            # Draw box
            box = FancyBboxPatch(
                (0.2, y-0.05), 0.6, 0.08,
                boxstyle="round,pad=0.01",
                edgecolor='#1E88E5', facecolor='#E3F2FD',
                linewidth=2
            )
            ax.add_patch(box)
            
            # Add text
            ax.text(0.5, y, step, ha='center', va='center', fontsize=10, weight='bold')
            
            # Draw arrow to next step
            if i < len(steps) - 1:
                arrow = FancyArrowPatch(
                    (0.5, y-0.05), (0.5, y_positions[i+1]+0.05),
                    arrowstyle='->', mutation_scale=20, linewidth=2,
                    color='#1E88E5'
                )
                ax.add_patch(arrow)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title(data.get('title', 'Process Flow'), fontsize=14, weight='bold', pad=20)
    
    def _draw_comparison_chart(self, ax, data: Dict):
        """
        Draw a comparison chart
        """
        items = data.get('items', [])
        attributes = data.get('attributes', [])
        
        if not items or not attributes:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return
        
        # Create comparison table
        n_items = len(items)
        n_attrs = len(attributes)
        
        colors = ['#E3F2FD', '#FFFFFF']
        
        for i, item in enumerate(items):
            y = 0.9 - (i * 0.15)
            ax.text(0.1, y, item, fontsize=10, weight='bold')
            
            for j, attr in enumerate(attributes):
                x = 0.3 + (j * 0.2)
                color = colors[i % 2]
                rect = mpatches.Rectangle((x-0.08, y-0.05), 0.16, 0.08, 
                                          facecolor=color, edgecolor='#1E88E5')
                ax.add_patch(rect)
                ax.text(x, y, '✓', ha='center', va='center', fontsize=12)
        
        # Add attribute headers
        for j, attr in enumerate(attributes):
            x = 0.3 + (j * 0.2)
            ax.text(x, 0.95, attr, ha='center', fontsize=9, style='italic')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title(data.get('title', 'Comparison'), fontsize=14, weight='bold', pad=20)
    
    def _draw_timeline(self, ax, data: Dict):
        """
        Draw a timeline diagram
        """
        events = data.get('events', [])
        
        if not events:
            ax.text(0.5, 0.5, 'No events available', ha='center', va='center')
            return
        
        # Draw main timeline
        ax.plot([0.1, 0.9], [0.5, 0.5], 'k-', linewidth=3)
        
        n_events = len(events)
        x_positions = np.linspace(0.15, 0.85, n_events)
        
        for i, (x, event) in enumerate(zip(x_positions, events)):
            # Draw event marker
            ax.plot(x, 0.5, 'o', markersize=12, color='#1E88E5')
            
            # Add event label
            y_offset = 0.15 if i % 2 == 0 else -0.15
            ax.text(x, 0.5 + y_offset, event, ha='center', va='center',
                   fontsize=9, bbox=dict(boxstyle='round', facecolor='#E3F2FD'))
            
            # Draw connecting line
            ax.plot([x, x], [0.5, 0.5 + y_offset*0.7], 'k--', linewidth=1)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title(data.get('title', 'Timeline'), fontsize=14, weight='bold', pad=20)
    
    def _draw_basic_diagram(self, ax, data: Dict):
        """
        Draw a basic educational diagram
        """
        ax.text(0.5, 0.5, data.get('title', 'Diagram'),
               ha='center', va='center', fontsize=14, weight='bold')
        ax.axis('off')
    
    def create_educational_visualization(self, topic: str, viz_type: str, 
                                        content: str) -> Dict[str, Any]:
        """
        Create an appropriate visualization based on content analysis
        """
        result = {
            'type': viz_type,
            'code': None,
            'image': None,
            'success': False
        }
        
        try:
            if viz_type == 'mermaid_flowchart':
                # Parse content to extract steps
                steps = self._extract_steps_from_content(content)
                result['code'] = self.generate_mermaid_flowchart(topic, steps)
                result['success'] = True
            
            elif viz_type == 'concept_map':
                concepts = self._extract_concepts_from_content(content)
                result['code'] = self.generate_concept_map_mermaid(topic, concepts)
                result['success'] = True
            
            elif viz_type in ['process_flow', 'comparison', 'timeline']:
                diagram_data = self._prepare_matplotlib_data(content, viz_type)
                result['image'] = self.generate_matplotlib_diagram(viz_type, diagram_data)
                result['success'] = True
            
            logger.info(f"Successfully created {viz_type} visualization for {topic}")
        
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    def _extract_steps_from_content(self, content: str) -> List[str]:
        """
        Extract process steps from content
        """
        # Simple extraction - look for numbered lists or process indicators
        lines = content.split('\n')
        steps = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Clean up the line
                cleaned = line.lstrip('0123456789.-• ').strip()
                if cleaned:
                    steps.append(cleaned[:50])  # Limit length
        
        return steps[:8] if steps else ["Step 1", "Step 2", "Step 3"]
    
    def _extract_concepts_from_content(self, content: str) -> List[str]:
        """
        Extract key concepts from content
        """
        # Simple extraction - this should be enhanced with NLP
        words = content.split()
        concepts = []
        
        # Look for capitalized words or important terms
        for word in words:
            if word and word[0].isupper() and len(word) > 3:
                concepts.append(word.strip('.,!?'))
                if len(concepts) >= 6:
                    break
        
        return concepts if concepts else ["Concept 1", "Concept 2", "Concept 3"]
    
    def _prepare_matplotlib_data(self, content: str, viz_type: str) -> Dict:
        """
        Prepare data structure for matplotlib diagrams
        """
        if viz_type == 'process_flow':
            return {
                'title': 'Process Flow',
                'steps': self._extract_steps_from_content(content)
            }
        elif viz_type == 'timeline':
            return {
                'title': 'Timeline',
                'events': self._extract_steps_from_content(content)
            }
        elif viz_type == 'comparison':
            return {
                'title': 'Comparison',
                'items': ['Item A', 'Item B'],
                'attributes': ['Feature 1', 'Feature 2', 'Feature 3']
            }
        return {'title': 'Diagram'}
