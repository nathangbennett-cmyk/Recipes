"""
Bennett Cookbook — Recipe Discovery App

Discover random recipes from RecipeTin Eats and Ottolenghi,
and save them to The Bennett Cookbook in a copyright-safe way.

Run:
  streamlit run src/random_recipe_tin_eats.py
"""

from __future__ import annotations

import json
import random
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import requests
import streamlit as st
from bs4 import BeautifulSoup

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

from src.models import AdaptationStatus, DifficultyLevel, Recipe, RecordType, SaveType

# ─── Source configuration ───────────────────────────────────────────────────

SOURCES: dict[str, dict] = {
    "RecipeTin Eats": {
        "entry_urls": [
            "https://www.recipetineats.com/recipes/",
        ],
        "domain_filter": "recipetineats.com",
        "pagination_pattern": "page/{n}/",
        "cache_file": BASE / "data" / "recipetineats_recipe_index.json",
        "author": "Nagi Maehashi",
        "tag": "recipetineats",
        "max_pages": 10,
    },
    "Ottolenghi": {
        "entry_urls": [
            "https://ottolenghi.co.uk/pages/recipes",
        ],
        "domain_filter": "ottolenghi.co.uk",
        "pagination_pattern": None,
        "cache_file": BASE / "data" / "ottolenghi_recipe_index.json",
        "author": "Yotam Ottolenghi",
        "tag": "ottolenghi",
        "max_pages": 5,
    },
}

CATEGORIES = [
    "Pasta", "Seafood", "Vegetarian", "Brunch & Breakfast",
    "Sides & Sauces", "Entertaining", "Family Favourites", "Weeknight Winners",
    "Chicken", "Beef", "Lamb", "Salad", "Soup", "Dessert", "Other",
]

CUISINES = [
    "Italian", "Japanese", "Middle Eastern", "Australian", "Mediterranean",
    "Asian", "French", "Indian", "Thai", "Mexican", "American", "Modern Australian", "Other",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; BennettCookbook/1.0; personal-use; "
        "github.com/bennettcookbook)"
    )
}

CACHE_MAX_AGE_HOURS = 24


# ─── Utility ────────────────────────────────────────────────────────────────

def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def cache_is_fresh(cache_data: dict) -> bool:
    last_updated = cache_data.get("last_updated")
    if not last_updated:
        return False
    try:
        updated_dt = datetime.fromisoformat(last_updated)
        age_hours = (datetime.now(timezone.utc) - updated_dt).total_seconds() / 3600
        return age_hours < CACHE_MAX_AGE_HOURS
    except (ValueError, TypeError):
        return False


# ─── Scraper ────────────────────────────────────────────────────────────────

def extract_article_metadata(article, domain_filter: str) -> Optional[dict]:
    link_tag = article.find("a", href=True)
    if not link_tag:
        return None

    url = link_tag.get("href", "")
    if not url or domain_filter not in url:
        return None
    if not url.startswith("http"):
        return None

    # Exclude obvious non-recipe pages
    exclude_patterns = [
        "/category/", "/tag/", "/author/", "/about", "/contact",
        "/newsletter", "/privacy", "/terms", "/shop", "/pages/",
        "#", "?", "/search",
    ]
    if any(p in url.lower() for p in exclude_patterns):
        return None

    # Title
    title_tag = article.find(["h2", "h3", "h4"])
    title = title_tag.get_text(strip=True) if title_tag else link_tag.get_text(strip=True)
    if not title or len(title) < 3:
        return None

    # Image
    img = article.find("img")
    image_url = None
    if img:
        image_url = img.get("data-src") or img.get("src") or img.get("data-lazy-src")
        if image_url and image_url.startswith("data:"):
            image_url = None

    # Category
    cat_tag = article.find(class_=re.compile(r"categ|tag|label", re.I))
    category = cat_tag.get_text(strip=True) if cat_tag else None

    # Description
    desc_tag = article.find("p")
    description = desc_tag.get_text(strip=True)[:250] if desc_tag else None

    return {
        "title": title,
        "url": url,
        "category": category,
        "image_url": image_url,
        "description": description,
        "date_indexed": iso_now(),
    }


