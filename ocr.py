import re
import pytesseract
from pdf2image import convert_from_path
import adressREGEX

import re

# Wzory słów kluczowych
keyword_patterns = [
    r"\bdz\.",  # "dz."
    r"\bdziałk.*(?:\b [0-9]+\b|\b [0-9]+/[0-9]+\b)",  # "działk" połączone z liczbą lub liczba/liczba
    r"\bposes.*(?:\b [0-9]+[a-z]\b|\b [0-9]+[a-z]/[0-9]+\b)",  # "poses"
    r"\bob\.",  # "ob."
    r"\bobręb",  # "obręb"
]

ulica_patterns = r"(?:\bul\b|\bul\.\b|ulic\w*)"

# Lista wyrażeń regularnych do wykluczenia
unwanted_regex_patterns = [
    r'dz\.u\.',   # "dz.u."
    r'dz\. u\.',  # "dz. u."
]


def extract_combined_lines_with_criteria(text, keyword_patterns):
    # Dzielimy tekst na linie
    lines = text.split('\n')

    # Lista do przechowywania bloków linii
    combined_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        combined_line = line
        match_found = False
        ulica_match_found = False

        # Sprawdzamy dopasowania dla bieżącej linii
        for pattern in keyword_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                match_found = True
            ulica_matches = re.findall(ulica_patterns, line, re.IGNORECASE)
            if ulica_matches:
                ulica_match_found = True

        # Dopóki kolejne linie zawierają dopasowania, łączymy je
        j = i + 1
        while j < len(lines):
            next_line = lines[j].strip()  # Usuwamy białe znaki
            next_match_found = False

            # Jeśli linia jest pusta, przechodzimy do kolejnej niepustej linii
            while next_line == "" and j < len(lines) - 1:
                j += 1
                next_line = lines[j].strip()

            # Sprawdzamy dopasowania w kolejnej linii
            for pattern in keyword_patterns:
                next_matches = re.findall(pattern, next_line, re.IGNORECASE)
                if next_matches:
                    next_match_found = True

            # Jeśli nie ma dopasowań w kluczowych wzorcach, sprawdzamy wzorzec ulicy
            if not next_match_found and match_found:
                next_matches = re.findall(ulica_patterns, next_line, re.IGNORECASE)
                if next_matches:
                    next_match_found = True

            # Jeśli są dopasowania w kolejnej linii, łączymy z poprzednią
            if next_match_found:
                combined_line += " " + next_line  # Łączymy linię z kolejną
                match_found = True
                ulica_match_found = True
                j += 1  # Przechodzimy do następnej linii
            else:
                break  # Przestajemy łączyć, jeśli kolejna linia nie zawiera dopasowania

        # Dodajemy połączony blok tekstu do listy, jeśli były dopasowania
        if match_found:
            combined_lines.append(combined_line)

        # Przechodzimy do linii, która nie zawierała dopasowania lub kolejnej połączonej
        i = j

    return combined_lines






# Funkcja do filtrowania linii zawierających niechciane wyrażenia regex
def filter_out_lines_with_regex(lines, unwanted_regex_patterns):
    filtered_lines = []

    for line in lines:
        # Sprawdzamy, czy linia zawiera którekolwiek z niechcianych wyrażeń regex
        if not any(re.search(pattern, line, re.IGNORECASE) for pattern in unwanted_regex_patterns):
            filtered_lines.append(line)

    return filtered_lines


def filtruj_dane(dane):
    # Filtrujemy elementy, które mają wszystkie wartości inne niż 'brak'
    przefiltrowane = [elem for elem in dane if all(value != 'brak' for value in elem.values())]

    # Jeśli znajdzie się element, który spełnia warunki, zwracamy przefiltrowaną listę
    if przefiltrowane:
        return przefiltrowane
    # W przeciwnym razie zwracamy oryginalną listę
    else:
        return dane


