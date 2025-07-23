import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch
import matplotlib.patches as mpatches

# Set up the figure with high resolution
plt.rcParams['figure.figsize'] = (20, 16)
plt.rcParams['figure.dpi'] = 300
fig, ax = plt.subplots(1, 1, facecolor='white')

# Define colors
colors = {
    'client': '#e1f5fe',
    'api': '#f3e5f5', 
    'service': '#e8f5e8',
    'data': '#fff3e0',
    'external': '#ffebee',
    'border': '#333333',
    'text': '#2c3e50'
}

# Define component positions and sizes
components = {
    # External Clients
    'web_app': {'pos': (2, 14), 'size': (3, 1), 'color': colors['client'], 'label': 'Web Application'},
    'api_client': {'pos': (6, 14), 'size': (3, 1), 'color': colors['client'], 'label': 'API Client'},
    'mobile': {'pos': (10, 14), 'size': (3, 1), 'color': colors['client'], 'label': 'Mobile App'},
    
    # API Gateway Layer
    'load_balancer': {'pos': (6, 12.5), 'size': (4, 0.8), 'color': colors['api'], 'label': 'Load Balancer'},
    'api_gateway': {'pos': (6, 11.5), 'size': (4, 0.8), 'color': colors['api'], 'label': 'API Gateway'},
    
    # FastAPI Application Layer
    'fastapi': {'pos': (6, 10), 'size': (4, 1), 'color': colors['api'], 'label': 'FastAPI Application'},
    
    # API Endpoints
    'validate': {'pos': (1, 8.5), 'size': (2.5, 0.6), 'color': colors['api'], 'label': '/validate-application'},
    'query': {'pos': (4, 8.5), 'size': (2.5, 0.6), 'color': colors['api'], 'label': '/query-knowledge-graph'},
    'compare': {'pos': (7, 8.5), 'size': (2.5, 0.6), 'color': colors['api'], 'label': '/compare-query-approaches'},
    'process': {'pos': (10, 8.5), 'size': (2.5, 0.6), 'color': colors['api'], 'label': '/process-documents'},
    
    # Core Services
    'loan_validator': {'pos': (1, 7), 'size': (2.5, 0.8), 'color': colors['service'], 'label': 'Loan Validator'},
    'loan_converter': {'pos': (4, 7), 'size': (2.5, 0.8), 'color': colors['service'], 'label': 'Loan Converter'},
    'pdf_processor': {'pos': (7, 7), 'size': (2.5, 0.8), 'color': colors['service'], 'label': 'PDF Processor'},
    'neo4j_service': {'pos': (10, 7), 'size': (2.5, 0.8), 'color': colors['service'], 'label': 'Neo4j Service'},
    
    # Knowledge Graph Services
    'semantic_search': {'pos': (1, 5.5), 'size': (2.5, 0.6), 'color': colors['service'], 'label': 'Semantic Search'},
    'multi_hop': {'pos': (4, 5.5), 'size': (2.5, 0.6), 'color': colors['service'], 'label': 'Multi-Hop Search'},
    'context_search': {'pos': (7, 5.5), 'size': (2.5, 0.6), 'color': colors['service'], 'label': 'Context Search'},
    'ai_recommendations': {'pos': (10, 5.5), 'size': (2.5, 0.6), 'color': colors['service'], 'label': 'AI Recommendations'},
    
    # LLM Integration
    'openai_client': {'pos': (1, 4), 'size': (2.5, 0.8), 'color': colors['service'], 'label': 'OpenAI Client'},
    'chain_of_thought': {'pos': (4, 4), 'size': (2.5, 0.8), 'color': colors['service'], 'label': 'Chain of Thought'},
    'evaluation_engine': {'pos': (7, 4), 'size': (2.5, 0.8), 'color': colors['service'], 'label': 'Evaluation Engine'},
    'response_generation': {'pos': (10, 4), 'size': (2.5, 0.8), 'color': colors['service'], 'label': 'Response Generation'},
    
    # Data Layer
    'neo4j_db': {'pos': (6, 2.5), 'size': (4, 1), 'color': colors['data'], 'label': 'Neo4j Database'},
    'guidelines': {'pos': (1, 1.5), 'size': (2.5, 0.6), 'color': colors['data'], 'label': 'Guidelines'},
    'relationships': {'pos': (4, 1.5), 'size': (2.5, 0.6), 'color': colors['data'], 'label': 'Relationships'},
    'embeddings': {'pos': (7, 1.5), 'size': (2.5, 0.6), 'color': colors['data'], 'label': 'Embeddings'},
    'file_storage': {'pos': (10, 1.5), 'size': (2.5, 0.6), 'color': colors['data'], 'label': 'File Storage'},
    
    # External Services
    'openai_api': {'pos': (15, 4), 'size': (3, 1), 'color': colors['external'], 'label': 'OpenAI API'},
    'embedding_api': {'pos': (15, 2.5), 'size': (3, 1), 'color': colors['external'], 'label': 'Embedding API'},
}

