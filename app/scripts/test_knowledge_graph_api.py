import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"  # Adjust if your API runs on a different port

def test_semantic_search():
    """Test semantic search endpoint"""
    print("\n=== Testing Semantic Search ===")
    response = requests.post(
        f"{BASE_URL}/query-knowledge-graph",
        json={
            "query": "What are the DTI requirements?",
            "search_type": "semantic",
            "max_results": 3
        }
    )
    
    if response.status_code == 200:
        results = response.json()
        print("\nSemantic Search Results:")
        for idx, result in enumerate(results["results"], 1):
            print(f"\n{idx}. Guideline: {result['guideline'].get('title', 'No title')}")
            print(f"   Similarity Score: {result['similarity_score']:.2f}")
            print(f"   Content Preview: {result['guideline'].get('content', '')[:200]}...")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_multi_hop_search():
    """Test multi-hop search endpoint"""
    print("\n=== Testing Multi-hop Search ===")
    response = requests.post(
        f"{BASE_URL}/query-knowledge-graph",
        json={
            "query": "DTI requirements",
            "search_type": "multi_hop",
            "max_hops": 2,
            "max_results": 2
        }
    )
    
    if response.status_code == 200:
        results = response.json()
        print("\nMulti-hop Search Results:")
        for idx, result in enumerate(results["results"], 1):
            print(f"\nPath {idx}:")
            for node_idx, node in enumerate(result["path"]):
                print(f"  {node_idx + 1}. {node.get('title', 'No title')}")
            print("  Relationships:")
            for rel in result["relationships"]:
                print(f"    - {rel['type']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_context_search():
    """Test context search endpoint"""
    print("\n=== Testing Context Search ===")
    response = requests.post(
        f"{BASE_URL}/query-knowledge-graph",
        json={
            "query": "DTI requirements",
            "search_type": "context",
            "max_results": 2
        }
    )
    
    if response.status_code == 200:
        results = response.json()
        print("\nContext Search Results:")
        for idx, result in enumerate(results["results"], 1):
            print(f"\n{idx}. Main Guideline: {result['guideline'].get('title', 'No title')}")
            print(f"   Content Preview: {result['guideline'].get('content', '')[:200]}...")
            print("\n   Related Guidelines:")
            for rel_idx, related in enumerate(result["related_guidelines"], 1):
                print(f"     {rel_idx}. {related['guideline'].get('title', 'No title')}")
                print(f"        Relationship: {related['relationship']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def main():
    """Run all tests"""
    print("Starting Knowledge Graph API Tests...")
    
    # Test semantic search
    test_semantic_search()
    
    # Test multi-hop search
    test_multi_hop_search()
    
    # Test context search
    test_context_search()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 