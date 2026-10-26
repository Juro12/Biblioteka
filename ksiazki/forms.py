from django import forms

from .models import Czytelnik, Ksiazka, Wypozyczenie


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class KsiazkaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Ksiazka
        fields = ['tytul', 'autor', 'isbn', 'rok_wydania', 'gatunek', 'liczba_egzemplarzy']

    def clean_isbn(self):
        # Puste ISBN zapisujemy jako NULL, żeby nie łamać unikalności
        return self.cleaned_data['isbn'] or None


class CzytelnikForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Czytelnik
        fields = ['imie', 'nazwisko', 'email', 'numer_karty']


class WypozyczenieForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Wypozyczenie
        fields = ['ksiazka', 'czytelnik']

    def clean_ksiazka(self):
        ksiazka = self.cleaned_data['ksiazka']
        aktywne = Wypozyczenie.objects.filter(
            ksiazka=ksiazka,
            data_zwrotu__isnull=True,
        ).count()
        if aktywne >= ksiazka.liczba_egzemplarzy:
            raise forms.ValidationError('Brak wolnych egzemplarzy tej książki.')
        return ksiazka
