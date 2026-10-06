"""Fetches GitHub stats and writes them into dark_mode.svg / light_mode.svg.
Env: ACCESS_TOKEN (PAT), USER_NAME (your GitHub login)."""
import datetime, json, os, sys, time
import requests
from dateutil import relativedelta
from lxml import etree

BIRTHDAY = datetime.datetime(2006, 7, 4)
SVGS = ["dark_mode.svg", "light_mode.svg"]
CACHE = "cache/loc.json"

USER = os.environ["USER_NAME"]
S = requests.Session()
S.headers.update({"Authorization": f"Bearer {os.environ['ACCESS_TOKEN']}", "Accept": "application/vnd.github+json"})

def gql(query, **variables):
    for attempt in range(3):
        r = S.post("https://api.github.com/graphql", json={"query": query, "variables": variables}, timeout=30)
        if r.status_code == 200 and "errors" not in r.json():
            return r.json()["data"]
        time.sleep(5 * (attempt + 1))
    r.raise_for_status()
    raise RuntimeError(r.text)

def plural(n): return "" if n == 1 else "s"

def uptime():
    d = relativedelta.relativedelta(datetime.datetime.today(), BIRTHDAY)
    return f"{d.years} year{plural(d.years)}, {d.months} month{plural(d.months)}, {d.days} day{plural(d.days)}"

def user_info():
    d = gql("query($u:String!){user(login:$u){createdAt followers{totalCount}}}", u=USER)["user"]
    return d["createdAt"], d["followers"]["totalCount"]

def commits_all_time(created_at):
    """contributionsCollection is capped at 1 year per query, so walk year by year."""
    start = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    total = 0
    while start < now:
        end = min(start + datetime.timedelta(days=365), now)
        d = gql("query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){totalCommitContributions}}}",
                u=USER, f=start.isoformat(), t=end.isoformat())
        total += d["user"]["contributionsCollection"]["totalCommitContributions"]
        start = end
    return total

REPOS_Q = """query($u:String!,$aff:[RepositoryAffiliation],$c:String){user(login:$u){repositories(first:100,after:$c,ownerAffiliations:$aff){
  totalCount pageInfo{hasNextPage endCursor} nodes{nameWithOwner isFork pushedAt stargazerCount}}}}"""

def repos(affiliations):
    out, cursor = [], None
    while True:
        d = gql(REPOS_Q, u=USER, aff=affiliations, c=cursor)["user"]["repositories"]
        out += d["nodes"]
        if not d["pageInfo"]["hasNextPage"]: return out
        cursor = d["pageInfo"]["endCursor"]

def repo_loc(full_name):
    """Additions/deletions by USER on the default branch, from GitHub's stats endpoint (202 = still computing)."""
    for _ in range(6):
        r = S.get(f"https://api.github.com/repos/{full_name}/stats/contributors", timeout=30)
        if r.status_code == 202:
            time.sleep(4); continue
        if r.status_code != 200: return 0, 0
        for c in r.json() or []:
            if c["author"] and c["author"]["login"].lower() == USER.lower():
                return sum(w["a"] for w in c["weeks"]), sum(w["d"] for w in c["weeks"])
        return 0, 0
    return 0, 0

def loc_totals(owned):
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    add = dele = 0
    for r in owned:
        if r["isFork"]: continue
        hit = cache.get(r["nameWithOwner"])
        if not hit or hit["pushedAt"] != r["pushedAt"]:
            a, d = repo_loc(r["nameWithOwner"])
            hit = cache[r["nameWithOwner"]] = {"pushedAt": r["pushedAt"], "a": a, "d": d}
        add += hit["a"]; dele += hit["d"]
    json.dump(cache, open(CACHE, "w"), indent=1)
    return add, dele

def dots(budget, value_len):
    n = max(0, budget - value_len)
    return " " + "." * (n - 2) + " " if n > 2 else [" ", " ", ". "][n]

def write_svg(path, values):
    tree = etree.parse(path)
    root = tree.getroot()
    for key, text in values.items():
        el = root.find(f".//*[@id='{key}']")
        if el is None: continue
        el.text = text
        pad = root.find(f".//*[@id='{key}_dots']")
        if pad is not None and pad.get("data-pad"):
            pad.text = dots(int(pad.get("data-pad")), len(text))
    tree.write(path, encoding="utf-8", xml_declaration=True)

def main():
    created, followers = user_info()
    owned = repos(["OWNER"])
    contrib = repos(["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"])
    add, dele = loc_totals(owned)
    values = {
        "age_data": uptime(),
        "repo_data": f"{len(owned):,}",
        "contrib_data": f"{len(contrib):,}",
        "star_data": f"{sum(r['stargazerCount'] for r in owned):,}",
        "commit_data": f"{commits_all_time(created):,}",
        "follower_data": f"{followers:,}",
        "loc_data": f"{add - dele:,}",
        "loc_add": f"{add:,}",
        "loc_del": f"{dele:,}",
    }
    for svg in SVGS: write_svg(svg, values)
    print(values)

if __name__ == "__main__":
    main()
