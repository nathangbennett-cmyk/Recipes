from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    ADVANCED = "Advanced"


class RecordType(str, Enum):
    PERSONAL = "personal_recipe"
    EXTERNAL = "external_saved_reference"
    ADAPTED = "adapted_bennett_recipe"


class SaveType(str, Enum):
    REFERENCE_ONLY = "reference_only"
    SAVE_AS_IS = "save_as_is"
    ADAPT = "adapt"


class AdaptationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    NOT_APPLICABLE = "not_applicable"


class Recipe(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # Identity
    recipe_id: str
    recipe_name: str
    record_type: RecordType = RecordType.PERSONAL

    # Classification
    category: str = ""
    cuisine: str = ""
    difficulty: DifficultyLevel = DifficultyLevel.EASY
    tags: list[str] = Field(default_factory=list)

    # Timing and servings
    prep_time_minutes: int = 0
    cook_time_minutes: int = 0
    total_time_minutes: int = 0
    serves: str = "4"

    # Family metadata
    kid_friendly: bool = False
    leah_rating: Optional[float] = None
    nina_rating: Optional[float] = None
    nathan_rating: Optional[float] = None

    # Scores
    entertaining_score: Optional[int] = None
    weeknight_score: Optional[int] = None

    # Content
    ingredients: list[str] = Field(default_factory=list)
    method: list[str] = Field(default_factory=list)
    nathan_tweaks: Optional[str] = None
    substitutions: Optional[str] = None
    pairings: list[str] = Field(default_factory=list)

    # Relationships
    full_meal_id: Optional[str] = None
    adapted_from_recipe_id: Optional[str] = None

    # Source (external recipes)
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_author: Optional[str] = None
    source_image_url: Optional[str] = None
    source_notes: Optional[str] = None
    date_saved: Optional[str] = None

    # Images
    image_prompt: Optional[str] = None
    image_file: Optional[str] = None
    image_url: Optional[str] = None
    emoji: str = "🍽️"

    # Flags
    try_soon: bool = False
    family_dinner_candidate: bool = False
    entertaining_candidate: bool = False

    # Copyright / adaptation
    copyright_status: Optional[str] = None
    editable_title: Optional[str] = None
    save_type: Optional[SaveType] = None
    nathan_modified_before_save: bool = False
    planned_ingredient_changes: Optional[str] = None
    planned_method_changes: Optional[str] = None
    approved_adaptation_text: Optional[str] = None
    adaptation_status: Optional[AdaptationStatus] = None

    @model_validator(mode="after")
    def compute_total_time(self) -> "Recipe":
        if self.total_time_minutes == 0 and (self.prep_time_minutes or self.cook_time_minutes):
            self.total_time_minutes = self.prep_time_minutes + self.cook_time_minutes
        return self


class FullMeal(BaseModel):
    full_meal_id: str
    meal_name: str
    description: Optional[str] = None
    recipe_ids: list[str] = Field(default_factory=list)
    serves: str = "4"
    total_time_estimate: Optional[str] = None
    occasions: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class IndexedRecipe(BaseModel):
    title: str
    url: str
    source_name: str = ""
    category: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    date_indexed: str = ""


class RecipeSourceIndex(BaseModel):
    source_name: str
    last_updated: Optional[str] = None
    total_count: int = 0
    recipes: list[IndexedRecipe] = Field(default_factory=list)


class TagsVocabulary(BaseModel):
    categories: list[str] = Field(default_factory=list)
    cuisines: list[str] = Field(default_factory=list)
    dietary: list[str] = Field(default_factory=list)
    occasion: list[str] = Field(default_factory=list)
    method: list[str] = Field(default_factory=list)
    custom: list[str] = Field(default_factory=list)
