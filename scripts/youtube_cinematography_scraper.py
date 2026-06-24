"""YouTube cinematography data scraper — gathers video metadata about camera techniques.

Uses YouTube Data API v3 (official, ToS-compliant) to search for videos
about camera angles, lighting techniques, genre filmmaking, etc.

Requires: pip install google-api-python-client
Set YOUTUBE_API_KEY env var or pass --api-key
"""

import json
import os
import sys
import time
from typing import List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "nicto_neural", "data")
os.makedirs(DATA_DIR, exist_ok=True)

SEARCH_QUERIES = [
    "cinematography camera angles tutorial",
    "film lighting techniques guide",
    "cinematography composition rules",
    "horror film cinematography techniques",
    "action movie camera work",
    "cinematic lighting setup tutorial",
    "film color grading tutorial",
    "documentary cinematography tips",
    "music video cinematography techniques",
    "cinematography lens choices guide",
    "film movement types dolly crane steadicam",
    "cinematography for beginners full guide",
    "professional lighting setup for video",
    "cinematography genre conventions",
    "visual storytelling camera techniques",
    "cinematography masterclass",
    "camera angles explained with examples",
    "film noir lighting tutorial",
    "cinematography framing composition guide",
    "professional video production techniques",
]


def search_youtube(query: str, api_key: str, max_results: int = 50) -> List[dict]:
    """Search YouTube for videos matching query. Uses official Data API v3."""
    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("  google-api-python-client not installed. Run: pip install google-api-python-client")
        return []

    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        request = youtube.search().list(
            q=query,
            part="snippet",
            maxResults=min(max_results, 50),
            type="video",
            videoDuration="medium",
            relevanceLanguage="en",
        )
        response = request.execute()

        videos = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            videos.append({
                "video_id": item["id"]["videoId"],
                "title": snippet.get("title", ""),
                "description": snippet.get("description", "")[:500],
                "channel": snippet.get("channelTitle", ""),
                "published": snippet.get("publishedAt", ""),
                "tags": snippet.get("tags", []),
                "category": "cinematography",
                "search_query": query,
                "source": "youtube_api",
            })
        return videos

    except Exception as e:
        print(f"  YouTube API error: {e}")
        return []


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape YouTube for cinematography data")
    parser.add_argument("--api-key", help="YouTube Data API key (or set YOUTUBE_API_KEY env var)")
    parser.add_argument("--max-per-query", type=int, default=50, help="Max results per query")
    parser.add_argument("--limit-queries", type=int, default=5, help="Limit number of queries to run")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("YouTube API key required. Set YOUTUBE_API_KEY env var or pass --api-key")
        print("Get a key at: https://console.cloud.google.com/apis/credentials")
        sys.exit(1)

    queries = SEARCH_QUERIES[:args.limit_queries]
    all_videos = []
    existing_ids = set()

    out_path = os.path.join(DATA_DIR, "youtube_cinematography.jsonl")
    if os.path.exists(out_path):
        with open(out_path) as f:
            for line in f:
                if line.strip():
                    v = json.loads(line)
                    existing_ids.add(v.get("video_id", ""))
                    all_videos.append(v)
        print(f"Loaded {len(all_videos)} existing videos from {out_path}")

    for i, query in enumerate(queries):
        print(f"[{i+1}/{len(queries)}] Searching: '{query}'...")
        videos = search_youtube(query, api_key, args.max_per_query)
        new_count = 0
        for v in videos:
            if v["video_id"] not in existing_ids:
                existing_ids.add(v["video_id"])
                all_videos.append(v)
                new_count += 1
        print(f"  Found {len(videos)}, {new_count} new")
        time.sleep(0.5)

    with open(out_path, "w") as f:
        for v in all_videos:
            f.write(json.dumps(v) + "\n")
    print(f"\nSaved {len(all_videos)} videos to {out_path}")


if __name__ == "__main__":
    main()
