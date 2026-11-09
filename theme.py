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

# Color Tokens - ChatGPT Aesthetic
DARK_THEME = {
    "bg": "#212121",                 # ChatGPT signature dark canvas
    "surface": "#171717",            # ChatGPT sidebar charcoal
    "surface_variant": "#2F2F2F",    # ChatGPT pill / user bubble
    "surface_active": "#343541",     # Active session highlight
    "primary": "#10A37F",            # ChatGPT iconic emerald
    "primary_gradient_start": "#10A37F",
    "primary_gradient_end": "#0E8C6D",
    "user_bubble": "#2F2F2F",        # ChatGPT user bubble
    "assistant_bubble": "#212121",   # Seamless with canvas
    "user_text": "#ECECEC",
    "text_primary": "#ECECEC",
    "text_secondary": "#B4B4B4",
    "text_muted": "#7E7E7E",
    "border": "#383838",
    "input_bg": "#2F2F2F",           # ChatGPT floating input pill
    "code_bg": "#171717",
    "badge_bg": "#2A2A2A",
    "badge_text": "#ECECEC",
    "accent": "#10A37F",
}

LIGHT_THEME = {
    "bg": "#FFFFFF",                 # Clean white canvas
    "surface": "#F9F9F9",            # Light sidebar
    "surface_variant": "#F4F4F4",    # Light user bubble / pill
    "surface_active": "#EBEBEB",
    "primary": "#10A37F",
    "primary_gradient_start": "#10A37F",
    "primary_gradient_end": "#0E8C6D",
    "user_bubble": "#F4F4F4",
    "assistant_bubble": "#FFFFFF",
    "user_text": "#0D0D0D",
    "text_primary": "#0D0D0D",
    "text_secondary": "#5D5D5D",
    "text_muted": "#8E8E8E",
    "border": "#E5E5E5",
    "input_bg": "#F4F4F4",
    "code_bg": "#F8F8F8",
    "badge_bg": "#F4F4F4",
    "badge_text": "#0D0D0D",
    "accent": "#10A37F",
}


def get_theme_colors(is_dark: bool) -> dict:
    return DARK_THEME if is_dark else LIGHT_THEME
