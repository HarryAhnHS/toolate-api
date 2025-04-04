# test script running on test_enhanced corpus + index, trained on about 1200 entries
from app.services.retrieval import retrieve_top_k

def print_results(results):
    print("\n🧠 Top Description Matches:\n" + "-"*40)
    for item in results['descriptions']:
        print(f"- [{item['meta']['name']}]")
        print(f"  Score: {item['score']:.4f}")
        print(f"  Tags: {', '.join(item['meta'].get('meta', {}).get('tags', []))}")
        print(f"  Summary: {item['standardized']}...\n")

    print("\n💬 Top Comment Matches:\n" + "-"*40)
    for item in results['comments']:
        print(f"- Parent: [{item['meta']['parent_name']}]")
        print(f"  Score: {item['score']:.4f}")
        print(f"  Snippet: {item['standardized']}...\n")

if __name__ == "__main__":
    query = input("🤖 Enter your startup idea: ").strip()
    if not query:
        print("⚠️  Please provide a valid startup idea.")
        exit(1)

    print(f"\n🔍 Searching for similar ideas to: “{query}”")
    results = retrieve_top_k(query, top_k=3)

    print_results(results)