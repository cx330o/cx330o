#!/usr/bin/env python3
"""
Fully auto-update README.md — zero manual maintenance.

Auto-generated sections:
  1. Typing SVG headline   (from repo topics)
  2. Keywords badge line    (from repo topics)
  3. Tech Stack icons       (from repo languages)
  4. Active Projects table  (from recently-pushed repos)
  5. Recent Activity list   (from public events)
  6. Random quote           (from built-in quote pool)
"""

import os
import re
import json
import random
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── Config ──────────────────────────────────────────────────────────
USERNAME = os.getenv("GITHUB_USERNAME", "cx330o")
TOKEN = os.getenv("GITHUB_TOKEN", "")
README_PATH = os.getenv("README_PATH", "README.md")
MAX_ACTIVITY = 8
MAX_REPOS = 6
MAX_TOPICS = 15
EXCLUDE_REPOS: set[str] = set()   # e.g. {"cx330o"}

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "readme-updater",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


# ── GitHub API helper ───────────────────────────────────────────────

def api_get(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"⚠️  API error {e.code} for {url}")
        return None


def fetch_all_repos() -> list[dict]:
    """Fetch all owner repos (non-fork), paginated."""
    repos: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?type=owner&sort=pushed&direction=desc&per_page=100&page={page}"
        )
        batch = api_get(url)
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return [r for r in repos if not r.get("fork")]


# ── 1. Typing SVG ──────────────────────────────────────────────────

def build_typing_svg(topics: list[str]) -> str:
    """Generate a Typing SVG markdown image from topic keywords."""
    if not topics:
        return "![Typing SVG](https://readme-typing-svg.demolab.com/?lines=Hello+World!&center=true&width=920)\n"

    # Group topics into 2-3 lines for the animation
    chunk_size = max(1, len(topics) // 3) or 1
    lines_raw: list[str] = []
    for i in range(0, len(topics), chunk_size):
        chunk = topics[i : i + chunk_size]
        lines_raw.append(" | ".join(t.replace("-", " ").title() for t in chunk))
    # Keep max 4 lines
    lines_raw = lines_raw[:4]

    lines_encoded = [ln.replace(" ", "+").replace("|", "%7C") for ln in lines_raw]
    lines_param = ";".join(lines_encoded)
    return (
        f"![Typing SVG](https://readme-typing-svg.demolab.com/"
        f"?lines={lines_param}&center=true&width=920)\n"
    )


# ── 2. Keywords badges ─────────────────────────────────────────────

def build_keywords(topics: list[str]) -> str:
    """Generate shields.io badges for each topic."""
    if not topics:
        return "_No topics found across repositories._\n"
    badges: list[str] = []
    colors = [
        "blue", "green", "orange", "red", "purple",
        "brightgreen", "yellow", "blueviolet", "ff69b4", "00CED1",
    ]
    for i, t in enumerate(topics):
        label = t.replace("-", " ")
        color = colors[i % len(colors)]
        safe = t.replace("-", "--")
        badges.append(
            f"![{label}](https://img.shields.io/badge/{safe}-{color}?style=flat-square)"
        )
    return " ".join(badges) + "\n"


# ── 3. Tech Stack icons ────────────────────────────────────────────

# Map GitHub language names -> skillicons.dev icon ids
LANG_TO_ICON: dict[str, str] = {
    "Python": "py",
    "C++": "cpp",
    "C": "c",
    "C#": "cs",
    "Java": "java",
    "JavaScript": "js",
    "TypeScript": "ts",
    "Go": "go",
    "Rust": "rust",
    "Shell": "bash",
    "MATLAB": "matlab",
    "HTML": "html",
    "CSS": "css",
    "Dockerfile": "docker",
    "Jupyter Notebook": "py",
    "Makefile": "linux",
    "CMake": "cmake",
    "Lua": "lua",
    "Ruby": "ruby",
    "PHP": "php",
    "Kotlin": "kotlin",
    "Swift": "swift",
    "Dart": "dart",
    "R": "r",
    "Scala": "scala",
    "Perl": "perl",
    "Vue": "vue",
    "Svelte": "svelte",
}

# Always include these tool icons regardless of language detection
ALWAYS_INCLUDE = ["git", "github", "vscode", "linux"]


def build_tech_stack(repos: list[dict]) -> str:
    """Generate skillicons.dev badge from actual repo languages."""
    lang_bytes: dict[str, int] = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            lang_bytes[lang] = lang_bytes.get(lang, 0) + r.get("size", 0)

    # Sort by usage, map to icon ids, deduplicate
    sorted_langs = sorted(lang_bytes, key=lambda k: lang_bytes[k], reverse=True)
    icons: list[str] = []
    seen: set[str] = set()
    for lang in sorted_langs:
        icon = LANG_TO_ICON.get(lang)
        if icon and icon not in seen:
            icons.append(icon)
            seen.add(icon)

    for tool in ALWAYS_INCLUDE:
        if tool not in seen:
            icons.append(tool)
            seen.add(tool)

    if not icons:
        return "_No languages detected._\n"

    icon_str = ",".join(icons)
    per_line = min(len(icons), 10)
    return (
        f"[![Tech Stack](https://skillicons.dev/icons?i={icon_str}"
        f"&theme=dark&perline={per_line})](https://skillicons.dev)\n"
    )


# ── 4. Active Projects table ───────────────────────────────────────

LANG_EMOJI: dict[str, str] = {
    "Python": "🐍", "C++": "⚙️", "C": "⚙️", "MATLAB": "📐",
    "JavaScript": "🟨", "TypeScript": "🔷", "Shell": "🐚",
    "Jupyter Notebook": "📓", "HTML": "🌐", "CSS": "🎨",
    "Rust": "🦀", "Go": "🐹", "Java": "☕", "Dockerfile": "🐳",
}


def relative_time(iso_str: str) -> str:
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - dt
    days = delta.days
    if days == 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 30:
        return f"{days} days ago"
    months = days // 30
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''} ago"
    return f"{days // 365} year{'s' if days // 365 != 1 else ''} ago"


