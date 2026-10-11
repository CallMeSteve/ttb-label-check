"""Rule data. Every entry carries its CFR cite."""

# 27 CFR 16.21, as one continuous paragraph (TTB guidance: continuous paragraph).
WARNING_TEXT = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink "
    "alcoholic beverages during pregnancy because of the risk of birth defects. "
    "(2) Consumption of alcoholic beverages impairs your ability to drive a car or "
    "operate machinery, and may cause health problems."
)
WARNING_RULE = "27 CFR 16.21"
WARNING_CAPS_RULE = "27 CFR 16.22(a)(2)"

# 27 CFR 5.203(a), standards of fill for distilled spirits, in mL.
SPIRITS_FILLS_ML = (
    3750, 3000, 2000, 1800, 1750, 1500, 1000, 945, 900, 750, 720, 710, 700,
    570, 500, 475, 375, 355, 350, 331, 250, 200, 187, 100, 50,
)
SPIRITS_FILL_RULE = "27 CFR 5.203(a)"

# 27 CFR 4.72(a), standards of fill for wine, in mL. Above 3 L: whole liters only.
WINE_FILLS_ML = (
    3000, 2250, 1800, 1500, 1000, 750, 720, 700, 620, 600, 568, 550, 500, 473,
    375, 360, 355, 330, 300, 250, 200, 187, 180, 100, 50,
)
WINE_FILL_RULE = "27 CFR 4.72(a)"

# mL per unit.
UNIT_ML = {
    "ml": 1.0, "cl": 10.0, "l": 1000.0,
    "floz": 29.5735, "pint": 473.176, "quart": 946.353, "gallon": 3785.41,
}
METRIC_UNITS = {"ml", "cl", "l"}

# Minimum alcohol by volume for a class designation. 27 CFR 5.142 to 5.151.
CLASS_MINIMUMS = {
    "WHISKY": 40.0, "BOURBON": 40.0, "RYE": 40.0, "VODKA": 40.0, "GIN": 40.0,
    "RUM": 40.0, "BRANDY": 40.0, "TEQUILA": 40.0, "MEZCAL": 40.0, "AGAVE": 40.0,
}
FLAVORED_MINIMUM = 30.0
CLASS_MINIMUM_RULE = "27 CFR 5.142 to 5.151"

# Words that change the legal meaning of a class designation.
SIGNIFICANT_WORDS = ("STRAIGHT", "BLENDED", "BOTTLED IN BOND", "LIGHT", "FLAVORED", "IMITATION")

# Class keywords the label scan looks for when no class was typed (most specific first).
SPIRITS_CLASSES = (
    "BOURBON", "RYE", "WHISKY", "VODKA", "GIN", "RUM", "BRANDY", "TEQUILA", "MEZCAL",
    "AGAVE", "LIQUEUR", "CORDIAL",
)
WINE_CLASSES = ("TABLE WINE", "LIGHT WINE", "SPARKLING WINE", "DESSERT WINE", "WINE", "SAKE")
MALT_CLASSES = ("MALT BEVERAGE", "MALT LIQUOR", "BEER", "ALE", "LAGER", "STOUT", "PORTER")

NAME_ADDRESS_PHRASES = (
    "distilled and bottled by", "brewed and bottled by", "bottled by", "distilled by",
    "produced by", "blended by", "made by", "prepared by", "manufactured by", "canned by",
    "packed by", "filled by", "brewed by", "imported by", "vinted by", "cellared by",
)
NAME_ADDRESS_RULES = {
    "spirits": "27 CFR 5.63(b)(1)", "wine": "27 CFR 4.32(b)(1)", "malt": "27 CFR 7.63(a)(4)",
}

BRAND_CASE_RULES = {
    "spirits": "27 CFR 5.52(d)",
    "malt": "27 CFR 7.52(d)",
    "wine": "TTB Form 5100.31, allowable revision 3.b",
}
