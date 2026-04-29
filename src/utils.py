import re
from urllib.parse import quote_plus

def clean_text(text):
    """Standardizes user input to help the AI."""
    if not text:
        return ""
    text = text.lower().strip()
    return re.sub(r"[^a-zA-Z0-9\s]", " ", text)

def generate_maps_link(name, location):
    """Creates a Google Maps search URL."""
    query = quote_plus(f"{name} {location}")
    return f"https://www.google.com/maps/search/{query}"

def get_city_tag(location):
    """Extracts city name for UI labeling."""
    loc = (location or "").lower()
    if any(w in loc for w in ["mumbai", "nagpada", "fort", "dadar", "andheri"]):
        return "Mumbai"
    if any(w in loc for w in ["bengaluru", "bangalore", "bbmp", "majestic"]):
        return "Bengaluru"
    return "City Facility"


def normalize_category(category):
    """Maps noisy dataset labels to resource categories used by the UI."""
    text = clean_text(category)
    if any(word in text for word in ["salon", "saloon", "barber", "beauty", "parlour", "parlor"]):
        return "Salons"
    if any(word in text for word in ["mechanic", "garage", "repair", "puncture", "vehicle"]):
        return "Mechanics"
    if any(word in text for word in ["clothes", "clothing", "garment", "apparel", "tailor"]):
        return "Clothes"
    if any(word in text for word in ["sweet", "mithai", "sweets", "bakery"]):
        return "Sweet Shops"
    if any(word in text for word in ["stationary", "stationery", "book", "notebook", "xerox", "print"]):
        return "Stationery"
    if any(word in text for word in ["grocery", "groceries", "kirana", "ration", "general store"]):
        return "Groceries"
    if any(word in text for word in ["doctor", "physician", "pediatrician", "cardiologist"]):
        return "Doctors"
    hospital_labels = [
        "hospital",
        "medical",
        "maternity",
        "clinic",
        "private",
        "government",
        "govt",
        "municipal",
        "trust",
        "bmc",
        "defence",
        "bbmp",
    ]
    if any(word in text for word in hospital_labels):
        return "Hospital"
    if any(word in text for word in ["food", "meal", "canteen", "ration"]):
        return "Free Food"
    if any(word in text for word in ["ngo", "foundation", "charity", "support"]):
        return "NGO"
    if any(word in text for word in ["mall", "shopping"]):
        return "Mall"
    if any(word in text for word in ["shop", "market", "store"]):
        return "Shops"
    if any(word in text for word in ["bus", "metro", "rail", "transport", "station"]):
        return "Transportation"
    return (category or "Community Resource").strip()
