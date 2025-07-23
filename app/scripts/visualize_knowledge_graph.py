import networkx as nx
import matplotlib.pyplot as plt
from app.db.session import SessionLocal
from app.models.knowledge_graph import GuidelineNode, guideline_relationships
import json

def visualize_knowledge_graph():
    """Visualize the knowledge graph using NetworkX"""
    db = SessionLocal()
    
    try:
        # Create a directed graph
        G = nx.DiGraph()
        
        # Get all guidelines
        guidelines = db.query(GuidelineNode).all()
        
        # Add nodes
        for guideline in guidelines:
            G.add_node(
                guideline.id,
                title=guideline.title,
                category=guideline.category,
                content=guideline.content[:100] + "..."  # Truncate content for display
            )
        
        # Add edges based on relationships
        relationships = db.query(guideline_relationships).all()
        for rel in relationships:
            G.add_edge(
                rel.source_id,
                rel.target_id,
                relationship=rel.relationship_type
            )
        
        # Create the visualization
        plt.figure(figsize=(15, 10))
        
        # Use different colors for different categories
        categories = set(nx.get_node_attributes(G, 'category').values())
        color_map = plt.cm.get_cmap('tab20', len(categories))
        category_colors = {cat: color_map(i) for i, cat in enumerate(categories)}
        
        # Get node colors based on category
        node_colors = [category_colors[G.nodes[node]['category']] for node in G.nodes()]
        
        # Layout
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2000, alpha=0.7)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=20)
        
        # Add labels
        labels = {node: G.nodes[node]['title'] for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')
        
        # Add edge labels
        edge_labels = nx.get_edge_attributes(G, 'relationship')
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6)
        
        # Add legend for categories
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=category_colors[cat], label=cat, markersize=10)
            for cat in categories
        ]
        plt.legend(handles=legend_elements, title="Categories", loc='upper right', bbox_to_anchor=(1.1, 1))
        
        # Save the visualization
        plt.title("Fannie Mae Guidelines Knowledge Graph")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig('knowledge_graph.png', dpi=300, bbox_inches='tight')
        print("Knowledge graph visualization saved as 'knowledge_graph.png'")
        
        # Create an interactive HTML visualization
        import plotly.graph_objects as go
        
        # Create edge trace
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(
                f"Title: {G.nodes[node]['title']}<br>"
                f"Category: {G.nodes[node]['category']}<br>"
                f"Content: {G.nodes[node]['content']}"
            )
            node_colors.append(category_colors[G.nodes[node]['category']])
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[G.nodes[node]['title'] for node in G.nodes()],
            textposition="top center",
            marker=dict(
                showscale=False,
                color=node_colors,
                size=20,
                line_width=2
            )
        )
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Interactive Fannie Mae Guidelines Knowledge Graph',
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                       )
        
        # Save interactive visualization
        fig.write_html('knowledge_graph_interactive.html')
        print("Interactive knowledge graph visualization saved as 'knowledge_graph_interactive.html'")
        
    except Exception as e:
        print(f"Error creating visualization: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    visualize_knowledge_graph() 