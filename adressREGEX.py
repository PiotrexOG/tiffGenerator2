import re

# Funkcja wyciągająca informacje
def extract_info(text):
    # Konwersja do małych liter
    text = text.lower()
    print(text)

    # Wzorce do wyciągania ulicy i numeru adresowego
    ulica_patterns = r"(?:\bul\b|\bul\.\b|ulic\w*|\bui\b|\bui\.\b)[ ]*[^\w\s]?[ ]*([a-ząćęłńóśźż0-9\s]+?)\s+(\d+\w*)[,. ]"
    dzialka_pattern = r"(?:\bdz\b|\bdz\.\b|dział\w*)[^\d]*(\d+(?:/\d+)?(?:[^\w]+\d+(?:/\d+)?)*).*"
    #dzialka_pattern = r"(?:\bdz\b|\bdz\.\b|dział\w*)[^\d]*(\d+(?:/\d+)?(?:[^\w]+\d+(?:/\d+)?)*).*"

    obreb_pattern = r"(?:ob\.|ob|obr|obr\.|obrę\w*)[^\d]*(\d+\w*)"

    results = []

    # Sprawdź, czy w tekście pasują ulice i numery adresowe
    ulica = numer_adresowy = None

    match = re.search(ulica_patterns, text)
    if match:
        ulica = match.group(1).strip().title()  # Konwersja do tytułowego formatu (pierwsza litera wielka)
        numer_adresowy = match.group(2).strip()

    if not ulica:
        # Nazwa ulicy (obowiązkowa)
        ulica_pattern = r"(?:ul[^\w]*|ui[^\w]*)([\w\s/]+?)(?=[,. )]|$)"

        match_ulica = re.search(ulica_pattern, text)
        ulica = match_ulica.group(1).strip().title() if match_ulica else "brak"

    if not numer_adresowy:
        numer_adresowy_pattern = r"poses[^d]*(?!dz\.?\s)\b(\d+\s?[a-zA-Z]?)\b"
        match_numer_adresowy = re.search(numer_adresowy_pattern, text)
        numer_adresowy = match_numer_adresowy.group(1).strip() if match_numer_adresowy else "brak"

    # Znajdź wszystkie wystąpienia obrębów
    obreb_matches = list(re.finditer(obreb_pattern, text))

    # Iterujemy po każdym obrębie i szukamy dla niego odpowiednich działek
    for i, obreb_match in enumerate(obreb_matches):
        obreb = obreb_match.group(1).strip()

        # Ustal zakres do szukania działek (między aktualnym a poprzednim obrębem)
        start_idx = 0 if i == 0 else obreb_matches[i - 1].end()  # Początek to koniec poprzedniego obrębu
        search_area = text[start_idx:obreb_match.start()]  # Szukamy działek tylko przed aktualnym obrębem

        # Szukamy działek w obszarze poprzedzającym obręb
        dzialka_match = re.search(dzialka_pattern, search_area)

        if dzialka_match:
            dzialki_raw = dzialka_match.group(1)  # Surowe działki z tekstu

            # Usuwanie spacji i zamiana wszystkich separatorów na przecinki
            dzialki_clean = re.sub(r'[^\d/]+', ',', dzialki_raw)  # Zamiana dowolnych separatorów na przecinki

            # Dodaj do wyników
            if not any(
                    item == {"Ulica": ulica, "Numer_adresowy": numer_adresowy, "Obręb": obreb, "Działki": dzialki_clean}
                    for item in results):
                        results.append({
                            "Ulica": ulica,
                            "Numer_adresowy": numer_adresowy,
                            "Obręb": obreb,
                            "Działki": dzialki_clean
                        })


    # Jeśli nie ma wyników, próbujemy znaleźć na podstawie słowa 'poses.*'
    # Jeśli nie ma wyników, próbujemy znaleźć na podstawie słowa 'poses.*'
    if not results:
        # Numer adresowy (opcjonalny)
        numer_adresowy_pattern = r"poses.*?(\d+\s?[a-zA-Z]?)"
        match_numer_adresowy = re.search(numer_adresowy_pattern, text)
        numer_adresowy = match_numer_adresowy.group(1).strip() if match_numer_adresowy else "brak"

        # Numer działki (obowiązkowy)
        dzialka_pattern = r"(?:\bdz\b|\bdz\.\b|dział\w*)[^\d]*(\d+(?:/\d+)?(?:[^\w]+\d+(?:/\d+)?)*).*"
       # dzialka_pattern = r"(?:\bdz\b|\bdz\.\b)[^\d]*(\d+/\d+|\d+)"

        match_dzialka = re.search(dzialka_pattern, text)
        # dzialki_clean = "brak"
        # if match_dzialka:
        #     dzialki_raw = match_dzialka.group(1).strip()  # Surowe działki z tekstu
        #
        #     # Usuwanie spacji i zamiana wszystkich separatorów na przecinki
        #     dzialki_clean = re.sub(r'[^\d/]+', ',', dzialki_raw)  # Zamiana dowolnych separatorów na przecinki

        dzialka = match_dzialka.group(1).strip() if match_dzialka else "brak"

        # Numer obrębu (opcjonalny)
        obreb_pattern = r"(?:obr\.|obr|ob|ob\.|obrę[^\w]*)[^\d]*(\d+\w*)?"
        match_obreb = re.search(obreb_pattern, text)
        obreb = match_obreb.group(1).strip() if match_obreb else "brak"

        # Nazwa ulicy (obowiązkowa)
        ulica_pattern = r"(?:ul[^\w]*|ui[^\w]*)([\w\s]+?)(?=[,. ]|$)"

        match_ulica = re.search(ulica_pattern, text)
        ulica = match_ulica.group(1).strip().title() if match_ulica else "brak"
       # print(dzialka)
        # Dodanie wyników do listy
        if not any(
                item == {"Ulica": ulica, "Numer_adresowy": numer_adresowy, "Obręb": obreb, "Działki": dzialka}
                for item in results):
            results.append({
                "Ulica": ulica,
                "Numer_adresowy": numer_adresowy,
                "Obręb": obreb,
                "Działki": dzialka
            })

    return results


# # Testowe dane
# texts = [
#     "Adres budowy: ul. Telimeny 38 A, dz. nr 178/4 obr. 170S",
#     "Zlecam montaż wodomierza nr posesji/ działki 30 B dz. 2/4 przy ul. Wąwóz"
# ]
#
# # Wywołanie funkcji dla każdej linii
# for text in texts:
#     print(extract_info(text))


# #Testowe dane
# texts = [
#     # "Budowa przyłącza kanalizacji sanitarnej dz. 36/27 obręby 0719, dz. 7/8 obręb 0713 w ulice Bitwy pod Lenino 7 w Gdańsku.",
#     # "ADRES: ul. BITWY POD LENINO 6, GDAŃSK OBIEKTU DZ 36/27 obręb nr 0719, DZ. NR 7/8 OBRĘB NR 0713",
#     # "ulicydfsd 11 Worcella 13 - dz.iał numery. 5/21 5/48. 45, 89/324, 7/8 ob 713, działka numry: 99, 87/345 obręb 342, dzałki - 43, 56/45, 77, 88 ob. 234"
#     # " Adres budowy: ul. Telimeny 38 A, dz. nr 178/4 obr. 170S",
#     # "Zlecam montaż wodomierza nr posesji 30 B dz. 2/4 przy ul. Wąwóz",
#
#     "dz. 3/4, 5/6; 6-7"
# ]
#
# # Wywołanie funkcji dla każdej linii
# for text in texts:
#     print(extract_info(text))
