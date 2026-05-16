.PHONY: compile clean help

# Default target
compile:
	@echo "🔄 Fetching latest data from Bluesky..."
	@cd scripts && python3 fetch_starter_packs.py
	@cd scripts && python3 fetch_blocklists.py
	@cd scripts && python3 fetch_curated_lists.py
	@cd scripts && python3 fetch_custom_feeds.py
	@echo ""
	@echo "🏗️  Generating site files..."
	@cd scripts && python3 generate_site.py
	@echo ""
	@echo "✨ Site compiled successfully!"
	@echo "📦 Output files:"
	@ls -lh data.json site.html

clean:
	@echo "🧹 Cleaning generated files..."
	@rm -f data.json site.html
	@rm -f markdown/*.md
	@echo "✅ Clean complete!"

help:
	@echo "Cipher - Bluesky Collections Archive"
	@echo ""
	@echo "Available targets:"
	@echo "  make compile    - Fetch latest data and regenerate site (default)"
	@echo "  make clean      - Remove all generated files"
	@echo "  make help       - Show this help message"
