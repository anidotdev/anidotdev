"""Update the GitHub profile SVG statistics from the GitHub GraphQL API."""

import argparse
import datetime as dt
import os
import time
from pathlib import Path

import requests
from lxml import etree

API_URL = "https://api.github.com/graphql"
USER_NAME = os.getenv("USER_NAME", "animeshhq")
TOKEN = os.getenv("ACCESS_TOKEN")
ROOT_DIR = Path(__file__).resolve().parent

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

# IDs in the new isometric SVGs. Keep these in sync with both SVG files.
STAT_ELEMENT_IDS = {
    "repos": "stat-repositories",
    "stars": "stat-stars",
    "commits": "stat-commits",
    "contributions": "stat-contributions",
    "followers": "stat-followers",
}


def year_to_date_window():
    """Return UTC timestamps spanning January 1 of this year through now."""
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    start = now.replace(month=1, day=1, hour=0, minute=0, second=0)
    return start.isoformat().replace("+00:00", "Z"), now.isoformat().replace("+00:00", "Z")


def graphql(query, variables=None):
    if not TOKEN:
        raise RuntimeError("ACCESS_TOKEN is not set. Configure it as an environment variable or GitHub Actions secret.")

    for attempt in range(3):
        try:
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json={"query": query, "variables": variables or {}},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("errors"):
                raise RuntimeError(payload["errors"])
            if "data" not in payload or payload["data"] is None:
                raise RuntimeError("GitHub GraphQL returned no data.")
            return payload["data"]
        except (requests.RequestException, RuntimeError):
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))


def get_stats():
    from_time, to_time = year_to_date_window()
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        followers { totalCount }
        repositories(first: 100, ownerAffiliations: OWNER) {
          totalCount
          nodes { stargazerCount }
          pageInfo { hasNextPage endCursor }
        }
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          contributionCalendar { totalContributions }
        }
      }
    }
    """

    user = graphql(query, {"login": USER_NAME, "from": from_time, "to": to_time})["user"]
    repos_connection = user["repositories"]
    total_stars = sum(repo["stargazerCount"] for repo in repos_connection["nodes"])
    page = repos_connection["pageInfo"]
    cursor = page["endCursor"]

    # Sum stars from all owned repositories, including accounts with over 100 repos.
    while page["hasNextPage"]:
        query_next = """
        query($login: String!, $cursor: String!) {
          user(login: $login) {
            repositories(first: 100, after: $cursor, ownerAffiliations: OWNER) {
              nodes { stargazerCount }
              pageInfo { hasNextPage endCursor }
            }
          }
        }
        """
        connection = graphql(
            query_next, {"login": USER_NAME, "cursor": cursor}
        )["user"]["repositories"]
        total_stars += sum(repo["stargazerCount"] for repo in connection["nodes"])
        page = connection["pageInfo"]
        cursor = page["endCursor"]

    contributions = user["contributionsCollection"]
    return {
        "repos": repos_connection["totalCount"],
        "stars": total_stars,
        "commits": contributions["totalCommitContributions"],
        "contributions": contributions["contributionCalendar"]["totalContributions"],
        "followers": user["followers"]["totalCount"],
    }


def replace_svg_text(root, element_id, value):
    """Replace exactly one identified SVG text element or fail loudly."""
    matches = root.xpath(".//*[@id=$element_id]", element_id=element_id)
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one SVG element with id={element_id!r}; found {len(matches)}."
        )

    node = matches[0]
    if etree.QName(node).localname != "text":
        raise ValueError(f"SVG element {element_id!r} must be a <text> element.")
    if isinstance(value, int):
        node.text = f"{value:,}"
    else:
        node.text = str(value)


def rewrite_svg(filename, stats):
    """Update only stat text nodes, leaving illustration and animation untouched."""
    filename = Path(filename)
    parser = etree.XMLParser(
        remove_blank_text=False,
        resolve_entities=False,
        no_network=True,
        recover=False,
    )
    tree = etree.parse(str(filename), parser)
    root = tree.getroot()

    for stat_name, element_id in STAT_ELEMENT_IDS.items():
        if stat_name not in stats:
            raise KeyError(f"Missing statistic {stat_name!r} for {filename.name}.")
        replace_svg_text(root, element_id, stats[stat_name])

    # Serialize to a temporary file first so a failed write cannot truncate the SVG.
    temporary = filename.with_suffix(filename.suffix + ".tmp")
    tree.write(
        str(temporary),
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=False,
    )
    temporary.replace(filename)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Write sample values to the SVGs without calling GitHub (local visual test only).",
    )
    args = parser.parse_args()

    if args.sample:
        stats = {"repos": 42, "stars": 137, "commits": 86, "contributions": 624, "followers": 19}
        print("Using sample values; these are not live GitHub statistics.")
    else:
        stats = get_stats()

    print(f"Updating profile SVG statistics for {USER_NAME}: {stats}")
    for filename in ("dark_mode.svg", "light_mode.svg"):
        rewrite_svg(ROOT_DIR / filename, stats)
    print("Profile SVGs updated.")


if __name__ == "__main__":
    main()
