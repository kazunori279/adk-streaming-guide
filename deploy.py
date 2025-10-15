#!/usr/bin/env python3
"""
Deploy script for ADK streaming guide.

Deploys:
1. docs/part2.md -> ../adk-docs/docs/streaming/dev-guide/part2.md
   - Rewrites links to match destination project structure
2. src/part2 -> ../adk-docs/examples/python/snippets/streaming/dev-guide/part2
   - Excludes __pycache__ and other build artifacts
"""

import os
import re
import shutil
from pathlib import Path


def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def rewrite_docs_links(content: str) -> str:
    """
    Rewrite relative links in documentation for the destination project.

    Transforms:
    - ../src/part2/README.md -> ../../../examples/python/snippets/streaming/dev-guide/part2/README.md
    """
    # Rewrite link to src/part2/README.md
    content = re.sub(
        r'\(\.\./src/part2/README\.md\)',
        r'(../../../examples/python/snippets/streaming/dev-guide/part2/README.md)',
        content
    )

    return content


def deploy_docs(source_root: Path, dest_root: Path) -> None:
    """Deploy documentation with link rewriting."""
    source_file = source_root / "docs" / "part2.md"
    dest_file = dest_root / "docs" / "streaming" / "dev-guide" / "part2.md"

    print(f"Deploying docs: {source_file} -> {dest_file}")

    # Read source file
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Rewrite links
    content = rewrite_docs_links(content)

    # Ensure destination directory exists
    ensure_dir(dest_file.parent)

    # Write to destination
    with open(dest_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Deployed documentation to {dest_file}")


def should_exclude(path: Path) -> bool:
    """Check if a file/directory should be excluded from deployment."""
    exclude_patterns = {
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '.DS_Store',
        '.pytest_cache',
        '*.egg-info',
    }

    name = path.name

    # Check exact matches
    if name in exclude_patterns:
        return True

    # Check wildcard patterns
    for pattern in exclude_patterns:
        if '*' in pattern:
            import fnmatch
            if fnmatch.fnmatch(name, pattern):
                return True

    return False


def deploy_code(source_root: Path, dest_root: Path) -> None:
    """Deploy code examples."""
    source_dir = source_root / "src" / "part2"
    dest_dir = dest_root / "examples" / "python" / "snippets" / "streaming" / "dev-guide" / "part2"

    print(f"Deploying code: {source_dir} -> {dest_dir}")

    # Remove existing destination if it exists
    if dest_dir.exists():
        shutil.rmtree(dest_dir)

    # Ensure destination directory exists
    ensure_dir(dest_dir)

    # Copy files, excluding build artifacts
    for item in source_dir.iterdir():
        if should_exclude(item):
            print(f"  Skipping: {item.name}")
            continue

        dest_item = dest_dir / item.name

        if item.is_file():
            shutil.copy2(item, dest_item)
            print(f"  Copied: {item.name}")
        elif item.is_dir():
            shutil.copytree(item, dest_item, ignore=lambda d, files: [f for f in files if should_exclude(Path(d) / f)])
            print(f"  Copied: {item.name}/")

    print(f"✓ Deployed code to {dest_dir}")


def main():
    """Main deployment function."""
    # Get source and destination roots
    source_root = Path(__file__).parent.resolve()
    dest_root = source_root.parent / "adk-docs"

    print(f"Source: {source_root}")
    print(f"Destination: {dest_root}")
    print()

    # Check if destination exists
    if not dest_root.exists():
        print(f"Error: Destination directory not found: {dest_root}")
        print("Please ensure ../adk-docs exists relative to this repository.")
        return 1

    # Deploy documentation
    try:
        deploy_docs(source_root, dest_root)
        print()
    except Exception as e:
        print(f"Error deploying docs: {e}")
        return 1

    # Deploy code
    try:
        deploy_code(source_root, dest_root)
        print()
    except Exception as e:
        print(f"Error deploying code: {e}")
        return 1

    print("✓ Deployment complete!")
    return 0


if __name__ == "__main__":
    exit(main())
