"""Small sample application used by the Jenkins CI exercise."""

import sys


def greet(name: str = "world") -> str:
    """Return a friendly greeting, using ``world`` for blank names."""
    cleaned_name = name.strip()
    return f"Hello, {cleaned_name or 'world'}!"


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "world"
    print(greet(name))


if __name__ == "__main__":
    main()
