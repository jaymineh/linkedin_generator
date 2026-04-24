from __future__ import annotations

import argparse

from common import echo, fail


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local deploys are disabled for this repo.")
    parser.add_argument("--dispatch", action="store_true", help="Reserved for future manual workflow dispatch support.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.dispatch:
        fail(
            "Manual dispatch via this script is not enabled.\n"
            "Use GitHub Actions instead: push to `main`, or trigger the workflow from GitHub."
        )

    echo("Local deploys are disabled.")
    echo("Push your committed code to `main` and GitHub Actions will build and deploy from the repo.")


if __name__ == "__main__":
    main()
