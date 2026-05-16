#!/usr/bin/env python3
"""
Fetch all curated lists from a Bluesky user's PDS,
then compile into a single markdown file with DIDs as clickable URLs.
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


def get_list_members(list_uri: str, did: str, pds_host: str) -> List[str]:
    """Fetch all members from a list."""
    # Get all listitem records
    listitems = get_repo_records(did, "app.bsky.graph.listitem", pds_host)

    members = []
    for item in listitems:
        if item.get("value", {}).get("list") == list_uri:
            subject_did = item["value"]["subject"]
            members.append(subject_did)

    return sorted(members)


def main():
    target_handle = "gothicwtf.eurosky.social"
    pds_host = "eurosky.social"

    print(f"Resolving {target_handle}...")
    did = resolve_handle(target_handle, pds_host)
    print(f"DID: {did}")

    # Fetch all list records
    print("\nFetching list records...")
    all_lists = get_repo_records(did, "app.bsky.graph.list", pds_host)

    # Filter to only curated lists (purpose: curate)
    curated_lists = [
        lst for lst in all_lists
        if lst.get("value", {}).get("purpose") == "app.bsky.graph.defs#curatelist"
    ]
    print(f"Found {len(curated_lists)} curated lists")

    # Fetch ALL listitems ONCE
    print("\nFetching all list items...")
    all_listitems = get_repo_records(did, "app.bsky.graph.listitem", pds_host)
    print(f"Found {len(all_listitems)} total list items")

    # Build markdown
    markdown_lines = [
        f"# Curated Lists for @{target_handle}",
        "",
        f"Retrieved {len(curated_lists)} curated lists.",
        "",
    ]

    for curated_list in curated_lists:
        name = curated_list.get("value", {}).get("name", "Untitled")
        description = curated_list.get("value", {}).get("description", "")
        list_uri = curated_list.get("uri")

        if not list_uri:
            continue

        print(f"\nProcessing: {name}")
        markdown_lines.append(f"## {name}")
        markdown_lines.append("")

        if description:
            markdown_lines.append(description)
            markdown_lines.append("")

        # Filter listitems for this specific list
        members = sorted([
            item["value"]["subject"]
            for item in all_listitems
            if item.get("value", {}).get("list") == list_uri
        ])
        print(f"  → {len(members)} members")

        for member in members:
            markdown_lines.append(f"- https://bsky.app/profile/{member}")

        markdown_lines.append("")

    # Write output
    output_path = "../markdown/curated_lists.md"
    with open(output_path, "w") as f:
        f.write("\n".join(markdown_lines))

    print(f"\n✅ Written to {output_path}")


if __name__ == "__main__":
    main()
