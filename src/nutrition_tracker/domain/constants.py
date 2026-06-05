CORE_NUTRITION_METRICS = ("kcal", "protein_g", "fat_g", "carbs_g", "fiber_g")
REQUIRED_NUTRITION_METRICS = ("kcal", "protein_g", "fat_g", "carbs_g")
EXTENDED_NUTRITION_METRICS = (
    "fiber_g",
    "saturated_fat_g",
    "sugar_g",
    "added_sugar_g",
    "sodium_mg",
    "cholesterol_mg",
    "trans_fat_g",
    "polyunsaturated_fat_g",
    "monounsaturated_fat_g",
    "caffeine_mg",
    "alcohol_g",
    "vitamin_d_ug",
    "calcium_mg",
)
ALL_NUTRITION_METRICS = tuple(
    dict.fromkeys((*REQUIRED_NUTRITION_METRICS, *EXTENDED_NUTRITION_METRICS))
)
GOAL_METRICS = CORE_NUTRITION_METRICS

ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}
