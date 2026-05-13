"""
Build the Bennett Cookbook manuscript and designed output.

Outputs:
  cookbook/the_bennett_cookbook.md
  cookbook/the_bennett_cookbook.html
  cookbook/the_bennett_cookbook.pdf   (requires WeasyPrint + system libs)

Run from repo root:
  python -m src.build_cookbook
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Callable

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

from jinja2 import Environment, FileSystemLoader

from src.models import FullMeal, Recipe

try:
    from weasyprint import HTML as WeasyprintHTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


# ─── Sections definition ────────────────────────────────────────────────────

SECTIONS: list[tuple[str, Callable[[Recipe], bool]]] = [
    ("Weeknight Winners",  lambda r: (r.weeknight_score or 0) >= 7),
    ("Family Favourites",  lambda r: r.family_dinner_candidate),
    ("Pasta",              lambda r: r.category == "Pasta"),
    ("Seafood",            lambda r: r.category == "Seafood"),
    ("Vegetarian",         lambda r: r.category == "Vegetarian"),
    ("Brunch & Breakfast", lambda r: r.category == "Brunch & Breakfast"),
    ("Entertaining",       lambda r: r.entertaining_candidate or (r.entertaining_score or 0) >= 8),
    ("Sides & Sauces",     lambda r: r.category == "Sides & Sauces"),
]


# ─── Load / validate ────────────────────────────────────────────────────────

def load_recipes(path: Path) -> list[Recipe]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Recipe.model_validate(r) for r in raw]


def load_full_meals(path: Path) -> list[FullMeal]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [FullMeal.model_validate(m) for m in raw]


# ─── Jinja2 environment ─────────────────────────────────────────────────────

def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def build_jinja_env(templates_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=True,
    )
    env.filters["slugify"] = slugify
    return env


# ─── Section grouping ───────────────────────────────────────────────────────

def group_sections(recipes: list[Recipe]) -> list[tuple[str, list[Recipe]]]:
    # Only include personal and adapted recipes in the printed cookbook
    cookbook_recipes = [
        r for r in recipes
        if r.record_type.value in ("personal_recipe", "adapted_bennett_recipe")
    ]
    sections = []
    for name, filter_fn in SECTIONS:
        matching = [r for r in cookbook_recipes if filter_fn(r)]
        sections.append((name, matching))
    return sections


# ─── Markdown generation ────────────────────────────────────────────────────

def recipe_to_markdown(r: Recipe) -> str:
    lines: list[str] = []
    lines.append(f"## {r.recipe_name}")
    lines.append("")

    meta_parts = [
        f"**Cuisine:** {r.cuisine}",
        f"**Difficulty:** {r.difficulty.value}",
        f"**Prep:** {r.prep_time_minutes} min",
        f"**Cook:** {r.cook_time_minutes} min",
        f"**Total:** {r.total_time_minutes} min",
        f"**Serves:** {r.serves}",
    ]
    if r.kid_friendly:
        meta_parts.append("**Kid Friendly** ✓")
    lines.append(" · ".join(meta_parts))
    lines.append("")

    ratings: list[str] = []
    if r.nathan_rating is not None:
        ratings.append(f"Nathan {r.nathan_rating}/10")
    if r.leah_rating is not None:
        ratings.append(f"Leah {r.leah_rating}/10")
    if r.nina_rating is not None:
        ratings.append(f"Nina {r.nina_rating}/10")
    if ratings:
        lines.append("**Ratings:** " + " · ".join(ratings))
        lines.append("")

    if r.image_file:
        lines.append(f"![{r.recipe_name}](../images/source/{r.image_file})")
        lines.append("")

    lines.append("### Ingredients")
    lines.append("")
    for ing in r.ingredients:
        lines.append(f"- {ing}")
    lines.append("")

    lines.append("### Method")
    lines.append("")
    for i, step in enumerate(r.method, 1):
        lines.append(f"{i}. {step}")
    lines.append("")

    if r.nathan_tweaks:
        lines.append(f"> **Nathan's Tweaks:** {r.nathan_tweaks}")
        lines.append("")

    if r.substitutions:
        lines.append(f"**Substitutions:** {r.substitutions}")
        lines.append("")

    if r.pairings:
        lines.append("**Pairs well with:** " + ", ".join(r.pairings))
        lines.append("")

    if r.tags:
        lines.append("*Tags: " + ", ".join(f"`{t}`" for t in r.tags) + "*")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def full_meal_to_markdown(m: FullMeal, recipe_lookup: dict[str, Recipe]) -> str:
    lines: list[str] = []
    lines.append(f"## {m.meal_name}")
    lines.append("")
    if m.description:
        lines.append(f"*{m.description}*")
        lines.append("")
    lines.append(f"**Serves:** {m.serves}")
    if m.total_time_estimate:
        lines.append(f"**Total time:** {m.total_time_estimate}")
    lines.append("")
    lines.append("**Components:**")
    lines.append("")
    for rid in m.recipe_ids:
        name = recipe_lookup[rid].recipe_name if rid in recipe_lookup else rid
        lines.append(f"- {name}")
    lines.append("")
    if m.notes:
        lines.append(f"> {m.notes}")
        lines.append("")
    if m.occasions:
        lines.append("*Occasions: " + ", ".join(m.occasions) + "*")
        lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def build_markdown(recipes: list[Recipe], full_meals: list[FullMeal]) -> str:
    sections = group_sections(recipes)
    recipe_lookup = {r.recipe_id: r for r in recipes}

    parts: list[str] = []

    parts.append("# The Bennett Cookbook")
    parts.append("")
    parts.append("*A family recipe collection — curated, tested, and loved.*")
    parts.append("")
    parts.append(f"*Generated: {date.today().strftime('%d %B %Y')}*")
    parts.append("")
    parts.append("---")
    parts.append("")

    # Table of contents
    parts.append("## Table of Contents")
    parts.append("")
    for i, (section_name, section_recipes) in enumerate(sections, 1):
        if section_recipes:
            parts.append(f"{i}. [{section_name}](#{slugify(section_name)}) ({len(section_recipes)} recipes)")
    parts.append(f"{len(sections)+1}. [Full Meal Builds](#full-meal-builds)")
    parts.append(f"{len(sections)+2}. [Recipe Index](#recipe-index)")
    parts.append("")
    parts.append("---")
    parts.append("")

    # Sections
    for section_name, section_recipes in sections:
        if not section_recipes:
            continue
        parts.append(f"# {section_name}")
        parts.append("")
        for recipe in section_recipes:
            parts.append(recipe_to_markdown(recipe))

    # Full Meal Builds
    parts.append("# Full Meal Builds")
    parts.append("")
    for meal in full_meals:
        parts.append(full_meal_to_markdown(meal, recipe_lookup))

    # Recipe Index
    parts.append("# Recipe Index")
    parts.append("")
    parts.append("| Recipe | Category | Cuisine | Serves | Time | Difficulty |")
    parts.append("|---|---|---|---|---|---|")
    for r in sorted(recipes, key=lambda x: x.recipe_name):
        if r.record_type.value in ("personal_recipe", "adapted_bennett_recipe"):
            parts.append(
                f"| {r.recipe_name} | {r.category} | {r.cuisine} "
                f"| {r.serves} | {r.total_time_minutes} min | {r.difficulty.value} |"
            )
    parts.append("")

    # Recipe intake template
    parts.append("---")
    parts.append("")
    parts.append("# Add a New Recipe — Intake Template")
    parts.append("")
    parts.append("```")
    parts.append("Recipe name:")
    parts.append("Category:")
    parts.append("Cuisine:")
    parts.append("Difficulty: Easy / Medium / Advanced")
    parts.append("Prep time (minutes):")
    parts.append("Cook time (minutes):")
    parts.append("Serves:")
    parts.append("Kid-friendly: Yes / No")
    parts.append("Weeknight score (1-10):")
    parts.append("Entertaining score (1-10):")
    parts.append("")
    parts.append("Ingredients:")
    parts.append("  -")
    parts.append("")
    parts.append("Method:")
    parts.append("  1.")
    parts.append("")
    parts.append("Nathan tweaks:")
    parts.append("Substitutions:")
    parts.append("Pairings:")
    parts.append("Full meal build:")
    parts.append("Tags:")
    parts.append("Notes:")
    parts.append("Image idea:")
    parts.append("```")
    parts.append("")

    return "\n".join(parts)


# ─── HTML generation ────────────────────────────────────────────────────────

def build_html(
    recipes: list[Recipe],
    full_meals: list[FullMeal],
    env: Environment,
    out_path: Path,
) -> None:
    sections = group_sections(recipes)
    recipe_lookup = {r.recipe_id: r for r in recipes}

    cookbook_recipes = [
        r for r in recipes
        if r.record_type.value in ("personal_recipe", "adapted_bennett_recipe")
    ]

    template = env.get_template("cookbook.html.j2")
    html = template.render(
        sections=sections,
        full_meals=full_meals,
        all_recipes=cookbook_recipes,
        recipe_lookup=recipe_lookup,
        total_recipes=len(cookbook_recipes),
        total_meals=len(full_meals),
        generated_date=date.today().strftime("%d %B %Y"),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"  HTML → {out_path}")


# ─── PDF generation ─────────────────────────────────────────────────────────

def build_pdf(html_path: Path, pdf_path: Path) -> None:
    if not WEASYPRINT_AVAILABLE:
        print("  PDF  → skipped (WeasyPrint not installed)")
        print("         Install: pip install weasyprint")
        print("         System:  apt install libcairo2 libpango-1.0-0 libpangocairo-1.0-0")
        return
    try:
        WeasyprintHTML(filename=str(html_path)).write_pdf(str(pdf_path))
        print(f"  PDF  → {pdf_path}")
    except Exception as exc:
        print(f"  PDF  → failed: {exc}")


# ─── Entry point ────────────────────────────────────────────────────────────

def main() -> None:
    print("Bennett Cookbook — Building cookbook outputs...")

    recipes    = load_recipes(BASE / "data" / "recipes.json")
    full_meals = load_full_meals(BASE / "data" / "full_meals.json")
    env        = build_jinja_env(BASE / "templates")

    # Markdown
    md_path = BASE / "cookbook" / "the_bennett_cookbook.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(build_markdown(recipes, full_meals), encoding="utf-8")
    print(f"  MD   → {md_path}")

    # HTML
    html_path = BASE / "cookbook" / "the_bennett_cookbook.html"
    build_html(recipes, full_meals, env, html_path)

    # PDF
    pdf_path = BASE / "cookbook" / "the_bennett_cookbook.pdf"
    build_pdf(html_path, pdf_path)

    print(f"\nDone. {len(recipes)} recipes rendered.")


if __name__ == "__main__":
    main()