# Draw components
for name, comp in components.items():
    x, y = comp['pos']
    w, h = comp['size']
    
    # Create rounded rectangle
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.1",
        facecolor=comp['color'],
        edgecolor=colors['border'],
        linewidth=1.5
    )
    ax.add_patch(box)
    
    # Add label
    ax.text(x + w/2, y + h/2, comp['label'], 
            ha='center', va='center', fontsize=8, fontweight='bold',
            color=colors['text'])

# Draw layer labels
layer_labels = [
    ('External Clients', 15.5, 14.5),
    ('API Gateway Layer', 15.5, 12),
    ('FastAPI Application', 15.5, 10.5),
    ('API Endpoints', 15.5, 8.8),
    ('Core Services', 15.5, 7.4),
    ('Knowledge Graph Services', 15.5, 5.8),
    ('LLM Integration', 15.5, 4.4),
    ('Data Layer', 15.5, 3),
    ('External Services', 15.5, 1.5)
]

for label, x, y in layer_labels:
    ax.text(x, y, label, fontsize=10, fontweight='bold', 
            color=colors['text'], rotation=90, va='center')

# Draw connections
connections = [
    # Client to Load Balancer
    ('web_app', 'load_balancer'),
    ('api_client', 'load_balancer'),
    ('mobile', 'load_balancer'),
    
    # Load Balancer to API Gateway
    ('load_balancer', 'api_gateway'),
    
    # API Gateway to FastAPI
    ('api_gateway', 'fastapi'),
    
    # FastAPI to Endpoints
    ('fastapi', 'validate'),
    ('fastapi', 'query'),
    ('fastapi', 'compare'),
    ('fastapi', 'process'),
    
    # Endpoints to Services
    ('validate', 'loan_validator'),
    ('query', 'neo4j_service'),
    ('compare', 'neo4j_service'),
    ('compare', 'openai_client'),
    ('process', 'pdf_processor'),
    
    # Service connections
    ('loan_validator', 'loan_converter'),
    ('loan_validator', 'neo4j_service'),
    ('loan_validator', 'openai_client'),
    
    # Knowledge Graph Services to Neo4j
    ('semantic_search', 'neo4j_db'),
    ('multi_hop', 'neo4j_db'),
    ('context_search', 'neo4j_db'),
    ('ai_recommendations', 'neo4j_db'),
    ('neo4j_service', 'neo4j_db'),
    
    # LLM Integration
    ('chain_of_thought', 'openai_client'),
    ('evaluation_engine', 'openai_client'),
    ('response_generation', 'openai_client'),
    
    # External API connections
    ('openai_client', 'openai_api'),
    ('semantic_search', 'embedding_api'),
    
    # Data connections
    ('neo4j_db', 'guidelines'),
    ('neo4j_db', 'relationships'),
    ('neo4j_db', 'embeddings'),
    ('pdf_processor', 'file_storage'),
]

# Draw arrows
for start, end in connections:
    start_pos = components[start]['pos']
    start_size = components[start]['size']
    end_pos = components[end]['pos']
    end_size = components[end]['size']
    
    # Calculate arrow start and end points
    start_x = start_pos[0] + start_size[0]/2
    start_y = start_pos[1] + start_size[1]/2
    end_x = end_pos[0] + end_size[0]/2
    end_y = end_pos[1] + end_size[1]/2
    
    # Create arrow
    arrow = FancyArrowPatch(
        (start_x, start_y), (end_x, end_y),
        arrowstyle='->', mutation_scale=20,
        color='#666666', linewidth=1.5,
        connectionstyle="arc3,rad=0.1"
    )
    ax.add_patch(arrow)

# Add title
ax.text(6, 16, 'Knowledge Graph Based Loan Validator and Querying System', 
        fontsize=16, fontweight='bold', ha='center', color=colors['text'])

# Add subtitle
ax.text(6, 15.5, 'System Architecture Diagram', 
        fontsize=12, ha='center', color=colors['text'])

# Set axis limits and remove axes
ax.set_xlim(0, 19)
ax.set_ylim(0, 17)
ax.axis('off')

# Add legend
legend_elements = [
    patches.Patch(color=colors['client'], label='External Clients'),
    patches.Patch(color=colors['api'], label='API Layer'),
    patches.Patch(color=colors['service'], label='Core Services'),
    patches.Patch(color=colors['data'], label='Data Layer'),
    patches.Patch(color=colors['external'], label='External Services')
]

ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))

# Add key features text
features_text = """
Key Features:
• Intelligent Loan Validation with AI reasoning
• Multi-hop Knowledge Graph Search
• Chain-of-Thought Analysis
• Comprehensive Response Evaluation
• Real-time Processing & Scalable Architecture
"""

ax.text(0.5, 0.5, features_text, fontsize=10, 
        bbox=dict(boxstyle="round,pad=0.5", facecolor='#f8f9fa', alpha=0.8),
        transform=ax.transAxes, verticalalignment='bottom')

plt.tight_layout()
plt.savefig('system_architecture.png', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
plt.show()

print("System architecture diagram saved as 'system_architecture.png'") 