def scrape_source(source_name: str) -> dict:
    config = SOURCES[source_name]
    seen_urls: set[str] = set()
    recipes: list[dict] = []
    errors: list[str] = []

    for entry_url in config["entry_urls"]:
        page = 1
        max_pages = config.get("max_pages", 5)

        while page <= max_pages:
            if page == 1:
                url = entry_url
            elif config["pagination_pattern"]:
                url = entry_url.rstrip("/") + "/" + config["pagination_pattern"].format(n=page)
            else:
                break

            try:
                resp = requests.get(url, headers=HEADERS, timeout=20)
                if resp.status_code == 404:
                    break
                resp.raise_for_status()
            except requests.RequestException as e:
                errors.append(f"Page {page}: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")

            # Try JSON-LD schema first (most reliable)
            jsonld_recipes = []
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or "")
                    schemas = data if isinstance(data, list) else [data]
                    for schema in schemas:
                        if schema.get("@type") == "Recipe":
                            recipe_url = schema.get("url") or schema.get("@id") or url
                            if config["domain_filter"] in recipe_url and recipe_url not in seen_urls:
                                entry = {
                                    "title": schema.get("name", ""),
                                    "url": recipe_url,
                                    "category": (
                                        schema.get("recipeCategory") or
                                        (schema.get("recipeCuisine") or "")
                                    ),
                                    "image_url": (
                                        (schema.get("image") or {}).get("url")
                                        if isinstance(schema.get("image"), dict)
                                        else (
                                            schema.get("image")[0]
                                            if isinstance(schema.get("image"), list)
                                            else schema.get("image")
                                        )
                                    ),
                                    "description": (schema.get("description") or "")[:250],
                                    "date_indexed": iso_now(),
                                }
                                jsonld_recipes.append(entry)
                                seen_urls.add(recipe_url)
                except (json.JSONDecodeError, AttributeError, TypeError):
                    pass

            if jsonld_recipes:
                recipes.extend(jsonld_recipes)
            else:
                # Fallback: parse article/card elements
                articles = (
                    soup.find_all("article") or
                    soup.find_all(class_=re.compile(r"archive|recipe.card|post.card|recipe.item", re.I))
                )
                new_this_page = 0
                for article in articles:
                    entry = extract_article_metadata(article, config["domain_filter"])
                    if entry and entry["url"] not in seen_urls:
                        recipes.append(entry)
                        seen_urls.add(entry["url"])
                        new_this_page += 1

                if new_this_page == 0 and page > 1:
                    break

            page += 1
            time.sleep(1.2)

    result = {
        "source_name": source_name,
        "last_updated": iso_now(),
        "total_count": len(recipes),
        "recipes": recipes,
        "errors": errors,
    }
    return result


def load_index(source_name: str) -> list[dict]:
    cache_file = SOURCES[source_name]["cache_file"]
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8")).get("recipes", [])
        except (json.JSONDecodeError, KeyError):
            pass
    return []


def save_index(source_name: str, data: dict) -> None:
    cache_file = SOURCES[source_name]["cache_file"]
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_combined_index(source_filter: str) -> list[dict]:
    if source_filter == "Any (both)":
        sources = list(SOURCES.keys())
    else:
        sources = [source_filter]

    all_recipes = []
    for src in sources:
        recipes = load_index(src)
        for r in recipes:
            r["_source"] = src
        all_recipes.extend(recipes)
    return all_recipes


def load_saved_urls() -> set[str]:
    saved_path = BASE / "data" / "saved_external.json"
    if saved_path.exists():
        try:
            saved = json.loads(saved_path.read_text(encoding="utf-8"))
            return {r.get("source_url", "") for r in saved if r.get("source_url")}
        except (json.JSONDecodeError, KeyError):
            pass
    return set()


