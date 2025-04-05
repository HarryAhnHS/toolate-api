# test script running on test_enhanced corpus + index, trained on about 1200 entries
from app.services.retriever import retrieve_top_k
from typing import List, Dict

def print_results(results: List[Dict]):
    print("\n🧠 Top Company Matches:\n" + "-"*40)
    for company in results:
        best_score = company['min_score']
        product_meta = company['product_meta']
        print(f"🏢 Company: {product_meta['meta']['name']}")
        print(f"🏢 Company website: {product_meta['meta']['website']}")
        print(f"⭐ Best Match Similarity Score: {best_score:.4f}")

        for match in company["matches"]:
            match_meta = match["match_meta"]
            score = match["score"]
            match_type = match["type"]

            if match_type == "description":
                name = match_meta['meta'].get("name", "Unknown")
                description = match_meta['text']
                tags = ", ".join(match_meta['meta'].get("tags", []))
                summary = match_meta.get("standardized", "[No summary]")

                print(f"\n🔹 [Description: {name}]")
                print(f"   Score: {score:.4f}")
                print(f"   Original description: {description[:50]}...")
                print(f"   Tags: {tags}")
                print(f"   Standardized description: {summary[:50]}...")
            elif match_type == "comment":
                product_name = match_meta['meta'].get("parent_name", "Unknown")
                comment = match_meta['text']
                summary = match_meta.get("standardized", "[No comment content]")

                print(f"\n💬 [Comment on: {product_name}]")
                print(f"   Score: {score:.4f}")
                print(f"   Original comment: {comment[:50]}...")
                print(f"   Standardized comment: {summary[:50]}...")

        print("\n" + "-"*40)


if __name__ == "__main__":
    query = input("🤖 Enter your startup idea: ").strip()
    if not query:
        print("⚠️  Please provide a valid startup idea.")
        exit(1)

    print(f"\n🔍 Searching for similar ideas to: “{query}”")
    results = retrieve_top_k(query, top_k=3)
    print_results(results)