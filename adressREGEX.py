import re

# Funkcja wyciągająca informacje
def extract_info(text):
    # Konwersja do małych liter
    text = text.lower()

    # Wzorce do wyciągania ulicy i numeru adresowego
    regex_patterns = [
        r"\bul(?:\.| |ic)[ ]+([a-ząćęłńóśźż0-9\s]+?)\s+(\d+)[,. ]",  # Ulica + numer adresowy
        r"\b(?:ulica|ul\.?|ulic)[ ]+([a-ząćęłńóśźż0-9\s]+?)\s+(\d+)[,. ]"  # Inne wariacje "ulicy"
    ]

    # Poprawiony wzorzec do wyciągania działek i obrębów
    dzialka_obreb_pattern = r"(?:dz\.?|działk|dza)[^\d]*(\d+(?:/\d+)?(?:[^\w]+\d+(?:/\d+)?)*).*(?:obręb|ob\.?)\s*(\d+)"
    dzialka_pattern = r"(?:dz\.?|działka|dza)[^\d]*(\d+(?:/\d+)?(?:[^\w]+\d+(?:/\d+)?)*).*"
    obreb_pattern = r"(?:obręb|ob\.?)\s*(\d+)"

    results = []

    # Sprawdź, czy w tekście pasują ulice i numery adresowe
    ulica = numer_adresowy = None
    for pattern in regex_patterns:
        match = re.search(pattern, text)
        if match:
            ulica = match.group(1).strip().title()  # Konwersja do tytułowego formatu (pierwsza litera wielka)
            numer_adresowy = match.group(2).strip()
            break

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
            results.append({
                "Ulica": ulica,
                "Numer adresowy": numer_adresowy,
                "Obręb": obreb,
                "Działki": dzialki_clean
            })

    return results

# Testowe dane
texts = [
    "ul. 11 Worcella 13 - dza 5/21 5/48. 45, 89/324, 7/8 obręb 713, działka : 99, 87/345 obręb 342, dzał - 43, 56/45, 77, 88 ob. 234"
]

# Wywołanie funkcji dla każdej linii
for text in texts:
    print(extract_info(text))
