from django.contrib import messages
from django.db.models import Count, ExpressionWrapper, F, IntegerField, Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CzytelnikForm, KsiazkaForm, WypozyczenieForm
from .models import Czytelnik, Ksiazka, Wypozyczenie


def lista(request):
    ksiazki = Ksiazka.objects.annotate(
        aktywne_wypozyczenia=Count(
            'wypozyczenia',
            filter=Q(wypozyczenia__data_zwrotu__isnull=True),
        ),
    ).annotate(
        dostepne=ExpressionWrapper(
            F('liczba_egzemplarzy') - F('aktywne_wypozyczenia'),
            output_field=IntegerField(),
        ),
    )
    q = request.GET.get('q', '').strip()
    if q:
        ksiazki = ksiazki.filter(Q(tytul__icontains=q) | Q(autor__icontains=q) | Q(isbn__icontains=q))

    sort_fields = {'tytul': 'tytul', 'autor': 'autor', 'rok': 'rok_wydania'}
    sort = request.GET.get('sort', 'tytul')
    if sort not in sort_fields:
        sort = 'tytul'
    direction = request.GET.get('direction', 'asc')
    if direction not in {'asc', 'desc'}:
        direction = 'asc'
    sort_direction = '-' if direction == 'desc' else ''
    ksiazki = ksiazki.order_by(f'{sort_direction}{sort_fields[sort]}', 'pk')
    ksiazki_page = Paginator(ksiazki, 10).get_page(request.GET.get('page'))
    return render(request, 'ksiazki/lista.html', {
        'ksiazki': ksiazki_page,
        'page_obj': ksiazki_page,
        'paginator': ksiazki_page.paginator,
        'q': q,
        'sort': sort,
        'direction': direction,
        'next_direction': 'desc' if direction == 'asc' else 'asc',
    })


def dodaj(request):
    form = KsiazkaForm(request.POST or None)
    if form.is_valid():
        ksiazka = form.save()
        messages.success(request, f'Dodano książkę „{ksiazka.tytul}”.')
        return redirect('lista')
    return render(request, 'ksiazki/formularz.html', {
        'form': form,
        'naglowek': 'Dodaj książkę',
        'anuluj_url': 'lista',
    })


def edytuj(request, pk):
    ksiazka = get_object_or_404(Ksiazka, pk=pk)
    form = KsiazkaForm(request.POST or None, instance=ksiazka)
    if form.is_valid():
        form.save()
        messages.success(request, f'Zapisano zmiany w „{ksiazka.tytul}”.')
        return redirect('lista')
    return render(request, 'ksiazki/formularz.html', {
        'form': form,
        'naglowek': 'Edytuj książkę',
        'anuluj_url': 'lista',
    })


def usun(request, pk):
    ksiazka = get_object_or_404(Ksiazka, pk=pk)
    if request.method == 'POST':
        ksiazka.delete()
        messages.success(request, f'Usunięto książkę „{ksiazka.tytul}”.')
        return redirect('lista')
    return render(request, 'ksiazki/usun.html', {'ksiazka': ksiazka})


def lista_czytelnikow(request):
    czytelnicy = Czytelnik.objects.all()
    return render(request, 'ksiazki/czytelnicy_lista.html', {'czytelnicy': czytelnicy})


def szczegoly_czytelnika(request, pk):
    czytelnik = get_object_or_404(Czytelnik, pk=pk)
    wypozyczenia = czytelnik.wypozyczenia.select_related('ksiazka').order_by(
        '-data_wypozyczenia',
        '-pk',
    )
    return render(request, 'ksiazki/czytelnik_szczegoly.html', {
        'czytelnik': czytelnik,
        'wypozyczenia': wypozyczenia,
    })


def dodaj_czytelnika(request):
    form = CzytelnikForm(request.POST or None)
    if form.is_valid():
        czytelnik = form.save()
        messages.success(request, f'Dodano czytelnika {czytelnik}.')
        return redirect('czytelnicy')
    return render(request, 'ksiazki/formularz.html', {
        'form': form,
        'naglowek': 'Dodaj czytelnika',
        'anuluj_url': 'czytelnicy',
    })


def edytuj_czytelnika(request, pk):
    czytelnik = get_object_or_404(Czytelnik, pk=pk)
    form = CzytelnikForm(request.POST or None, instance=czytelnik)
    if form.is_valid():
        form.save()
        messages.success(request, f'Zapisano zmiany czytelnika {czytelnik}.')
        return redirect('czytelnicy')
    return render(request, 'ksiazki/formularz.html', {
        'form': form,
        'naglowek': 'Edytuj czytelnika',
        'anuluj_url': 'czytelnicy',
    })


def usun_czytelnika(request, pk):
    czytelnik = get_object_or_404(Czytelnik, pk=pk)
    if request.method == 'POST':
        czytelnik.delete()
        messages.success(request, f'Usunięto czytelnika {czytelnik}.')
        return redirect('czytelnicy')
    return render(request, 'ksiazki/czytelnik_usun.html', {'czytelnik': czytelnik})


def wypozycz(request):
    form = WypozyczenieForm(
        request.POST or None,
        initial={'ksiazka': request.GET.get('ksiazka')},
    )
    if form.is_valid():
        wypozyczenie = form.save()
        messages.success(
            request,
            f'Wypożyczono „{wypozyczenie.ksiazka.tytul}” czytelnikowi {wypozyczenie.czytelnik}.',
        )
        return redirect('wypozyczenia')
    return render(request, 'ksiazki/formularz.html', {
        'form': form,
        'naglowek': 'Wypożycz książkę',
        'anuluj_url': 'lista',
    })


def lista_wypozyczen(request):
    wypozyczenia = Wypozyczenie.objects.filter(data_zwrotu__isnull=True).select_related(
        'ksiazka',
        'czytelnik',
    )
    return render(request, 'ksiazki/wypozyczenia_lista.html', {
        'wypozyczenia': wypozyczenia,
        'dzisiaj': timezone.localdate(),
    })


@require_POST
def zwroc(request, pk):
    wypozyczenie = get_object_or_404(
        Wypozyczenie,
        pk=pk,
        data_zwrotu__isnull=True,
    )
    wypozyczenie.data_zwrotu = timezone.localdate()
    wypozyczenie.save(update_fields=['data_zwrotu'])
    messages.success(request, f'Przyjęto zwrot książki „{wypozyczenie.ksiazka.tytul}”.')
    return redirect('wypozyczenia')
