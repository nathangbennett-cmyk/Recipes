# The Bennett Cookbook

A personal family recipe management system for the Bennett household.

---

## What's in here

```
/
  data/
    recipes.json                        ← source of truth for all recipes
    full_meals.json                     ← multi-course meal combinations
    tags.json                           ← controlled tag vocabulary
    saved_external.json                 ← recipes saved via the Streamlit app
    recipetineats_recipe_index.json     ← RecipeTin Eats discovery cache
    ottolenghi_recipe_index.json        ← Ottolenghi discovery cache
  src/
    models.py                           ← Pydantic v2 data models
    build_database.py                   ← generates CSV + XLSX exports
    build_cookbook.py                   ← generates Markdown + HTML + PDF cookbook
    random_recipe_tin_eats.py           ← Streamlit recipe discovery app
  templates/
    cookbook.html.j2                    ← Jinja2 HTML cookbook shell
    recipe_card.html.j2                 ← recipe card partial
  cookbook/                             ← generated outputs
    the_bennett_cookbook.md
    the_bennett_cookbook.html
    the_bennett_cookbook.pdf
  exports/                              ← generated database exports
    the_bennett_cookbook_recipe_database.xlsx
    the_bennett_cookbook_recipe_database.csv
    recipes_export.json
  images/
    source/                             ← place actual food photos here
    generated/                          ← place AI-generated images here
```

---

## Setup

```bash
pip install -r requirements.txt
```

### PDF generation (optional)

WeasyPrint requires system libraries. On Ubuntu/Debian:

```bash
apt install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
```

Without these, the PDF step is gracefully skipped and the HTML version is produced instead.

---

## Usage

### Build the recipe database (CSV + XLSX + JSON)

```bash
python -m src.build_database
```

Outputs:
- `exports/the_bennett_cookbook_recipe_database.xlsx` — 8 tabs: All Recipes, Personal, External, Adapted, Weeknight Wins, Entertaining, Full Meals, Tag Index
- `exports/the_bennett_cookbook_recipe_database.csv`
- `exports/recipes_export.json`

### Build the cookbook (Markdown + HTML + PDF)

```bash
python -m src.build_cookbook
```

Outputs:
- `cookbook/the_bennett_cookbook.md` — full manuscript
- `cookbook/the_bennett_cookbook.html` — styled, print-ready HTML
- `cookbook/the_bennett_cookbook.pdf` — if WeasyPrint is installed

### Run the recipe discovery app

```bash
streamlit run src/random_recipe_tin_eats.py
```

Opens at `http://localhost:8501`

---

## Adding a new personal recipe

1. Open `data/recipes.json`
2. Add a new object to the array using the schema below
3. Assign a unique `recipe_id` (lowercase slug, e.g. `my-new-recipe`)
4. Rebuild:

```bash
python -m src.build_database && python -m src.build_cookbook
```

### Recipe intake template

```json
{
  "recipe_id": "your-recipe-slug",
  "recipe_name": "Recipe Name",
  "record_type": "personal_recipe",
  "category": "Pasta",
  "cuisine": "Italian",
  "difficulty": "Easy",
  "prep_time_minutes": 10,
  "cook_time_minutes": 20,
  "serves": "4",
  "kid_friendly": false,
  "nathan_rating": null,
  "weeknight_score": 7,
  "entertaining_score": 5,
  "ingredients": [
    "500g pasta",
    "..."
  ],
  "method": [
    "Step 1.",
    "Step 2."
  ],
  "nathan_tweaks": "What makes this special.",
  "substitutions": "Approved swaps.",
  "pairings": ["Side dish", "Wine"],
  "full_meal_id": null,
  "tags": ["pasta", "weeknight"],
  "source_notes": "Bennett family original",
  "image_prompt": "Premium modern cookbook photograph of [dish], ...",
  "image_file": null,
  "family_dinner_candidate": true,
  "entertaining_candidate": false,
  "try_soon": false,
  "copyright_status": "personal",
  "adaptation_status": "not_applicable"
}
```

---

## Saving external recipes

Use the Streamlit app (`streamlit run src/random_recipe_tin_eats.py`).

The app handles:
- Copyright-safe saving (no recipe content copied by default)
- Duplicate URL detection
- Edit-before-save for all metadata
- Three save types: reference only, external reference, or Bennett adaptation

---

## Converting a saved external recipe into a Bennett adaptation

1. Find the saved record in `data/saved_external.json`
2. Add a new entry to `data/recipes.json` with:
   - `record_type: "adapted_bennett_recipe"`
   - `adapted_from_recipe_id: "<original_recipe_id>"`
   - Your own rewritten `ingredients` and `method`
   - `nathan_tweaks` with your modifications
3. Rebuild:

```bash
python -m src.build_database && python -m src.build_cookbook
```

---

## Recipe fields reference

See `src/models.py` for the full Pydantic v2 model with all field definitions.

Key fields:

| Field | Type | Description |
|---|---|---|
| `recipe_id` | str | Unique slug |
| `recipe_name` | str | Human-readable title |
| `record_type` | enum | `personal_recipe` / `external_saved_reference` / `adapted_bennett_recipe` |
| `category` | str | Pasta, Seafood, Vegetarian, etc. |
| `difficulty` | enum | Easy / Medium / Advanced |
| `weeknight_score` | int 1-10 | Higher = more weeknight-suitable |
| `entertaining_score` | int 1-10 | Higher = better for guests |
| `tags` | list[str] | Searchable tags |
| `full_meal_id` | str | Links to a full meal build |
| `nathan_tweaks` | str | Personal preferences and modifications |
| `copyright_status` | str | `personal` / `reference_only` / `adapted` |

---

## Searchable tags

Use these consistent tags across all recipes:

`weeknight` · `kid-friendly` · `family-favourite` · `impressive` · `entertaining` ·
`vegetarian` · `seafood` · `pasta` · `hidden-veg` · `brunch` · `side` · `sauce` ·
`full-meal` · `healthy-ish` · `comfort-food` · `date-night` · `quick` · `make-ahead` ·
`pantry` · `recipetineats` · `ottolenghi` · `external-source`

---

## Design system

The cookbook uses a warm, modern family aesthetic:

| Element | Value |
|---|---|
| Background | `#FAF8F5` (warm off-white) |
| Text | `#2C2C2C` (charcoal) |
| Accent | `#C0392B` (tomato red) |
| Secondary | `#7D9E4A` (olive green) |
| Section bg | `#F0EBE3` (soft beige) |
| Headings | Georgia serif |
| Body | System sans-serif |

---

## Recipe sources

- RecipeTin Eats: https://www.recipetineats.com/recipes/
- Ottolenghi: https://ottolenghi.co.uk/pages/recipes