# ─── Save logic ─────────────────────────────────────────────────────────────

def save_external_recipe(
    recipe: dict,
    editable_title: str,
    category: str,
    cuisine: str,
    difficulty: str,
    serves: str,
    tags_input: str,
    source_notes: str,
    save_type: str,
    try_soon: bool,
    family_dinner: bool,
    entertaining: bool,
    kid_friendly: bool,
    planned_ingredients: Optional[str],
    planned_method: Optional[str],
) -> None:
    source_name = recipe.get("_source") or recipe.get("source_name", "External")
    source_config = SOURCES.get(source_name, {})

    tags = [t.strip() for t in tags_input.split(",") if t.strip()]
    tags += ["external-source", source_config.get("tag", slugify(source_name))]
    tags = list(dict.fromkeys(tags))

    new_entry = {
        "recipe_id": slugify(editable_title) + "-" + date.today().strftime("%Y%m%d"),
        "recipe_name": editable_title,
        "record_type": RecordType.EXTERNAL.value,
        "category": category,
        "cuisine": cuisine,
        "difficulty": difficulty,
        "serves": serves,
        "tags": tags,
        "source_notes": source_notes or None,
        "save_type": save_type,
        "source_url": recipe.get("url"),
        "source_name": source_name,
        "source_author": source_config.get("author") or recipe.get("author"),
        "source_image_url": recipe.get("image_url"),
        "date_saved": date.today().isoformat(),
        "try_soon": try_soon,
        "family_dinner_candidate": family_dinner,
        "entertaining_candidate": entertaining,
        "kid_friendly": kid_friendly,
        "planned_ingredient_changes": planned_ingredients or None,
        "planned_method_changes": planned_method or None,
        "adaptation_status": (
            AdaptationStatus.PENDING.value
            if save_type == SaveType.ADAPT.value
            else AdaptationStatus.NOT_APPLICABLE.value
        ),
        "copyright_status": "reference_only",
        "ingredients": [],
        "method": [],
        "nathan_modified_before_save": True,
    }

    # Validate
    Recipe.model_validate(new_entry)

    saved_path = BASE / "data" / "saved_external.json"
    existing = []
    if saved_path.exists():
        try:
            existing = json.loads(saved_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []

    existing.append(new_entry)
    saved_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


# ─── Session state init ─────────────────────────────────────────────────────

def init_session_state() -> None:
    defaults = {
        "current_recipe": None,
        "save_form_open": False,
        "source_filter": "RecipeTin Eats",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─── UI: Sidebar ────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    with st.sidebar:
        st.title("🍳 Recipe Finder")
        st.caption("Discover and save recipes to The Bennett Cookbook")

        st.divider()

        # Source selector
        source_filter = st.radio(
            "Recipe source",
            ["RecipeTin Eats", "Ottolenghi", "Any (both)"],
            index=["RecipeTin Eats", "Ottolenghi", "Any (both)"].index(
                st.session_state.source_filter
            ),
        )
        st.session_state.source_filter = source_filter

        st.divider()

        # Index stats
        for src_name in SOURCES:
            cache_file = SOURCES[src_name]["cache_file"]
            if cache_file.exists():
                try:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    count = data.get("total_count", 0)
                    updated = data.get("last_updated", "Never")
                    if updated and updated != "Never":
                        try:
                            dt = datetime.fromisoformat(updated)
                            updated = dt.strftime("%d %b %Y %H:%M")
                        except (ValueError, TypeError):
                            pass
                    st.metric(f"{src_name}", f"{count} recipes", help=f"Last updated: {updated}")
                except (json.JSONDecodeError, KeyError):
                    st.metric(src_name, "0 recipes")
            else:
                st.metric(src_name, "Not indexed yet")

        st.divider()

        # Refresh button
        sources_to_refresh = (
            list(SOURCES.keys()) if source_filter == "Any (both)" else [source_filter]
        )
        if st.button("🔄 Refresh Index", use_container_width=True):
            total_new = 0
            for src_name in sources_to_refresh:
                with st.spinner(f"Scraping {src_name}..."):
                    result = scrape_source(src_name)
                    save_index(src_name, result)
                    new_count = result["total_count"]
                    total_new += new_count
                    if result.get("errors"):
                        st.warning(f"{src_name}: {len(result['errors'])} pages had errors")
            st.success(f"Index updated: {total_new} recipes found")
            st.rerun()

        st.divider()

        # Random recipe button
        combined = get_combined_index(source_filter)
        random_disabled = len(combined) == 0

        if st.button(
            "🎲 Random Recipe",
            use_container_width=True,
            type="primary",
            disabled=random_disabled,
            help="Refresh the index first if no recipes appear" if random_disabled else None,
        ):
            st.session_state.current_recipe = random.choice(combined)
            st.session_state.save_form_open = False
            st.rerun()

        if random_disabled:
            st.caption("No recipes in index — click Refresh Index first.")

        # View saved count
        saved_urls = load_saved_urls()
        if saved_urls:
            st.divider()
            st.caption(f"✓ {len(saved_urls)} recipes saved to Bennett Cookbook")


# ─── UI: Recipe card ────────────────────────────────────────────────────────

def render_recipe_card(recipe: dict, saved_urls: set[str]) -> None:
    src_name = recipe.get("_source", recipe.get("source_name", ""))

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        st.subheader(recipe.get("title", "Untitled"))

        if src_name:
            st.caption(f"From **{src_name}**")

        description = recipe.get("description")
        if description:
            st.write(description)

        url = recipe.get("url")
        if url:
            st.markdown(f"[View original recipe →]({url})")

        meta_parts = []
        if recipe.get("category"):
            meta_parts.append(f"**Category:** {recipe['category']}")
        if meta_parts:
            st.caption("  ·  ".join(meta_parts))

    with col2:
        image_url = recipe.get("image_url")
        if image_url and image_url.startswith("http"):
            try:
                st.image(image_url, use_container_width=True)
            except Exception:
                pass

    if recipe.get("url") in saved_urls:
        st.success("✓ Already saved to Bennett Cookbook")
        return

    st.divider()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("💾 Save to Bennett Cookbook", type="primary", use_container_width=True):
            st.session_state.save_form_open = True
    with col_b:
        if st.button("⏭ Skip / Next Random", use_container_width=True):
            combined = get_combined_index(st.session_state.source_filter)
            if combined:
                st.session_state.current_recipe = random.choice(combined)
                st.session_state.save_form_open = False
            st.rerun()
    with col_c:
        if recipe.get("url"):
            st.link_button("↗ Open Original", recipe["url"], use_container_width=True)


# ─── UI: Save form ──────────────────────────────────────────────────────────

def render_save_form(recipe: dict) -> None:
    src_name = recipe.get("_source", recipe.get("source_name", "External"))

    st.divider()
    st.subheader("Save to Bennett Cookbook")
    st.caption(
        "Review and edit the details below before saving. "
        "Only the title, source link, and your notes will be saved by default — "
        "no recipe content is copied."
    )

    with st.form("save_recipe_form"):
        editable_title = st.text_input(
            "Recipe title (editable)",
            value=recipe.get("title", ""),
        )

        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category", CATEGORIES)
            cuisine = st.selectbox("Cuisine", CUISINES)
        with col2:
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Advanced"])
            serves = st.text_input("Serves", value="4")

        tags_input = st.text_input(
            "Tags (comma separated)",
            placeholder="e.g. chicken, weeknight, impressive",
        )

        source_notes = st.text_area(
            "Nathan's notes",
            height=120,
            placeholder="Why are you saving this? What looks interesting? Any thoughts on tweaks?",
        )

        st.subheader("Save type")

        save_type_label = st.radio(
            "How do you want to save this?",
            options=[
                "reference_only",
                "save_as_is",
                "adapt",
            ],
            format_func=lambda x: {
                "reference_only": "📌 Reference only — save the link and my notes, nothing else",
                "save_as_is": "🔗 Save as external reference — full metadata, link-based entry",
                "adapt": "✍️ Adapt into a Bennett recipe — I'll rewrite it in my own words",
            }[x],
        )

        planned_ingredients = None
        planned_method = None

        if save_type_label == "adapt":
            st.warning(
                "**Adaptation note:** This will save a Bennett adaptation. "
                "Do not copy the original recipe text. "
                "Rewrite the ingredients and method in your own words and include your own changes.",
                icon="⚠️",
            )
            planned_ingredients = st.text_area(
                "Planned ingredient changes",
                height=100,
                placeholder="What will you change or substitute?",
            )
            planned_method = st.text_area(
                "Planned method changes",
                height=100,
                placeholder="What will you do differently?",
            )

        st.subheader("Flags")
        col3, col4 = st.columns(2)
        with col3:
            try_soon = st.checkbox("Try soon")
            family_dinner = st.checkbox("Family dinner candidate")
        with col4:
            entertaining = st.checkbox("Entertaining candidate")
            kid_friendly = st.checkbox("Kid friendly")

        st.divider()

        # Preview
        with st.expander("Preview save record", expanded=False):
            st.json({
                "recipe_name": editable_title or recipe.get("title"),
                "source": src_name,
                "source_url": recipe.get("url"),
                "save_type": save_type_label,
                "tags": [t.strip() for t in tags_input.split(",") if t.strip()]
                + ["external-source", SOURCES.get(src_name, {}).get("tag", "external")],
                "nathan_notes": source_notes or None,
                "try_soon": try_soon,
                "ingredients": "[ not copied — copyright safe ]",
                "method": "[ not copied — copyright safe ]",
            })

        submitted = st.form_submit_button("✅ Save Recipe", type="primary")

        if submitted:
            if not editable_title.strip():
                st.error("Please enter a recipe title.")
                return

            url = recipe.get("url")
            saved_urls = load_saved_urls()
            if url and url in saved_urls:
                st.warning("This recipe is already saved.")
                return

            try:
                save_external_recipe(
                    recipe=recipe,
                    editable_title=editable_title.strip(),
                    category=category,
                    cuisine=cuisine,
                    difficulty=difficulty,
                    serves=serves,
                    tags_input=tags_input,
                    source_notes=source_notes,
                    save_type=save_type_label,
                    try_soon=try_soon,
                    family_dinner=family_dinner,
                    entertaining=entertaining,
                    kid_friendly=kid_friendly,
                    planned_ingredients=planned_ingredients,
                    planned_method=planned_method,
                )
                st.session_state.save_form_open = False
                st.success(f"✓ Saved: **{editable_title}** to Bennett Cookbook")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")

    # Cancel button (outside form)
    if st.button("Cancel"):
        st.session_state.save_form_open = False
        st.rerun()


# ─── Main app ────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Bennett Cookbook — Recipe Finder",
        page_icon="🍳",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()
    render_sidebar()

    # Main content
    st.title("🍳 Bennett Cookbook — Recipe Finder")
    st.caption(
        "Discover recipes from RecipeTin Eats and Ottolenghi. "
        "Save them as references or plan your own adaptation — no copyrighted content is copied."
    )

    saved_urls = load_saved_urls()

    if st.session_state.current_recipe is None:
        st.info(
            "Click **Random Recipe** in the sidebar to discover a recipe, "
            "or **Refresh Index** first if you haven't built the index yet."
        )
        return

    recipe = st.session_state.current_recipe
    render_recipe_card(recipe, saved_urls)

    if st.session_state.save_form_open and recipe.get("url") not in saved_urls:
        render_save_form(recipe)


if __name__ == "__main__":
    main()
