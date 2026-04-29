from engine import ResourceEngine


def run_terminal():
    engine = ResourceEngine()
    print("\n" + "=" * 40)
    print("COMMUNITY RESOURCE FINDER: TERMINAL MODE")
    print("=" * 40)

    while True:
        query = input("\nHow can we help? (or 'q' to quit): ")
        if query.lower() in ["q", "exit", "quit"]:
            break

        results = engine.search(query, top_k=3)
        for index, resource in enumerate(results, start=1):
            print(f"\n{index}. RECOMMENDED: {resource['name']}")
            print(f"   CATEGORY: {resource['category']} | CITY: {resource['city']}")
            print(f"   ADDRESS: {resource['location']}")
        print("---")


if __name__ == "__main__":
    run_terminal()
