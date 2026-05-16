#!/usr/bin/env python3
"""
Fetch all custom feeds from a Bluesky user's PDS,
then compile into a single markdown file.
"""

import requests
import time
from typing import Dict, List


def resolve_handle(handle: str, pds_host: str) -> str:
    """Resolve a handle to a DID."""
    url = f"https://{pds_host}/xrpc/com.atproto.identity.resolveHandle"
    response = requests.get(url, params={"handle": handle})
    response.raise_for_status()
    return response.json()["did"]


def get_repo_records(did: str, collection: str, pds_host: str) -> List[Dict]:
    """Fetch all records of a given collection from a repo."""
    url = f"https://{pds_host}/xrpc/com.atproto.repo.listRecords"
    params = {
        "repo": did,
        "collection": collection,
        "limit": 100
    }

    all_records = []
    cursor = None

    while True:
        if cursor:
            params["cursor"] = cursor

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        all_records.extend(data.get("records", []))

        cursor = data.get("cursor")
        if not cursor:
            break

        time.sleep(0.1)

    return all_records


def main():
    target_handle = "gothicwtf.eurosky.social"
    pds_host = "eurosky.social"

    print(f"Resolving {target_handle}...")
    did = resolve_handle(target_handle, pds_host)
    print(f"DID: {did}")

    # Fetch all custom feed records
    print("\nFetching custom feed records...")
    custom_feeds = get_repo_records(did, "app.bsky.feed.generator", pds_host)
    print(f"Found {len(custom_feeds)} custom feeds")

    # Build markdown
    markdown_lines = [
        f"# Custom Feeds for @{target_handle}",
        "",
        f"Retrieved {len(custom_feeds)} custom feeds.",
        "",
    ]

    for feed in custom_feeds:
        name = feed.get("value", {}).get("displayName", "Untitled")
        description = feed.get("value", {}).get("description", "")
        feed_uri = feed.get("uri")

        if not feed_uri:
            continue

        print(f"\nProcessing: {name}")
        markdown_lines.append(f"## {name}")
        markdown_lines.append("")

        if description:
            markdown_lines.append(description)
            markdown_lines.append("")

        # Parse feed URI to get the rkey for the feed URL
        # Format: at://did:plc:xxx/app.bsky.feed.generator/rkey
        parts = feed_uri.replace("at://", "").split("/")
        feed_did = parts[0]
        rkey = parts[2]

        feed_url = f"https://bsky.app/profile/{feed_did}/feed/{rkey}"
        markdown_lines.append(f"**Feed URL:** {feed_url}")
        markdown_lines.append("")

    # Write output
    output_path = "../markdown/custom_feeds.md"
    with open(output_path, "w") as f:
        f.write("\n".join(markdown_lines))

    print(f"\n✅ Written to {output_path}")


if __name__ == "__main__":
    main()
