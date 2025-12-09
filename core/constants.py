"""
Shared constants across the application
"""

ITEM_TYPES = (
    ("C", "Case"),
    ("W", "Weight")
)

ITEM_TYPE_CHOICES = (
    ("0", "Select an item type..."),
    ("C", "Case"),
    ("W", "Weight")
)

def get_item_type_display(item_type):
    """Get human-readable item type"""
    return "Weight" if item_type == "W" else "Case"