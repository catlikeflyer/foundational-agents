"""CLI entrypoint for the ``fd-agents`` command.

Provides an ``install`` subcommand that unpacks bundled agent template files
from the package into the user's local project directory structure, ready for
use with Claude Code or GitHub Copilot.

Usage::

    fd-agents install            # unpack to CWD
    fd-agents install --global   # unpack to $HOME
"""

from __future__ import annotations

import shutil
import sys
from importlib import resources
from pathlib import Path

import click


# ---------------------------------------------------------------------------
# Template mapping: source subdirectory → target directory relative to root
# ---------------------------------------------------------------------------

TEMPLATE_MAP: dict[str, str] = {
    "claude": ".claude/agents",
    "copilot": ".github/agents",
}

# File extension patterns per source subdirectory
EXTENSION_MAP: dict[str, str] = {
    "claude": ".SKILL.md",
    "copilot": ".agent.md",
}


def _get_template_source() -> resources.abc.Traversable:
    """Locate the bundled templates package directory.

    Returns:
        A Traversable reference to the templates package.
    """
    return resources.files("my_foundational_agents.templates")


def _copy_templates(
    source_subdir: str,
    target_dir: Path,
    extension: str,
) -> list[str]:
    """Copy template files from a source subdirectory to target.

    Args:
        source_subdir: Name of the subdirectory under templates/ (e.g. 'claude').
        target_dir: Absolute path to the destination directory.
        extension: File extension to match (e.g. '.SKILL.md').

    Returns:
        List of filenames that were copied.
    """
    templates_root = _get_template_source()
    source_path = templates_root.joinpath(source_subdir)

    copied: list[str] = []

    # Iterate through source directory
    try:
        for item in source_path.iterdir():
            name = item.name
            if name.endswith(extension):
                # Read content from the package resource
                content = item.read_text(encoding="utf-8")

                # Write to target
                dest_file = target_dir / name
                dest_file.write_text(content, encoding="utf-8")
                copied.append(name)
    except (TypeError, FileNotFoundError) as exc:
        click.echo(
            click.style(f"  ⚠ Could not read templates/{source_subdir}/: {exc}", fg="yellow"),
            err=True,
        )

    return copied


# ---------------------------------------------------------------------------
# CLI Group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(package_name="my-foundational-agents")
def main() -> None:
    """fd-agents: Foundational Agents CLI.

    Manage and install AI agent persona templates for Claude and GitHub Copilot.
    """


@main.command()
@click.option(
    "--global",
    "use_global",
    is_flag=True,
    default=False,
    help="Install templates to $HOME instead of the current directory.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing template files.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be installed without writing files.",
)
def install(use_global: bool, force: bool, dry_run: bool) -> None:
    """Unpack agent templates to local project directories.

    Copies bundled template files to:

    \b
    • Claude:  .claude/agents/*.SKILL.md
    • Copilot: .github/agents/*.agent.md

    By default, targets the current working directory. Use --global to
    install to $HOME.
    """
    root = Path.home() if use_global else Path.cwd()

    click.echo(
        click.style("🚀 Foundational Agents — Template Installer", fg="cyan", bold=True)
    )
    click.echo(f"   Target root: {root}")
    if dry_run:
        click.echo(click.style("   (dry run — no files will be written)", fg="yellow"))
    click.echo()

    total_copied = 0

    for source_subdir, target_rel in TEMPLATE_MAP.items():
        extension = EXTENSION_MAP[source_subdir]
        target_dir = root / target_rel

        click.echo(
            click.style(f"📁 {source_subdir}/", fg="blue", bold=True)
            + f" → {target_dir}"
        )

        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)

        copied = _copy_templates(source_subdir, target_dir, extension) if not dry_run else []

        if dry_run:
            # List what would be copied
            templates_root = _get_template_source()
            source_path = templates_root.joinpath(source_subdir)
            try:
                for item in source_path.iterdir():
                    if item.name.endswith(extension):
                        dest = target_dir / item.name
                        exists = dest.exists()
                        status = (
                            click.style("(exists, would skip)", fg="yellow")
                            if exists and not force
                            else click.style("(would overwrite)", fg="red")
                            if exists
                            else click.style("(new)", fg="green")
                        )
                        click.echo(f"   • {item.name} {status}")
                        total_copied += 1
            except (TypeError, FileNotFoundError):
                click.echo(click.style("   ⚠ Source templates not found", fg="yellow"))
        else:
            for name in copied:
                click.echo(click.style(f"   ✓ {name}", fg="green"))
            total_copied += len(copied)

        click.echo()

    # Summary
    action = "would install" if dry_run else "installed"
    click.echo(
        click.style(f"✅ Done — {action} {total_copied} template(s)", fg="green", bold=True)
    )

    if not dry_run and total_copied > 0:
        click.echo()
        click.echo("Next steps:")
        click.echo("  • Claude:  Templates are in .claude/agents/ — Claude Code will discover them automatically.")
        click.echo("  • Copilot: Templates are in .github/agents/ — commit them to enable in GitHub Copilot.")
