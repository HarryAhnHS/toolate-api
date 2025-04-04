# scripts/test_retrieve.py

import sys
from app.services.retrieval import retrieve_top_k

def print_results(results):
    print("\n🧠 Top Description Matches:\n" + "-"*40)
    for item in results['descriptions']:
        print(f"- [{item['meta']['name']}]")
        print(f"  Score: {item['score']:.4f}")
        print(f"  Tags: {', '.join(item['meta'].get('meta', {}).get('tags', []))}")
        print(f"  Summary: {item['standardized'][:200]}...\n")

    print("\n💬 Top Comment Matches:\n" + "-"*40)
    for item in results['comments']:
        print(f"- Parent: [{item['meta']['parent_name']}]")
        print(f"  Score: {item['score']:.4f}")
        print(f"  Snippet: {item['standardized'][:200]}...\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.tests.test_retrieve 'your startup idea here'")
        sys.exit(1)

    query = sys.argv[1]
    print(f"\n🔍 Searching for similar ideas to: “{query}”")
    results = retrieve_top_k(query, top_k=5)

    print_results(results)
