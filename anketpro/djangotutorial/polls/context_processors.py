from .models import UserProfile


def theme_context(request):
    """Add the current theme to the template context for all pages."""
    theme = 'beyaz'
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile:
            theme = profile.theme
    return {'current_theme': theme}
