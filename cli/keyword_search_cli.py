import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Keyword Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    search_parser = subparsers.add_parser("search", help="Search movies using keywords")
    search_parser.add_argument("query", type=str, help="Search query")

    args = parser.parse_args()

    match args.command:
        case "search":
            with open("data/movies.json", "r") as file:
                data = json.load(file)
            filtered_movies = []
            for movie in data.get("movies", []):
                if args.query in movie.get("title", ""):
                    filtered_movies.append(movie)

            print(f"Searching for: {args.query}")
            for index, fm in enumerate(filtered_movies[:5], start=1):
                print(f"{index}. {fm.get('title')}")
        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
