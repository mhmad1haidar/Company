from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

class StyledAuthenticationForm(AuthenticationForm):
    """Enhanced authentication form with security features and better UX."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Enhanced field attributes for better UX and security
        self.fields["username"].widget.attrs.update({
            "class": "form-control form-control-lg",
            "autocomplete": "username",
            "placeholder": "Enter your username",
            "required": True,
            "autocapitalize": "none",
            "spellcheck": "false",
        })
        
        self.fields["password"].widget.attrs.update({
            "class": "form-control form-control-lg",
            "autocomplete": "current-password",
            "placeholder": "Enter your password",
            "required": True,
        })

    def confirm_login_allowed(self, user):
        """Enhanced login validation with detailed error messages."""
        if not user.is_active:
            raise ValidationError(
                "This account is inactive. Please contact an administrator.",
                code='inactive'
            )
        
        # Additional security checks can be added here
        # For example: account lockout, password expiry, etc.
        
        return super().confirm_login_allowed(user)
