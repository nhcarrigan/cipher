#!/usr/bin/env python3
"""
Generate site.html from the markdown collection files.
Run this after fetching updated collections to rebuild the site.
"""

import re
import json
from datetime import date
from typing import Dict, List


def parse_markdown_collections(filepath: str) -> List[Dict]:
    """Parse a markdown file into structured collection data."""
    with open(filepath, "r") as f:
        content = f.read()

    collections = []
    current_collection = None

    for line in content.split("\n"):
        line = line.strip()

        # Skip header and count lines
        if line.startswith("# ") or line.startswith("Retrieved"):
            continue

        # New collection
        if line.startswith("## "):
            if current_collection:
                collections.append(current_collection)
            current_collection = {
                "name": line[3:].strip(),
                "description": "",
                "members": []
            }
        # Description (non-link text after collection name)
        elif current_collection and line and not line.startswith("-"):
            if current_collection["description"]:
                current_collection["description"] += " " + line
            else:
                current_collection["description"] = line
        # Member link
        elif line.startswith("- https://"):
            did = line.split("/")[-1]
            current_collection["members"].append(did)

    if current_collection:
        collections.append(current_collection)

    return collections


def generate_html(starter_packs: List[Dict], blocklists: List[Dict], curated_lists: List[Dict]) -> str:
    """Generate the complete HTML document."""

    today = date.today().isoformat()

    html = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <title>Cipher</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta
      name="description"
      content="Public archive of Bluesky collections - starter packs, blocklists, and curated lists."
    />
    <script
      src="https://cdn.nhcarrigan.com/headers/index.js"
      async
      defer
    ></script>
    <style>
      /* Collection-specific styles */
      .disclaimer {{
        background: rgba(168, 87, 126, 0.15);
        border: 2px solid var(--witch-rose);
        border-radius: 15px;
        padding: 1.5em;
        margin-bottom: 2em;
      }}

      /* Terms modal - namespaced to avoid conflicts with global headers */
      .cipher-terms-modal {{
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.85);
        z-index: 10000;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(5px);
      }}

      .cipher-terms-modal.active {{
        display: flex;
      }}

      .cipher-modal-content {{
        background: var(--background, #f5f5f5);
        border: 3px solid var(--witch-rose);
        border-radius: 20px;
        padding: 2.5em;
        max-width: 650px;
        max-height: 85vh;
        overflow-y: auto;
        box-shadow: 0 10px 40px rgba(168, 87, 126, 0.4);
      }}

      .is-dark .cipher-modal-content {{
        background: var(--background, #0a0009);
      }}

      .cipher-modal-content h2 {{
        font-family: 'Griffy', cursive;
        color: var(--witch-purple);
        margin-top: 0;
        font-size: 2rem;
      }}

      .cipher-modal-content h3 {{
        color: var(--witch-rose);
        margin-top: 1.5em;
        font-size: 1.25rem;
      }}

      .cipher-modal-content p {{
        line-height: 1.6;
        margin-bottom: 1em;
      }}

      .cipher-modal-content ul {{
        margin: 0.75em 0 1.5em 1.5em;
        line-height: 1.6;
      }}

      .cipher-modal-actions {{
        text-align: center;
        margin-top: 2em;
        padding-top: 1.5em;
        border-top: 2px solid var(--witch-plum);
      }}

      .cipher-modal-actions button {{
        font-size: 1.1rem;
        padding: 0.75em 2em;
        margin: 0 0.5em;
      }}

      .cipher-decline-btn {{
        background: rgba(200, 60, 60, 0.2);
        border-color: #993333;
        color: #993333;
      }}

      .cipher-decline-btn:hover {{
        background: rgba(200, 60, 60, 0.3);
      }}

      .cipher-blocked-message {{
        display: none;
        text-align: center;
        padding: 3em 2em;
        max-width: 600px;
        margin: 5em auto;
      }}

      .cipher-blocked-message.active {{
        display: block;
      }}

      .cipher-blocked-message h2 {{
        font-family: 'Griffy', cursive;
        color: var(--witch-rose);
        font-size: 2rem;
        margin-bottom: 1em;
      }}

      .disclaimer h2 {{
        margin-top: 0;
        color: var(--witch-purple);
      }}

      .disclaimer p {{
        margin-bottom: 0.75em;
      }}

      .disclaimer p:last-child {{
        margin-bottom: 0;
      }}

      .stats-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1em;
        margin: 2em 0;
      }}

      .stat-card {{
        background: rgba(212, 165, 199, 0.1);
        border: 1px solid var(--witch-plum);
        border-radius: 12px;
        padding: 1.25em;
        text-align: center;
      }}

      .stat-number {{
        font-family: 'Griffy', cursive;
        font-size: 2.5rem;
        color: var(--witch-rose);
        display: block;
        margin-bottom: 0.25em;
      }}

      .stat-label {{
        font-size: 0.9rem;
        color: var(--witch-plum);
      }}

      .search-box {{
        width: 100%;
        max-width: 500px;
        margin: 2em auto;
        display: block;
      }}

      .page-size-control {{
        text-align: center;
        margin: 1.5em 0;
        padding: 1em;
        background: rgba(212, 165, 199, 0.1);
        border-radius: 12px;
      }}

      .page-size-control label {{
        font-weight: 700;
        color: var(--witch-purple);
        margin-right: 1em;
      }}

      .page-size-control input[type="radio"] {{
        margin: 0 0.25em 0 1em;
        cursor: pointer;
      }}

      .page-size-control input[type="radio"]:first-of-type {{
        margin-left: 0;
      }}

      .pagination-controls {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 1.5em;
        padding-top: 1.5em;
        border-top: 1px solid rgba(68, 39, 90, 0.2);
      }}

      .pagination-info {{
        font-size: 0.85rem;
        color: var(--witch-plum);
      }}

      .pagination-buttons {{
        display: flex;
        gap: 0.5em;
      }}

      .pagination-buttons button {{
        padding: 0.5em 1em;
        font-size: 0.85rem;
      }}

      .pagination-buttons button:disabled {{
        opacity: 0.4;
        cursor: not-allowed;
      }}

      .collection-section {{
        margin: 3em 0;
      }}

      .collection-header {{
        cursor: pointer;
        background: rgba(212, 165, 199, 0.1);
        border: 1px solid var(--witch-plum);
        border-radius: 12px;
        padding: 1em 1.5em;
        margin-bottom: 1em;
        transition: all 0.3s ease;
        user-select: none;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1em;
      }}

      .collection-header:hover {{
        background: rgba(168, 87, 126, 0.15);
        border-color: var(--witch-rose);
      }}

      .header-content {{
        display: flex;
        align-items: center;
        gap: 0.5em;
        flex: 1;
        min-width: 0;
        flex-wrap: wrap;
      }}

      .collection-name {{
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex-shrink: 1;
        min-width: 0;
      }}

      .toggle-icon {{
        font-family: monospace;
        font-size: 1.5rem;
        color: var(--witch-rose);
        flex-shrink: 0;
      }}

      .collection-list {{
        background: rgba(212, 165, 199, 0.05);
        border: 1px solid rgba(68, 39, 90, 0.3);
        border-radius: 12px;
        padding: 1.5em;
        margin-bottom: 2em;
      }}

      .collection-list.collapsed {{
        display: none;
      }}

      .collection-description {{
        font-style: italic;
        color: var(--witch-plum);
        margin-bottom: 1em;
        padding-bottom: 1em;
        border-bottom: 1px solid rgba(68, 39, 90, 0.2);
      }}

      .member-count {{
        font-size: 0.85rem;
        color: var(--witch-rose);
        margin-bottom: 1em;
      }}

      .member-list {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 0.5em;
      }}

      .member-link {{
        font-size: 0.85rem;
        padding: 0.5em;
        background: rgba(245, 245, 245, 0.5);
        border-radius: 8px;
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }}

      .is-dark .member-link {{
        background: rgba(10, 0, 9, 0.5);
      }}

      .no-results {{
        text-align: center;
        padding: 2em;
        color: var(--witch-plum);
        font-style: italic;
      }}

      .section-type {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-left: 0.5em;
        vertical-align: middle;
      }}

      .type-starter {{
        background: rgba(168, 87, 126, 0.2);
        color: var(--witch-purple);
      }}

      .type-block {{
        background: rgba(200, 60, 60, 0.2);
        color: #993333;
      }}

      .type-curated {{
        background: rgba(80, 150, 120, 0.2);
        color: #2B5A45;
      }}

      .member-count-badge {{
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-left: 0.75em;
        background: rgba(68, 39, 90, 0.15);
        color: var(--witch-rose);
        vertical-align: middle;
      }}

      .expand-all {{
        margin: 1em 0;
        text-align: center;
      }}

      .expand-all button {{
        margin: 0 0.5em;
      }}

      @media screen and (max-width: 625px) {{
        .stats-grid {{
          grid-template-columns: 1fr 1fr;
        }}

        .member-list {{
          grid-template-columns: 1fr;
        }}
      }}

      /* Hikari please do not remove this i need it */
      footer {{
        z-index: 10000;
      }}
    </style>
  </head>
  <body>
    <!-- Terms of Use Modal -->
    <div class="cipher-terms-modal" id="cipher-terms-modal">
      <div class="cipher-modal-content">
        <h2>Terms of Use</h2>

        <p>
          By accessing and using this archive, you acknowledge and agree to the following terms:
        </p>

        <h3>Informational Use Only</h3>
        <p>
          This archive is provided strictly for <strong>informational and educational purposes</strong>.
          You agree that you will <strong>NOT</strong> use this data for:
        </p>
        <ul>
          <li>Harassment, doxxing, or targeted attacks of any kind</li>
          <li>Criminal activity or planning criminal activity</li>
          <li>Violation of any applicable laws or regulations</li>
          <li>Circumventing Bluesky's moderation or safety systems</li>
          <li>Commercial purposes without prior written consent</li>
        </ul>

        <h3>Liability Disclaimer</h3>
        <p>
          This archive is provided <strong>"AS-IS"</strong> with <strong>NO WARRANTIES</strong> of any kind.
          NHCarrigan and the archive maintainers:
        </p>
        <ul>
          <li>Make no claims about the accuracy, completeness, or timeliness of the data</li>
          <li>Are not responsible for any consequences arising from use or misuse of this data</li>
          <li>Do not endorse, verify, or make claims about any accounts included in these lists</li>
          <li>Are not liable for any damages (direct, indirect, incidental, or consequential) resulting from your use of this archive</li>
        </ul>

        <h3>Third-Party Content</h3>
        <p>
          The lists archived here were created by a third party. We are not responsible for:
        </p>
        <ul>
          <li>The criteria used to include or exclude accounts</li>
          <li>The accuracy or fairness of list membership</li>
          <li>Any harm caused by inclusion or exclusion from these lists</li>
        </ul>

        <h3>Removal Requests</h3>
        <p>
          Removal requests will <strong>not be honoured</strong> at this level.
          This archive periodically refreshes from the source Bluesky account.
          Any changes made there will be reflected here automatically.
        </p>

        <h3>Intellectual Property</h3>
        <p>
          This is a transformative work falling under NHCarrigan's intellectual property.
          All rights reserved.
        </p>

        <div class="cipher-modal-actions">
          <button id="cipher-decline-terms" class="cipher-decline-btn">Decline</button>
          <button id="cipher-accept-terms">I Accept</button>
        </div>
      </div>
    </div>

    <!-- Blocked message (shown if user declines) -->
    <div class="cipher-blocked-message" id="cipher-blocked-message">
      <h2>Access Denied</h2>
      <p>You must accept the Terms of Use to access this archive.</p>
      <p><button onclick="location.reload()">Try Again</button></p>
    </div>

    <main id="main-content" style="display: none;">
      <h1>Cipher</h1>

      <div class="disclaimer">
        <h2>About This Archive</h2>
        <p>
          This page is a public backup of <a href="https://bsky.app/profile/gothicwtf.eurosky.social" target="_blank" rel="noopener noreferrer">@gothicwtf.eurosky.social</a>'s
          Bluesky starter packs, blocklists, and curated lists. It exists to preserve these community resources during her account suspension.
        </p>
        <p>
          <strong>Last Updated:</strong> {today}
        </p>
        <p>
          <strong>Legal Notice:</strong> This is a transformative work falling under NHCarrigan's intellectual property.
          We make no claims as to any of the accounts included in these lists — they are archived as-is from public data.
          Removal requests will not be honoured at this level; we periodically refresh from the source account, so any changes
          made there will be reflected here.
        </p>
      </div>

      <div class="stats-grid" id="stats-grid">
        <!-- Stats will be populated after data loads -->
      </div>

      <input
        type="text"
        id="search"
        class="search-box"
        placeholder="Search collections by name or description..."
      />

      <div class="page-size-control">
        <label>Items per page:</label>
        <label><input type="radio" name="pageSize" value="10"> 10</label>
        <label><input type="radio" name="pageSize" value="25" checked> 25</label>
        <label><input type="radio" name="pageSize" value="50"> 50</label>
        <label><input type="radio" name="pageSize" value="100"> 100</label>
      </div>

      <div class="expand-all">
        <button id="expand-all">Expand All</button>
        <button id="collapse-all">Collapse All</button>
      </div>

      <div id="loading-message" style="text-align: center; padding: 3em; color: var(--witch-plum);">
        <p style="font-size: 1.2rem;">Loading collections...</p>
      </div>

      <div id="collections-container"></div>

      <div id="no-results" class="no-results" style="display: none;">
        No collections match your search.
      </div>
    </main>

    <script>
      // Terms of Use modal handling
      // Wait for global headers to initialize before showing our modal
      function initCipherTermsModal() {{
        const TERMS_ACCEPTED_KEY = 'cipher_terms_accepted';
        const termsModal = document.getElementById('cipher-terms-modal');
        const mainContent = document.getElementById('main-content');
        const blockedMessage = document.getElementById('cipher-blocked-message');

        // Check if terms were previously accepted
        const termsAccepted = localStorage.getItem(TERMS_ACCEPTED_KEY);

        if (termsAccepted === 'true') {{
          // Already accepted - show content
          mainContent.style.display = 'block';
        }} else {{
          // Show terms modal after a small delay to let headers initialize
          setTimeout(() => {{
            termsModal.classList.add('active');
          }}, 500);
        }}

        // Accept button
        document.getElementById('cipher-accept-terms').addEventListener('click', () => {{
          localStorage.setItem(TERMS_ACCEPTED_KEY, 'true');
          termsModal.classList.remove('active');
          mainContent.style.display = 'block';
        }});

        // Decline button
        document.getElementById('cipher-decline-terms').addEventListener('click', () => {{
          termsModal.classList.remove('active');
          blockedMessage.classList.add('active');
        }});
      }}

      // Initialize when DOM is ready
      if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initCipherTermsModal);
      }} else {{
        initCipherTermsModal();
      }}

      // Global state
      let collections = [];
      let collapsedState = {{}};
      let currentPages = {{}}; // Track current page for each collection
      let pageSize = 25; // Default page size

      // Load data from data.json
      async function loadData() {{
        try {{
          const response = await fetch('data.json');
          if (!response.ok) {{
            throw new Error(`HTTP error! status: ${{response.status}}`);
          }}
          const data = await response.json();

          // Combine all collections with type tags
          collections = [
            ...data.starterPacks.map(c => ({{ ...c, type: 'starter' }})),
            ...data.blocklists.map(c => ({{ ...c, type: 'block' }})),
            ...data.curatedLists.map(c => ({{ ...c, type: 'curated' }}))
          ];

          // Calculate and display statistics
          const totalStarterMembers = data.starterPacks.reduce((sum, sp) => sum + sp.members.length, 0);
          const totalBlocked = data.blocklists.reduce((sum, bl) => sum + bl.members.length, 0);
          const totalCuratedMembers = data.curatedLists.reduce((sum, cl) => sum + cl.members.length, 0);

          document.getElementById('stats-grid').innerHTML = `
            <div class="stat-card">
              <span class="stat-number">${{data.starterPacks.length}}</span>
              <span class="stat-label">Starter Packs</span>
            </div>
            <div class="stat-card">
              <span class="stat-number">${{data.blocklists.length}}</span>
              <span class="stat-label">Blocklists</span>
            </div>
            <div class="stat-card">
              <span class="stat-number">${{data.curatedLists.length}}</span>
              <span class="stat-label">Curated Lists</span>
            </div>
            <div class="stat-card">
              <span class="stat-number">${{totalStarterMembers}}</span>
              <span class="stat-label">Starter Pack Members</span>
            </div>
            <div class="stat-card">
              <span class="stat-number">${{totalBlocked}}</span>
              <span class="stat-label">Blocked Accounts</span>
            </div>
            <div class="stat-card">
              <span class="stat-number">${{totalCuratedMembers}}</span>
              <span class="stat-label">Curated Members</span>
            </div>
          `;

          // Initial render
          renderCollections();

          // Hide loading message
          const loadingMsg = document.getElementById('loading-message');
          if (loadingMsg) loadingMsg.style.display = 'none';
        }} catch (error) {{
          console.error('Failed to load data:', error);
          document.getElementById('stats-grid').innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; color: var(--witch-rose); padding: 2em;">
              <strong>Failed to load collection data.</strong><br>
              Please try refreshing the page.
            </div>
          `;
        }}
      }}

      function renderCollections(filtered = collections) {{
        const container = document.getElementById('collections-container');
        const noResults = document.getElementById('no-results');

        if (filtered.length === 0) {{
          container.innerHTML = '';
          noResults.style.display = 'block';
          return;
        }}

        noResults.style.display = 'none';

        const typeLabels = {{
          'starter': 'Starter Pack',
          'block': 'Blocklist',
          'curated': 'Curated List'
        }};

        const html = filtered.map((collection, index) => {{
          const id = `collection-${{index}}`;
          const isCollapsed = collapsedState[id] !== undefined ? collapsedState[id] : true;

          // Pagination
          const currentPage = currentPages[id] || 1;
          const totalMembers = collection.members.length;
          const totalPages = Math.ceil(totalMembers / pageSize);
          const startIndex = (currentPage - 1) * pageSize;
          const endIndex = Math.min(startIndex + pageSize, totalMembers);
          const currentMembers = collection.members.slice(startIndex, endIndex);

          return `
            <div class="collection-section">
              <div class="collection-header" data-id="${{id}}">
                <div class="header-content">
                  <h3 class="collection-name">${{collection.name}}</h3>
                  <span class="section-type type-${{collection.type}}">${{typeLabels[collection.type]}}</span>
                  <span class="member-count-badge">${{collection.members.length}} account${{collection.members.length === 1 ? '' : 's'}}</span>
                </div>
                <span class="toggle-icon">${{isCollapsed ? '+' : '−'}}</span>
              </div>
              <div class="collection-list${{isCollapsed ? ' collapsed' : ''}}" id="${{id}}">
                ${{collection.description ? `<p class="collection-description">${{collection.description}}</p>` : ''}}
                <div class="member-list">
                  ${{currentMembers.map(did =>
                    `<a href="https://bsky.app/profile/${{did}}" class="member-link" target="_blank" rel="noopener noreferrer">${{did}}</a>`
                  ).join('')}}
                </div>
                ${{totalPages > 1 ? `
                  <div class="pagination-controls">
                    <div class="pagination-info">
                      Showing ${{startIndex + 1}}-${{endIndex}} of ${{totalMembers}}
                    </div>
                    <div class="pagination-buttons">
                      <button
                        class="prev-page"
                        data-id="${{id}}"
                        ${{currentPage === 1 ? 'disabled' : ''}}
                      >← Prev</button>
                      <span style="margin: 0 0.5em; color: var(--witch-plum);">Page ${{currentPage}} of ${{totalPages}}</span>
                      <button
                        class="next-page"
                        data-id="${{id}}"
                        ${{currentPage === totalPages ? 'disabled' : ''}}
                      >Next →</button>
                    </div>
                  </div>
                ` : ''}}
              </div>
            </div>
          `;
        }}).join('');

        container.innerHTML = html;

        // Attach click handlers for headers
        document.querySelectorAll('.collection-header').forEach(header => {{
          header.addEventListener('click', () => {{
            const id = header.getAttribute('data-id');
            const list = document.getElementById(id);
            const icon = header.querySelector('.toggle-icon');

            list.classList.toggle('collapsed');
            const isCollapsed = list.classList.contains('collapsed');
            collapsedState[id] = isCollapsed;
            icon.textContent = isCollapsed ? '+' : '−';
          }});
        }});

        // Attach pagination handlers
        document.querySelectorAll('.prev-page').forEach(btn => {{
          btn.addEventListener('click', () => {{
            const id = btn.getAttribute('data-id');
            currentPages[id] = (currentPages[id] || 1) - 1;
            renderCollections(filtered);
          }});
        }});

        document.querySelectorAll('.next-page').forEach(btn => {{
          btn.addEventListener('click', () => {{
            const id = btn.getAttribute('data-id');
            currentPages[id] = (currentPages[id] || 1) + 1;
            renderCollections(filtered);
          }});
        }});

        // Auto-shrink collection name to fit in one line
        document.querySelectorAll('.collection-name').forEach(nameEl => {{
          const headerContent = nameEl.parentElement;
          const badges = headerContent.querySelectorAll('.section-type, .member-count-badge');
          let fontSize = parseFloat(window.getComputedStyle(nameEl).fontSize);
          const minFontSize = 12; // Don't shrink below 12px

          // Calculate total width of badges
          let badgesWidth = 0;
          badges.forEach(badge => {{
            badgesWidth += badge.offsetWidth;
          }});

          // Account for gaps between elements (0.5em per gap)
          const gapWidth = badges.length * 8; // Approximate 0.5em

          // Available width for the name
          const availableWidth = headerContent.clientWidth - badgesWidth - gapWidth - 20; // 20px safety

          // Shrink until it fits
          while (nameEl.scrollWidth > availableWidth && fontSize > minFontSize) {{
            fontSize -= 0.5;
            nameEl.style.fontSize = fontSize + 'px';
          }}
        }});
      }}

      function filterCollections(query) {{
        const lowerQuery = query.toLowerCase();
        const filtered = collections.filter(c =>
          c.name.toLowerCase().includes(lowerQuery) ||
          (c.description && c.description.toLowerCase().includes(lowerQuery))
        );
        renderCollections(filtered);
      }}

      // Load data and render
      loadData();

      // Search
      document.getElementById('search').addEventListener('input', (e) => {{
        filterCollections(e.target.value);
      }});

      // Page size change
      document.querySelectorAll('input[name="pageSize"]').forEach(radio => {{
        radio.addEventListener('change', (e) => {{
          pageSize = parseInt(e.target.value);
          // Reset all pages to 1 when page size changes
          currentPages = {{}};
          renderCollections();
        }});
      }});

      // Expand/collapse all
      document.getElementById('expand-all').addEventListener('click', () => {{
        document.querySelectorAll('.collection-list').forEach(list => {{
          list.classList.remove('collapsed');
          collapsedState[list.id] = false;
        }});
        document.querySelectorAll('.toggle-icon').forEach(icon => {{
          icon.textContent = '−';
        }});
      }});

      document.getElementById('collapse-all').addEventListener('click', () => {{
        document.querySelectorAll('.collection-list').forEach(list => {{
          list.classList.add('collapsed');
          collapsedState[list.id] = true;
        }});
        document.querySelectorAll('.toggle-icon').forEach(icon => {{
          icon.textContent = '+';
        }});
      }});
    </script>
  </body>
</html>
'''

    return html


def main():
    print("Parsing markdown files...")
    starter_packs = parse_markdown_collections("../markdown/starter_packs_export.md")
    blocklists = parse_markdown_collections("../markdown/blocklists.md")
    curated_lists = parse_markdown_collections("../markdown/curated_lists.md")

    print(f"Found {len(starter_packs)} starter packs")
    print(f"Found {len(blocklists)} blocklists")
    print(f"Found {len(curated_lists)} curated lists")

    # Write data.json
    print("\nGenerating data.json...")
    data = {
        "starterPacks": starter_packs,
        "blocklists": blocklists,
        "curatedLists": curated_lists,
        "generatedAt": date.today().isoformat()
    }
    with open("../data.json", "w") as f:
        json.dump(data, f, indent=2)
    print("✅ data.json generated successfully!")

    print("\nGenerating site.html...")
    html = generate_html(starter_packs, blocklists, curated_lists)

    with open("../site.html", "w") as f:
        f.write(html)

    print("✅ site.html generated successfully!")


if __name__ == "__main__":
    main()
