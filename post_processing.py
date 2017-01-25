import aggregate_metadata as meta
import compile_corpus as corpus
import extract_links as links
import generate_lists as lists


def main():
    meta.main()
    corpus.main()
    links.main()
    #lists.main()


if __name__ == "__main__":
    main()