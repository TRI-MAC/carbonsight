from re import sub


def to_snake_case(s: str) -> str:
    # Replace hyphens with spaces, then apply regular expression substitutions for title case conversion
    # and add an underscore between words, finally convert the result to lowercase
    return "_".join(
        sub(
            "([A-Z][a-z]+)", r" \1", sub("([A-Z]+)", r" \1", s.replace("-", " "))
        ).split()
    ).lower()