def build_projects(repos: list[dict]) -> str:
    header = (
        "| Project | Description | Language | Stars | Updated |\n"
        "|---------|-------------|----------|-------|---------|\n"
    )
    rows: list[str] = []
    for r in repos:
        if r["name"] in EXCLUDE_REPOS:
            continue
        if len(rows) >= MAX_REPOS:
            break
        name = r["name"]
        full = r["full_name"]
        desc = (r.get("description") or "—")[:80]
        if len(r.get("description") or "") > 80:
            desc = desc[:77] + "..."
        lang = r.get("language") or "—"
        emoji = LANG_EMOJI.get(lang, "📦")
        stars = r.get("stargazers_count", 0)
        updated = relative_time(r.get("pushed_at") or r.get("updated_at", ""))
        star_str = f"⭐ {stars}" if stars > 0 else ""
        rows.append(
            f"| {emoji} [{name}](https://github.com/{full}) "
            f"| {desc} | {lang} | {star_str} | {updated} |"
        )
    if not rows:
        return "_No repositories found._\n"
    return header + "\n".join(rows) + "\n"


# ── 5. Recent Activity ─────────────────────────────────────────────

EMOJI_MAP: dict[str, str] = {
    "PushEvent":                "📌",
    "CreateEvent":              "🆕",
    "DeleteEvent":              "🗑️",
    "WatchEvent":               "⭐",
    "ForkEvent":                "🍴",
    "IssuesEvent":              "❗",
    "IssueCommentEvent":        "💬",
    "PullRequestEvent":         "🔀",
    "PullRequestReviewEvent":   "👀",
    "ReleaseEvent":             "🎉",
    "PublicEvent":              "🌍",
    "MemberEvent":              "👥",
}


def format_event(ev: dict) -> str | None:
    etype = ev.get("type", "")
    repo = ev.get("repo", {}).get("name", "")
    payload = ev.get("payload", {})
    emoji = EMOJI_MAP.get(etype, "🔸")
    repo_link = f"[{repo}](https://github.com/{repo})"

    if etype == "PushEvent":
        n = payload.get("size", 0)
        branch = (payload.get("ref") or "").replace("refs/heads/", "")
        return f"{emoji} Pushed **{n}** commit{'s' if n != 1 else ''} to `{branch}` in {repo_link}"
    if etype == "CreateEvent":
        ref_type = payload.get("ref_type", "repository")
        ref = payload.get("ref", "")
        if ref_type == "repository":
            return f"{emoji} Created new repository {repo_link}"
        return f"{emoji} Created {ref_type} `{ref}` in {repo_link}"
    if etype == "WatchEvent":
        return f"{emoji} Starred {repo_link}"
    if etype == "ForkEvent":
        forkee = payload.get("forkee", {}).get("full_name", "")
        return f"{emoji} Forked {repo_link} → [{forkee}](https://github.com/{forkee})"
    if etype == "IssuesEvent":
        action = payload.get("action", "")
        num = payload.get("issue", {}).get("number", "")
        title = payload.get("issue", {}).get("title", "")
        return f"{emoji} {action.capitalize()} issue [#{num}](https://github.com/{repo}/issues/{num}) in {repo_link}: *{title}*"
    if etype == "IssueCommentEvent":
        num = payload.get("issue", {}).get("number", "")
        return f"{emoji} Commented on [#{num}](https://github.com/{repo}/issues/{num}) in {repo_link}"
    if etype == "PullRequestEvent":
        action = payload.get("action", "")
        num = payload.get("pull_request", {}).get("number", "")
        title = payload.get("pull_request", {}).get("title", "")
        return f"{emoji} {action.capitalize()} PR [#{num}](https://github.com/{repo}/pull/{num}) in {repo_link}: *{title}*"
    if etype == "ReleaseEvent":
        tag = payload.get("release", {}).get("tag_name", "")
        return f"{emoji} Released [{tag}](https://github.com/{repo}/releases/tag/{tag}) in {repo_link}"
    return None


