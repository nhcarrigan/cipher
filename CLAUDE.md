# Cipher - Refresh Instructions

## Overview

Cipher is a backup archive of public Bluesky collections (starter packs, blocklists, and curated lists). It's designed to be periodically refreshed from the source account's live data.

**Source Account:**
- Handle: `gothicwtf.eurosky.social`
- PDS: `eurosky.social`
- DID: `did:plc:mxeixrodtfcdwakctgrgc7tk`

## How to Refresh the Data

### 1. Run the Collection Scripts

From the **scripts directory**, run all four collection scripts:

```bash
cd scripts/

# Fetch starter packs
python3 fetch_starter_packs.py

# Fetch blocklists
python3 fetch_blocklists.py

# Fetch curated lists
python3 fetch_curated_lists.py

# Fetch custom feeds (optional - not shown on public site)
python3 fetch_custom_feeds.py
```

This will generate/update files in `markdown/`:
- `markdown/starter_packs_export.md`
- `markdown/blocklists.md`
- `markdown/curated_lists.md`
- `markdown/custom_feeds.md` (not used on site)

### 2. Regenerate site files

Run the site generator script from the **scripts directory**:

```bash
python3 generate_site.py
```

This will:
- Parse all the markdown files from `markdown/`
- Generate `data.json` in the root with all collection data
- Generate `site.html` in the root (which loads data.json on the client side)
- Automatically set the "Last Updated" date to today

### 3. Verify the Output

Open `site.html` in a browser to verify:
- **Terms of Use modal** appears on first visit (stored in localStorage)
- Statistics show expected numbers
- All three collection types are present
- Search functionality works
- Expand/collapse works
- Dark mode works (use the theme toggle in the footer)
- Links to bsky.app profiles work correctly

**Note:** To test the Terms of Use modal again after accepting, clear your browser's localStorage for the site or open in an incognito window.

### 4. Deploy

Upload both files to the hosting location:
- `site.html` - The main page
- `data.json` - The collection data (loaded by site.html)

**Important:** Both files must be in the same directory for the site to work!

## Automation Notes

The scripts are designed to be idempotent - running them multiple times will simply overwrite the markdown files with fresh data. They don't modify anything except the output `.md` files.

**Rate limiting:** The scripts include 0.1s delays between paginated requests to be polite to the PDS. For Brooke's account with ~7,792 list items, expect the full refresh to take 1-2 minutes total.

## Troubleshooting

### Script fails with 401/403 error
The PDS might be temporarily unavailable or have changed auth requirements. Check if `https://eurosky.social` is accessible in a browser.

### No lists found
Verify the source account is still active and lists are still public. Check the profile at `https://bsky.app/profile/gothicwtf.eurosky.social`.

### Site.html not updating
Make sure you're editing the correct `site.html` file and re-uploading it to the hosting location. The "Last Updated" date should be the only manual change needed - the markdown content is embedded at build time, not loaded dynamically.

## Project Structure

```
cipher/
├── .gitea/                         # Gitea CI/CD configuration
│   ├── issue_template/
│   ├── pull_request_template.yml
│   └── workflows/
├── markdown/                       # Generated markdown data (gitignored)
│   ├── .gitkeep
│   ├── starter_packs_export.md     # Starter packs data
│   ├── blocklists.md               # Blocklists data
│   ├── curated_lists.md            # Curated lists data
│   └── custom_feeds.md             # Custom feeds (not used on site)
├── scripts/                        # All Python scripts
│   ├── fetch_starter_packs.py      # Fetch starter packs from PDS
│   ├── fetch_blocklists.py         # Fetch blocklists from PDS
│   ├── fetch_curated_lists.py      # Fetch curated lists from PDS
│   ├── fetch_custom_feeds.py       # Fetch custom feeds from PDS
│   ├── generate_site.py            # Build site.html + data.json
│   └── gothicwtf_fetch.py          # Original combined fetch script
├── data.json                       # Generated JSON (gitignored, loaded by site)
├── site.html                       # Generated website (gitignored)
├── .gitignore                      # Excludes generated files
├── CLAUDE.md                       # Instructions for Hikari (this file)
├── CODE_OF_CONDUCT.md             # Community guidelines
├── CONTRIBUTING.md                # How to contribute
├── LICENSE.md                     # Project license
├── PRIVACY.md                     # Privacy policy
├── README.md                      # Project overview
├── SECURITY.md                    # Security policy
└── TERMS.md                       # Terms of service
```

**Note:** All scripts should be run from the `scripts/` directory!

## Legal Note

This is a transformative work falling under NHCarrigan's intellectual property. We make no claims about the accounts included in these lists - they're simply archived as-is from the source account's public data. Removal requests should be directed to the source account on Bluesky; we refresh from source periodically and cannot honor individual removal requests at this level.
