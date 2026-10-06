import argparse
import json
import string

PUNCTUATION_TABLE = str.maketrans("", "", string.punctuation)
MAX_RESULTS = 5


def normalize(text: str) -> str:
    return text.lower().translate(PUNCTUATION_TABLE)


def tokenize(text: str, stop_words: list[str]) -> list[str]:
    tokens = []
    for token in normalize(text).split():
        if token not in stop_words:
            tokens.append(token)
    return tokens


def load_stop_words() -> list[str]:
    with open("data/stopwords.txt", "r") as f:
        words = f.read().splitlines()

    stop_words = []
    for word in words:
        stop_words.append(normalize(word))
    return stop_words


def has_matching_token(query_tokens: list[str], title_tokens: list[str]) -> bool:
    for query_token in query_tokens:
        for title_token in title_tokens:
            if query_token in title_token:
                return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Keyword Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    search_parser = subparsers.add_parser("search", help="Search movies using keywords")
    search_parser.add_argument("query", type=str, help="Search query")

    args = parser.parse_args()

    match args.command:
        case "search":
            with open("data/movies.json", "r") as f:
                movie_data = json.load(f)
            stop_words = load_stop_words()

            query_tokens = tokenize(args.query, stop_words)
            filtered_movies = []
            for movie in movie_data.get("movies", []):
                title_tokens = tokenize(movie.get("title", ""), stop_words)
                if has_matching_token(query_tokens, title_tokens):
                    filtered_movies.append(movie)
                    if len(filtered_movies) == MAX_RESULTS:
                        break

            print(f"Searching for: {args.query}")
            for index, fm in enumerate(filtered_movies, start=1):
                print(f"{index}. {fm.get('title')}")
        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
