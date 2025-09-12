from django import forms

from .models import ImagesAvatar, Profile


class ImagesAvatarForm(forms.ModelForm):
    """
    Пользовательская форма для загрузки аватарок через админку
    """

    class Meta:
        model = ImagesAvatar
        fields = "__all__"

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Если есть профиль в форме, устанавливаем связь
            if "profile" in self.cleaned_data and self.cleaned_data["profile"]:
                instance.profile = self.cleaned_data["profile"]
                instance.save()
        return instance


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = "__all__"

    phone = forms.CharField(widget=forms.TextInput(attrs={"size": "15"}))