def build_activity() -> str:
    url = f"https://api.github.com/users/{USERNAME}/events/public?per_page=100"
    events = api_get(url)
    if not events:
        return "_Could not fetch activity._\n"
    lines: list[str] = []
    for ev in events:
        if len(lines) >= MAX_ACTIVITY:
            break
        line = format_event(ev)
        if line:
            lines.append(f"- {line}")
    if not lines:
        return "_No recent public activity._\n"
    return "\n".join(lines) + "\n"


# ── 6. Random quote ─────────────────────────────────────────────────

QUOTES: list[tuple[str, str]] = [
    ("Measure carefully, build quickly, iterate relentlessly.", "cx330o"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
    ("Simplicity is the soul of efficiency.", "Austin Freeman"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
    ("The best error message is the one that never shows up.", "Thomas Fuchs"),
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("Any fool can write code that a computer can understand. Good programmers write code that humans can understand.", "Martin Fowler"),
    ("Programming is the art of telling another human what one wants the computer to do.", "Donald Knuth"),
    ("Debugging is twice as hard as writing the code in the first place.", "Brian Kernighan"),
    ("The only way to go fast is to go well.", "Robert C. Martin"),
    ("Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away.", "Antoine de Saint-Exupéry"),
    ("In theory, there is no difference between theory and practice. In practice, there is.", "Yogi Berra"),
    ("Science is what we understand well enough to explain to a computer. Art is everything else we do.", "Donald Knuth"),
    ("The function of good software is to make the complex appear to be simple.", "Grady Booch"),
]


def build_quote() -> str:
    quote, author = random.choice(QUOTES)
    q_encoded = quote.replace(" ", "+")
    a_encoded = author.replace(" ", "+")
    return (
        f'<img src="https://quotes-github-readme.vercel.app/api'
        f"?type=horizontal&theme=dark&quote={q_encoded}&author={a_encoded}\" />\n"
    )


# ── Topic extraction ────────────────────────────────────────────────

def extract_topics(repos: list[dict]) -> list[str]:
    """Aggregate topics from all repos, sorted by frequency."""
    counts: dict[str, int] = {}
    for r in repos:
        for t in r.get("topics", []):
            counts[t] = counts.get(t, 0) + 1
    sorted_topics = sorted(counts, key=lambda k: counts[k], reverse=True)
    return sorted_topics[:MAX_TOPICS]


# ── README injection ────────────────────────────────────────────────

def inject(content: str, start_tag: str, end_tag: str, payload: str) -> str:
    pattern = re.compile(
        rf"({re.escape(start_tag)}\n)(.*?)(\n{re.escape(end_tag)})",
        re.DOTALL,
    )
    new_content, n = pattern.subn(rf"\g<1>{payload}\g<3>", content)
    if n == 0:
        print(f"⚠️  Tag pair not found: {start_tag} ... {end_tag}")
    return new_content


# ── Main ────────────────────────────────────────────────────────────

def main():
    print(f"📡 Fetching data for @{USERNAME} ...")

    repos = fetch_all_repos()
    topics = extract_topics(repos)
    print(f"   Found {len(repos)} repos, {len(topics)} unique topics")

    typing_md = build_typing_svg(topics)
    keywords_md = build_keywords(topics)
    tech_md = build_tech_stack(repos)
    projects_md = build_projects(repos)
    activity_md = build_activity()
    quote_md = build_quote()

    print("📝 Updating README ...")
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = inject(content, "<!-- TYPING:START -->",    "<!-- TYPING:END -->",    typing_md)
    content = inject(content, "<!-- KEYWORDS:START -->",  "<!-- KEYWORDS:END -->",  keywords_md)
    content = inject(content, "<!-- TECHSTACK:START -->", "<!-- TECHSTACK:END -->", tech_md)
    content = inject(content, "<!-- PROJECTS:START -->",  "<!-- PROJECTS:END -->",  projects_md)
    content = inject(content, "<!-- ACTIVITY:START -->",  "<!-- ACTIVITY:END -->",  activity_md)
    content = inject(content, "<!-- QUOTE:START -->",     "<!-- QUOTE:END -->",     quote_md)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ README fully updated — 6 sections refreshed!")


if __name__ == "__main__":
    main()
