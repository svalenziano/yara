import os
import sys
from textwrap import dedent

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from rich.live import Live

from yara.cli.colors import console
from yara.cli.ui_helpers import home_panel, loading_panel, render_home, whitespace
from yara.db.pgvector import (
    deactivate_project,
    get_or_create_project,
    list_projects,
    update_project,
)
from yara.services.ingest import ingest_files_to_db


class WizardCancelled(Exception):
    pass


def startup_loop() -> int:
    while True:
        console.clear()
        projects = list_projects()

        if not projects:
            whitespace(3)
            console.print(
                home_panel(
                    "No projects found. Create one to get started.\n\n/create — create a new project"
                )
            )
            whitespace(3)
            answer = (
                prompt(HTML("<ansiblue>Create a new project? [y/n]: </ansiblue>"))
                .strip()
                .lower()
            )
            if answer != "y":
                console.print("Goodbye!")
                sys.exit(0)
            return project_wizard()

        lines = ""
        for i, p in enumerate(projects):
            name = p["name"]
            desc = p["description"] or ""
            count = p["file_count"]
            lines += f"{i + 1}) {name}"
            lines += f"[grey50]  {desc}  ({count})[/grey50]\n"

        lines += dedent("""\nTry:
  Type a number to open a project
  /create = setup a new project
  /edit   = edit an existing project
  /delete = archive a project
  """)

        render_home(lines)

        choice = prompt(HTML("<ansiblue>❯ </ansiblue>")).strip()

        if choice == "/create":
            try:
                console.clear()
                return project_wizard()
            except WizardCancelled:
                continue

        if choice == "/edit":
            console.clear()
            _pick_and_edit(projects)
            continue

        if choice == "/delete":
            console.clear()
            _pick_and_delete(projects)
            continue

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                return projects[idx]["id"]

        console.print("[yellow]Invalid choice. Try again.[/yellow]")


def project_wizard() -> int:
    # Step 1: name
    try:
        name = prompt(HTML("<ansiblue>Project name (≤ 40 chars): </ansiblue>")).strip()
    except (KeyboardInterrupt, EOFError):
        raise WizardCancelled

    if not name or len(name) > 40:
        console.print("[yellow]Name must be 1–40 characters.[/yellow]")
        raise WizardCancelled

    # Step 2: description
    try:
        description = (
            prompt(HTML("<ansiblue>Description (optional): </ansiblue>")).strip()
            or None
        )
    except (KeyboardInterrupt, EOFError):
        raise WizardCancelled

    # Step 3: ingestion path
    while True:
        try:
            path = prompt(HTML("<ansiblue>Ingestion path: </ansiblue>")).strip()
        except (KeyboardInterrupt, EOFError):
            raise WizardCancelled

        if os.path.isdir(path):
            break
        console.print(f"[yellow]'{path}' is not a valid directory. Try again.[/yellow]")

    # Step 4: create project
    project_id = get_or_create_project(name, path, description)

    # Step 5: ingest with spinner
    console.print()
    with Live(loading_panel(), console=console, refresh_per_second=12):
        ingest_files_to_db(path, project_id)
    console.print()

    return project_id


def edit_wizard(project: dict) -> None:
    console.print(f"[bold]Editing:[/bold] {project['name']}")
    try:
        name = prompt(
            HTML("<ansiblue>New name (≤ 40 chars): </ansiblue>"),
            default=project["name"],
        ).strip()
    except (KeyboardInterrupt, EOFError):
        return

    if not name or len(name) > 40:
        console.print("[yellow]Name must be 1–40 characters. Edit cancelled.[/yellow]")
        return

    try:
        description = (
            prompt(
                HTML("<ansiblue>Description (optional): </ansiblue>"),
                default=project["description"] or "",
            ).strip()
            or None
        )
    except (KeyboardInterrupt, EOFError):
        return

    update_project(project["id"], name, description)
    console.print(f"[green]Project updated.[/green]")


def delete_confirm(project: dict) -> None:
    console.print(f"[bold]Project:[/bold] {project['name']}")
    try:
        answer = (
            prompt(HTML("<ansired>Mark as inactive? [y/n]: </ansired>")).strip().lower()
        )
    except (KeyboardInterrupt, EOFError):
        return

    if answer == "y":
        deactivate_project(project["id"])
        console.print("[green]Project marked as inactive.[/green]")


def _pick_project(projects: list[dict], action: str) -> dict | None:
    console.print(f"[bold]Select a project to {action}:[/bold]")
    for i, p in enumerate(projects):
        console.print(f"  {i + 1}) {p['name']}")
    try:
        choice = prompt(HTML("<ansiblue>Number: </ansiblue>")).strip()
    except (KeyboardInterrupt, EOFError):
        return None
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(projects):
            return projects[idx]
    console.print("[yellow]Invalid selection.[/yellow]")
    return None


def _pick_and_edit(projects: list[dict]) -> None:
    project = _pick_project(projects, "edit")
    if project:
        edit_wizard(project)


def _pick_and_delete(projects: list[dict]) -> None:
    project = _pick_project(projects, "delete")
    if project:
        delete_confirm(project)
