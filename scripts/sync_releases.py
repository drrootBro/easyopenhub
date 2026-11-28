#!/usr/bin/env python3
"""Fetch the latest stable GitHub release of every Mac app in data/github_apps.json and record its .dmg files.

Writes ONLY data/releases.json. Never touches data/github_apps.json or data/manual_apps.json.
Auth: env GITHUB_TOKEN (set automatically inside GitHub Actions). Works without it, but rate-limited to 60 calls/hour.

For each repo:
  - GET /repos/{owner}/{repo}/releases: newest release that is not a draft, not flagged pre-release,
    and whose tag doesn't say alpha / beta / rc / nightly / canary / preview / dev
  - keep assets ending in .dmg, label each by chip:
      universal (or one .dmg with no chip in its name) -> "Download for Mac (Universal)"
      arm64 / aarch64 / apple-silicon / m1 / apple     -> "Download for Apple Silicon (M1–M4)"
      x64 / x86_64 / intel / amd64                     -> "Download for Intel Mac"
  - no release / no .dmg -> downloads = [] (the site then shows the official page and "View on GitHub Releases")
A failed request keeps the previous entry, so one GitHub hiccup never wipes a working button.
"""
import json, os, re, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = os.path.join(ROOT, "data", "github_apps.json")
OUT = os.path.join(ROOT, "data", "releases.json")
LABEL = {"universal": "Download for Mac (Universal)",
         "apple_silicon": "Download for Apple Silicon (M1–M4)",
         "intel": "Download for Intel Mac"}
ORDER = {"universal": 0, "apple_silicon": 1, "intel": 2}
UNSTABLE = re.compile(r"(alpha|beta|\brc\.?\d*\b|nightly|canary|preview|\bdev\b)", re.I)  # authors sometimes forget the pre-release flag
SKIP_WORDS = {"debug", "symbols", "dsym", "source", "src"}


def arch_of(name):
    n = name.lower()
    toks = set(re.split(r"[^a-z0-9]+", n))
    if "universal" in toks or "univ" in toks:
        return "universal"
    if toks & {"arm64", "aarch64", "arm", "m1", "applesilicon", "apple", "silicon"} or re.search(r"apple[-_ .]?silicon", n):
        return "apple_silicon"
    if toks & {"x64", "intel", "amd64", "x86"} or re.search(r"x86[-_]?64", n):
        return "intel"
    return None


def pick_dmgs(assets):
    dmgs = [a for a in assets if a["name"].lower().endswith(".dmg")
            and not (set(re.split(r"[^a-z0-9]+", a["name"].lower())) & SKIP_WORDS)]
    out, unlabeled = {}, []
    for a in dmgs:
        k = arch_of(a["name"])
        if k is None:
            unlabeled.append(a)
        elif k not in out:  # first match per chip wins
            out[k] = a
    if unlabeled and "universal" not in out:
        # a .dmg that names no chip: universal if it is the only kind there is, otherwise the biggest one
        out["universal"] = max(unlabeled, key=lambda a: a.get("size") or 0)
    return [{"arch": k, "label": LABEL[k], "url": a["browser_download_url"], "file": a["name"],
             "size_mb": round((a.get("size") or 0) / 1048576, 1)}
            for k, a in sorted(out.items(), key=lambda kv: ORDER[kv[0]])]


def get(url, token):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "easyopenhub-sync",
                                               "X-GitHub-Api-Version": "2022-11-28",
                                               **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    apps = json.load(open(APPS))
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    new, changed, failed = {}, 0, []
    for a in apps:
        repo = a.get("repo")
        if not repo or a.get("status") == "retired" or "macOS" not in (a.get("platforms") or []):
            continue
        try:
            rels = get(f"https://api.github.com/repos/{repo}/releases?per_page=20", token)
            rel = next((r for r in rels if not r.get("draft") and not r.get("prerelease") and not UNSTABLE.search(r.get("tag_name") or "")), None)
            if rel is None:
                raise urllib.error.HTTPError(repo, 404, "no stable release", None, None)
            entry = {"version": rel.get("tag_name") or rel.get("name"),
                     "updated_at": (rel.get("published_at") or "")[:10],
                     "release_url": rel.get("html_url"),
                     "downloads": pick_dmgs(rel.get("assets") or [])}
        except urllib.error.HTTPError as e:
            if e.code == 404:  # repo has no releases at all
                entry = {"version": None, "updated_at": None, "release_url": None, "downloads": []}
            else:
                failed.append(f"{repo}: HTTP {e.code}")
                if repo in old: new[repo] = old[repo]
                continue
        except Exception as e:  # network trouble: keep what we had
            failed.append(f"{repo}: {e}")
            if repo in old: new[repo] = old[repo]
            continue
        new[repo] = entry
        if old.get(repo) != entry:
            changed += 1
            print(f"updated {repo}: {entry['version']} {[d['arch'] for d in entry['downloads']]}")
        time.sleep(0.2)
    with open(OUT, "w") as f:
        json.dump(dict(sorted(new.items())), f, ensure_ascii=False, indent=1)
        f.write("\n")
    with_dmg = sum(1 for e in new.values() if e["downloads"])
    print(f"{len(new)} Mac repos checked, {with_dmg} with .dmg, {changed} changed, {len(failed)} failed")
    for x in failed: print("  failed:", x)
    if failed and len(failed) > len(new) / 2:
        sys.exit("too many failures, check GITHUB_TOKEN / rate limit")


if __name__ == "__main__":
    main()
