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

# Color Tokens
DARK_THEME = {
    "bg": "#0B0F19",                 # Deep void slate
    "surface": "#151C2C",            # Dark elevated card
    "surface_variant": "#1E293B",    # Subtle border/input surface
    "surface_active": "#2D3748",     # Highlighted item
    "primary": "#6366F1",            # Electric Indigo
    "primary_gradient_start": "#6366F1",
    "primary_gradient_end": "#8B5CF6",
    "user_bubble": "#4338CA",        # Deep Indigo for user
    "assistant_bubble": "#151C2C",   # Clean slate for assistant
    "user_text": "#FFFFFF",
    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "border": "#243046",
    "input_bg": "#121826",
    "code_bg": "#0D1117",
    "badge_bg": "#1E1B4B",
    "badge_text": "#A5B4FC",
    "accent": "#8B5CF6",
}

LIGHT_THEME = {
    "bg": "#F8FAFC",                 # Ultra light crisp slate
    "surface": "#FFFFFF",            # Clean white
    "surface_variant": "#F1F5F9",    # Light slate
    "surface_active": "#E2E8F0",
    "primary": "#4F46E5",
    "primary_gradient_start": "#4F46E5",
    "primary_gradient_end": "#7C3AED",
    "user_bubble": "#4F46E5",
    "assistant_bubble": "#FFFFFF",
    "user_text": "#FFFFFF",
    "text_primary": "#0F172A",
    "text_secondary": "#475569",
    "text_muted": "#94A3B8",
    "border": "#E2E8F0",
    "input_bg": "#FFFFFF",
    "code_bg": "#F1F5F9",
    "badge_bg": "#EEF2FF",
    "badge_text": "#4F46E5",
    "accent": "#7C3AED",
}


def get_theme_colors(is_dark: bool) -> dict:
    return DARK_THEME if is_dark else LIGHT_THEME
