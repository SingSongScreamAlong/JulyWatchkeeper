#!/usr/bin/env python3
"""
Merge additional sources into main sources configuration

This script combines sources.json with additional_sources.json
"""

import json
import sys
from pathlib import Path

def merge_sources():
    """Merge all source files into a comprehensive configuration."""

    # Get project root
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config"

    # Load main sources
    main_sources_file = config_dir / "sources.json"
    additional_sources_file = config_dir / "additional_sources.json"

    try:
        with open(main_sources_file, 'r') as f:
            main_config = json.load(f)

        with open(additional_sources_file, 'r') as f:
            additional_config = json.load(f)

        # Get existing sources
        existing_sources = main_config.get("sources", [])
        new_sources = additional_config.get("additional_sources", [])

        # Track existing source names to avoid duplicates
        existing_names = {source["name"] for source in existing_sources}

        # Add new sources that don't exist
        added_count = 0
        for source in new_sources:
            if source["name"] not in existing_names:
                existing_sources.append(source)
                added_count += 1
                print(f"✓ Added: {source['name']}")
            else:
                print(f"- Skipped (already exists): {source['name']}")

        # Update main config
        main_config["sources"] = existing_sources

        # Create backup
        backup_file = config_dir / "sources.json.backup"
        with open(backup_file, 'w') as f:
            json.dump(main_config, f, indent=4)
        print(f"\n✓ Created backup: {backup_file}")

        # Write merged config
        with open(main_sources_file, 'w') as f:
            json.dump(main_config, f, indent=4)

        print(f"\n{'='*60}")
        print(f"✓ Successfully merged sources!")
        print(f"{'='*60}")
        print(f"Total sources: {len(existing_sources)}")
        print(f"Sources added: {added_count}")
        print(f"{'='*60}\n")

        # Print statistics
        print_statistics(existing_sources)

        return True

    except FileNotFoundError as e:
        print(f"❌ Error: Could not find source file: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def print_statistics(sources):
    """Print statistics about the sources."""

    # Count by category
    categories = {}
    for source in sources:
        category = source.get("category", "unknown")
        categories[category] = categories.get(category, 0) + 1

    # Count by reliability
    reliability_counts = {}
    for source in sources:
        reliability = source.get("reliability", 0)
        reliability_counts[reliability] = reliability_counts.get(reliability, 0) + 1

    # Count enabled/disabled
    enabled = sum(1 for s in sources if s.get("enabled", True))
    disabled = len(sources) - enabled

    # Count by priority
    priorities = {}
    for source in sources:
        priority = source.get("priority", "medium")
        priorities[priority] = priorities.get(priority, 0) + 1

    print("STATISTICS")
    print("="*60)

    print(f"\nStatus:")
    print(f"  Enabled:  {enabled}")
    print(f"  Disabled: {disabled}")

    print(f"\nBy Category:")
    for category, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {category:25s} {count:3d}")

    print(f"\nBy Reliability:")
    for reliability, count in sorted(reliability_counts.items(), key=lambda x: -x[0]):
        print(f"  {reliability}/10: {count:3d} sources")

    print(f"\nBy Priority:")
    for priority, count in sorted(priorities.items()):
        print(f"  {priority:10s} {count:3d}")

    print("="*60)


if __name__ == "__main__":
    success = merge_sources()
    sys.exit(0 if success else 1)
