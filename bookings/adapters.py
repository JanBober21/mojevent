from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class GoogleRedirectAdapter(DefaultSocialAccountAdapter):
    """After social login, redirect new users to account settings."""

    def get_login_redirect_url(self, request):
        from bookings.models import UserProfile

        user = request.user
        if user.is_authenticated:
            profile, created = UserProfile.objects.get_or_create(user=user)
            # If profile was just created (new Google user) or no name filled
            if created or not user.first_name:
                return "/konto/?new=1"
        return "/"