def rozbij_dzialki(dane):
    wynik = []
    for elem in dane:
        # Rozdziel działki na osobne wpisy jeśli są oddzielone przecinkiem
        dzialki = elem['Działki'].split(',')

        # Dla każdej działki twórz nowy słownik i dodaj go do wyniku
        for dzialka in dzialki:
            nowy_elem = elem.copy()  # Kopiujemy słownik, żeby nie nadpisywać oryginału
            nowy_elem['Numer_działki'] = dzialka.strip()  # Usuwamy ewentualne białe znaki
            wynik.append(nowy_elem)

    return wynik



def podziel_na_ulice_od_drugiego(text):
    # Wzorzec do znajdywania słów oznaczających początek nowego adresu ulicy
    ulica_pattern = r"(?=\bul\b|\bul\.\b|ulic\w*)"

    # Znajdź wszystkie wystąpienia wzorca
    wystapienia = list(re.finditer(ulica_pattern, text, flags=re.IGNORECASE))

    # Jeśli jest mniej niż dwa wystąpienia, nie dzielimy
    if len(wystapienia) < 2:
        return [text]

    # Podział tekstu od drugiego wystąpienia wzorca
    pierwsza_czesc = text[:wystapienia[1].start()]  # Od początku do drugiego wystąpienia
    reszta = text[wystapienia[1].start():]  # Od drugiego wystąpienia do końca

    # Podział reszty tekstu na mniejsze fragmenty
    fragmenty = re.split(ulica_pattern, reszta, flags=re.IGNORECASE)

    # Scal pierwszą część z pozostałymi fragmentami
    wynik = [pierwsza_czesc.strip()] + [frag.strip() for frag in fragmenty if frag.strip()]

    return wynik


def przetworz_filtered_lines(filtered_lines):
    nowa_lista = []

    for linia in filtered_lines:
        # Sprawdź, czy linia zawiera wzorzec ulicy
        if re.search(r"\bul\b|\bul\.\b|ulic\w*", linia, flags=re.IGNORECASE):
            # Podziel linię i dodaj do nowej listy
            podzielone = podziel_na_ulice_od_drugiego(linia)
            nowa_lista.extend(podzielone)
        else:
            # Jeśli linia nie zawiera wzorca, dodaj ją do nowej listy bez zmian
            nowa_lista.append(linia)

    return nowa_lista

def rozpoznaj_adresy(file_path):
# Wyciąganie tekstu z każdej strony
    found_adress = False
    results = []
# Konwersja PDF na obrazy
    pages = convert_from_path(file_path, 300)  # 300 dpi dla dobrej jakości OCR

    for page_num, page in enumerate(pages, start=1):
        text = pytesseract.image_to_string(page, lang='pol')  # pol -> język polski

        # Wyciąganie połączonych linii spełniających kryteria
        matching_lines = extract_combined_lines_with_criteria(text, keyword_patterns)

        # Filtrowanie linii, zawierających niechciane wzorce regex
        filtered_lines = filter_out_lines_with_regex(matching_lines, unwanted_regex_patterns)
        ulica_patterns2 = [r"(?:\bul\b|\bul\.\b|ulic\w*)"]

        # Drukowanie przefiltrowanych wyników
        if filtered_lines:
            found_adress = True
            przetworzone_linie = przetworz_filtered_lines(filtered_lines)
            print(f"--- Dopasowane i przefiltrowane linie na stronie {page_num} ---")

            for line in przetworzone_linie:
                extracted_info = adressREGEX.extract_info(line)

                # Rozpakowujemy każdy słownik z listy i dodajemy go osobno do `results`
                for info in extracted_info:
                    results.append(info)

    if not found_adress:
        siema = extract_combined_lines_with_criteria(text, ulica_patterns2)
        print(f"--- DUPA BYLA i przefiltrowane linie na stronie {page_num} ---")
        for line in siema:
            print(line)
            print("\n" + "-" * 40 + "\n")

    if results:
        results = filtruj_dane(results)
        results = rozbij_dzialki(results)
        for res in results:
            print(res)



