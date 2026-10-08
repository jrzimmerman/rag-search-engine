import argparse
import json
import os
import pickle
import string
import sys

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

    def load(self) -> None:
        for path in (INDEX_PATH, DOCMAP_PATH):
            if not os.path.exists(path):
                raise FileNotFoundError(f"{path} not found, run the build command first")
        with open(INDEX_PATH, "rb") as f:
            self.index = pickle.load(f)
        with open(DOCMAP_PATH, "rb") as f:
            self.docmap = pickle.load(f)


def build_command() -> None:
    index = InvertedIndex()
    index.build()
    index.save()


def search_command(query: str) -> None:
    index = InvertedIndex()
    try:
        index.load()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    results = []
    for token in tokenize(query, index.stop_words):
        for doc_id in index.get_documents(token):
            if doc_id not in results:
                results.append(doc_id)
            if len(results) == MAX_RESULTS:
                break
        if len(results) == MAX_RESULTS:
            break

    print(f"Searching for: {query}")
    for position, doc_id in enumerate(results, start=1):
        print(f"{position}. {index.docmap[doc_id]['title']} (ID: {doc_id})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Keyword Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    search_parser = subparsers.add_parser("search", help="Search movies using keywords")
    search_parser.add_argument("query", type=str, help="Search query")

    subparsers.add_parser("build", help="Build the inverted index and save it to disk")

    args = parser.parse_args()

    match args.command:
        case "search":
            search_command(args.query)
        case "build":
            build_command()
        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
