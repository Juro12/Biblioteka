from datetime import timedelta

from django.contrib import admin
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Czytelnik, Ksiazka, Wypozyczenie
from .admin import WypozyczenieInline


class NotFoundPageTests(TestCase):
    def test_unknown_url_returns_generic_404(self):
        response = self.client.get('/nieistniejaca-podstrona/')

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Nie znaleziono strony.', status_code=404)
        self.assertNotContains(response, 'URLconf', status_code=404)


class CzytelnikTests(TestCase):
    def setUp(self):
        self.czytelnik = Czytelnik.objects.create(
            imie='Anna',
            nazwisko='Nowak',
            email='anna@example.com',
            numer_karty='K-001',
        )

    def test_czytelnik_is_registered_in_admin(self):
        self.assertIn(Czytelnik, admin.site._registry)

    def test_reader_detail_shows_full_loan_history(self):
        ksiazka = Ksiazka.objects.create(tytul='Historia', autor='Autor')
        Wypozyczenie.objects.create(ksiazka=ksiazka, czytelnik=self.czytelnik)
        Wypozyczenie.objects.create(
            ksiazka=ksiazka,
            czytelnik=self.czytelnik,
            data_zwrotu=timezone.localdate(),
        )

        response = self.client.get(reverse('szczegoly_czytelnika', args=[self.czytelnik.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['wypozyczenia'].count(), 2)
        self.assertContains(response, 'Historia')
        self.assertContains(response, 'Aktywna')
        self.assertContains(response, 'Zwrócona')

    def test_reader_crud_and_unique_fields(self):
        response = self.client.get(reverse('czytelnicy'))
        self.assertContains(response, 'Anna')

        duplicate = self.client.post(reverse('dodaj_czytelnika'), {
            'imie': 'Inna',
            'nazwisko': 'Osoba',
            'email': self.czytelnik.email,
            'numer_karty': 'K-002',
        })
        self.assertEqual(duplicate.status_code, 200)
        self.assertContains(duplicate, 'Czytelnik with this E-mail already exists.')

        response = self.client.post(reverse('edytuj_czytelnika', args=[self.czytelnik.pk]), {
            'imie': 'Anna',
            'nazwisko': 'Kowalska',
            'email': self.czytelnik.email,
            'numer_karty': self.czytelnik.numer_karty,
        })
        self.assertRedirects(response, reverse('czytelnicy'))
        self.czytelnik.refresh_from_db()
        self.assertEqual(self.czytelnik.nazwisko, 'Kowalska')

        response = self.client.post(reverse('usun_czytelnika', args=[self.czytelnik.pk]))
        self.assertRedirects(response, reverse('czytelnicy'))
        self.assertFalse(Czytelnik.objects.filter(pk=self.czytelnik.pk).exists())


class WypozyczenieTests(TestCase):
    def setUp(self):
        self.ksiazka = Ksiazka.objects.create(
            tytul='Dune',
            autor='Frank Herbert',
            liczba_egzemplarzy=2,
        )
        self.czytelnik = Czytelnik.objects.create(
            imie='Anna',
            nazwisko='Nowak',
            email='anna@example.com',
            numer_karty='K-001',
        )

    def test_borrow_and_default_due_date(self):
        response = self.client.post(reverse('wypozycz'), {
            'ksiazka': self.ksiazka.pk,
            'czytelnik': self.czytelnik.pk,
        })
        self.assertRedirects(response, reverse('wypozyczenia'))

        wypozyczenie = Wypozyczenie.objects.get()
        self.assertEqual(wypozyczenie.data_wypozyczenia, timezone.localdate())
        self.assertEqual(wypozyczenie.termin_zwrotu, timezone.localdate() + timedelta(days=30))
        self.assertIsNone(wypozyczenie.data_zwrotu)

        response = self.client.get(reverse('lista'))
        self.assertContains(response, '>1</td>')

    def test_form_rejects_borrowing_when_no_copies_are_available(self):
        self.ksiazka.liczba_egzemplarzy = 1
        self.ksiazka.save()
        Wypozyczenie.objects.create(ksiazka=self.ksiazka, czytelnik=self.czytelnik)

        response = self.client.post(reverse('wypozycz'), {
            'ksiazka': self.ksiazka.pk,
            'czytelnik': self.czytelnik.pk,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Brak wolnych egzemplarzy tej książki.')
        self.assertEqual(Wypozyczenie.objects.count(), 1)
        self.assertContains(self.client.get(reverse('lista')), 'disabled')

    def test_overdue_loan_is_highlighted_and_return_requires_post(self):
        wypozyczenie = Wypozyczenie.objects.create(
            ksiazka=self.ksiazka,
            czytelnik=self.czytelnik,
            termin_zwrotu=timezone.localdate() - timedelta(days=1),
        )

        response = self.client.get(reverse('wypozyczenia'))
        self.assertContains(response, 'class="table-danger"')
        self.assertEqual(response.context['wypozyczenia'].count(), 1)

        response = self.client.get(reverse('zwroc', args=[wypozyczenie.pk]))
        self.assertEqual(response.status_code, 405)

        response = self.client.post(reverse('zwroc', args=[wypozyczenie.pk]))
        self.assertRedirects(response, reverse('wypozyczenia'))
        wypozyczenie.refresh_from_db()
        self.assertEqual(wypozyczenie.data_zwrotu, timezone.localdate())
        self.assertFalse(
            self.client.get(reverse('wypozyczenia')).context['wypozyczenia'].exists(),
        )

    def test_book_list_paginates_ten_items_and_keeps_filters_in_links(self):
        for index in range(11):
            Ksiazka.objects.create(
                tytul=f'Książka {index:02}',
                autor='Test',
                rok_wydania=2000 + index,
            )

        response = self.client.get(reverse('lista'), {'q': 'Książka'})
        self.assertEqual(response.context['page_obj'].paginator.count, 11)
        self.assertEqual(len(response.context['ksiazki']), 10)
        self.assertContains(response, 'class="pagination')
        self.assertContains(response, 'q=Ksi%C4%85%C5%BCka')

        second_page = self.client.get(reverse('lista'), {
            'q': 'Książka',
            'page': 2,
        })
        self.assertEqual(second_page.context['page_obj'].number, 2)
        self.assertEqual(len(second_page.context['ksiazki']), 1)

    def test_book_list_can_sort_by_title_author_and_year(self):
        Ksiazka.objects.create(tytul='Beta', autor='Zed', rok_wydania=2002)
        Ksiazka.objects.create(tytul='Alfa', autor='Ada', rok_wydania=2001)

        response = self.client.get(reverse('lista'), {'sort': 'autor'})
        self.assertEqual(response.context['ksiazki'][0].autor, 'Ada')

        response = self.client.get(reverse('lista'), {'sort': 'rok', 'direction': 'desc'})
        self.assertEqual(response.context['ksiazki'][0].rok_wydania, 2002)

        response = self.client.get(reverse('lista'), {'sort': 'tytul', 'direction': 'desc'})
        self.assertEqual(response.context['ksiazki'][0].tytul, 'Dune')
        self.assertEqual(response.context['ksiazki'][1].tytul, 'Beta')

    def test_book_admin_has_loan_tabular_inline(self):
        book_admin = admin.site._registry[Ksiazka]
        self.assertIn(WypozyczenieInline, book_admin.inlines)
        self.assertTrue(issubclass(WypozyczenieInline, admin.TabularInline))
