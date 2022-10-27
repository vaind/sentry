from typing import Any

from django import forms

from sentry.rules.actions.integrations.base import INTEGRATION_KEY


class IntegrationNotifyServiceForm(forms.Form):
    integration = forms.ChoiceField(choices=(), widget=forms.Select())

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        integrations = [(i.id, i.name) for i in kwargs.pop("integrations")]
        super().__init__(*args, **kwargs)
        if integrations:
            self.fields[INTEGRATION_KEY].initial = integrations[0][0]

        # https://github.com/typeddjango/django-stubs/issues/1208
        self.fields[INTEGRATION_KEY].choices = integrations  # type: ignore[attr-defined]
        self.fields[INTEGRATION_KEY].widget.choices = self.fields[INTEGRATION_KEY].choices  # type: ignore[attr-defined]
