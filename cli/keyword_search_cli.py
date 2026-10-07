import argparse
import json
import os
import pickle
import string

from nltk.stem import PorterStemmer

PUNCTUATION_TABLE = str.maketrans("", "", string.punctuation)
MAX_RESULTS = 5
CACHE_DIR = "cache"
INDEX_PATH = os.path.join(CACHE_DIR, "index.pkl")
DOCMAP_PATH = os.path.join(CACHE_DIR, "docmap.pkl")

stemmer = PorterStemmer()


def normalize(text: str) -> str:
    return text.lower().translate(PUNCTUATION_TABLE)


def tokenize(text: str, stop_words: list[str]) -> list[str]:
    tokens = []
    for token in normalize(text).split():
        if token not in stop_words:
            tokens.append(stemmer.stem(token))
    return tokens


def load_stop_words() -> list[str]:
    with open("data/stopwords.txt", "r") as f:
        words = f.read().splitlines()

    stop_words = []
    for word in words:
        stop_words.append(normalize(word))
    return stop_words


def load_movies() -> list[dict]:
    with open("data/movies.json", "r") as f:
        movie_data = json.load(f)
    return movie_data.get("movies", [])


class InvertedIndex:
    def __init__(self) -> None:
        self.index: dict[str, set[int]] = {}
        self.docmap: dict[int, dict] = {}
        self.stop_words = load_stop_words()

    def __add_document(self, doc_id: int, text: str) -> None:
        for token in tokenize(text, self.stop_words):
            if token not in self.index:
                self.index[token] = set()
            self.index[token].add(doc_id)

    def get_documents(self, term: str) -> list[int]:
        doc_ids = self.index.get(term, set())
        return sorted(doc_ids)

    def build(self) -> None:
        for m in load_movies():
            self.docmap[m["id"]] = m
            self.__add_document(m["id"], f"{m['title']} {m['description']}")

    def save(self) -> None:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(INDEX_PATH, "wb") as f:
            pickle.dump(self.index, f)
        with open(DOCMAP_PATH, "wb") as f:
            pickle.dump(self.docmap, f)


def has_matching_token(query_tokens: list[str], title_tokens: list[str]) -> bool:
    for query_token in query_tokens:
        for title_token in title_tokens:
            if query_token in title_token:
                return True
    return False


def build_command() -> None:
    index = InvertedIndex()
    index.build()
    index.save()

    docs = index.get_documents("merida")
    print(f"First document for token 'merida' = {docs[0]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Keyword Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    search_parser = subparsers.add_parser("search", help="Search movies using keywords")
    search_parser.add_argument("query", type=str, help="Search query")

    subparsers.add_parser("build", help="Build the inverted index and save it to disk")

    args = parser.parse_args()

    match args.command:
        case "search":
            stop_words = load_stop_words()

            query_tokens = tokenize(args.query, stop_words)
            filtered_movies = []
            for movie in load_movies():
                title_tokens = tokenize(movie.get("title", ""), stop_words)
                if has_matching_token(query_tokens, title_tokens):
                    filtered_movies.append(movie)
                    if len(filtered_movies) == MAX_RESULTS:
                        break

            print(f"Searching for: {args.query}")
            for index, fm in enumerate(filtered_movies, start=1):
                print(f"{index}. {fm.get('title')}")
        case "build":
            build_command()
        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
