"""
UI Theme definitions, color tokens, and responsive layout constants.
"""

# Responsive breakpoint in logical pixels
MOBILE_BREAKPOINT = 768

# Desktop / Laptop default window dimensions
DESKTOP_WIDTH = 1080
DESKTOP_HEIGHT = 760
MIN_WINDOW_WIDTH = 360
MIN_WINDOW_HEIGHT = 520

# Color Tokens - Clean Monochromatic Black & White ChatGPT Aesthetic
DARK_THEME = {
    "bg": "#212121",                 # Dark canvas
    "surface": "#171717",            # Charcoal sidebar
    "surface_variant": "#2F2F2F",    # Pill / user bubble / cards
    "surface_active": "#383838",     # Highlighted item
    "primary": "#FFFFFF",            # Pure White
    "primary_gradient_start": "#FFFFFF",
    "primary_gradient_end": "#E5E5E5",
    "user_bubble": "#2F2F2F",        # Charcoal user bubble
    "assistant_bubble": "#212121",   # Canvas matching
    "user_text": "#FFFFFF",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B4B4B4",
    "text_muted": "#7E7E7E",
    "border": "#383838",
    "input_bg": "#2F2F2F",           # Floating input pill
    "code_bg": "#171717",
    "badge_bg": "#2F2F2F",
    "badge_text": "#FFFFFF",
    "accent": "#FFFFFF",
}

LIGHT_THEME = {
    "bg": "#FFFFFF",                 # Clean white canvas
    "surface": "#F9F9F9",            # Light sidebar
    "surface_variant": "#F4F4F4",    # Light user bubble / pill
    "surface_active": "#EBEBEB",
    "primary": "#000000",            # Pure Black
    "primary_gradient_start": "#000000",
    "primary_gradient_end": "#222222",
    "user_bubble": "#F4F4F4",
    "assistant_bubble": "#FFFFFF",
    "user_text": "#000000",
    "text_primary": "#000000",
    "text_secondary": "#5D5D5D",
    "text_muted": "#8E8E8E",
    "border": "#E5E5E5",
    "input_bg": "#F4F4F4",
    "code_bg": "#F8F8F8",
    "badge_bg": "#F4F4F4",
    "badge_text": "#000000",
    "accent": "#000000",
}


def get_theme_colors(is_dark: bool) -> dict:
    return DARK_THEME if is_dark else LIGHT_THEME
