import re
import pytesseract
from pdf2image import convert_from_path


# Funkcja do wyciągania linii spełniających kryteria i zliczania dopasowań, traktując kilka linii jako jedną
def extract_combined_lines_with_criteria_and_count(text, keyword_patterns):
    # Dzielimy tekst na linie
    lines = text.split('\n')

    # Lista do przechowywania bloków linii oraz liczby dopasowań
    combined_lines_with_count = []

    i = 0
    while i < len(lines):
        line = lines[i]
        combined_line = line
        match_count = 0

        # Zliczamy dopasowania dla bieżącej linii
        for pattern in keyword_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            match_count += len(matches)

        # Dopóki kolejne linie zawierają dopasowania, łączymy je
        j = i + 1
        while j < len(lines):
            next_line = lines[j]
            next_match_count = 0

            # Sprawdzamy dopasowania w kolejnej linii
            for pattern in keyword_patterns:
                next_matches = re.findall(pattern, next_line, re.IGNORECASE)
                next_match_count += len(next_matches)

            # Jeśli są dopasowania w kolejnej linii, łączymy z poprzednią
            if next_match_count > 0:
                combined_line += " " + next_line  # Łączymy linię z kolejną
                match_count += next_match_count  # Zwiększamy licznik dopasowań
                j += 1  # Przechodzimy do następnej linii
            else:
                break  # Przestajemy łączyć, jeśli kolejna linia nie zawiera dopasowania

        # Dodajemy połączony blok tekstu i liczbę dopasowań do listy
        if match_count > 0:
            combined_lines_with_count.append((combined_line, match_count))

        # Przechodzimy do linii, która nie zawierała dopasowania lub kolejnej połączonej
        i = j

    # Sortujemy bloki tekstu według liczby dopasowań malejąco
    combined_lines_with_count.sort(key=lambda x: x[1], reverse=True)

    return combined_lines_with_count


# Funkcja do filtrowania linii zawierających niechciane wyrażenia regex
def filter_out_lines_with_regex(lines_with_count, unwanted_regex_patterns):
    filtered_lines = []

    for line, count in lines_with_count:
        # Sprawdzamy, czy linia zawiera którekolwiek z niechcianych wyrażeń regex
        if not any(re.search(pattern, line, re.IGNORECASE) for pattern in unwanted_regex_patterns):
            filtered_lines.append((line, count))

    return filtered_lines

# Konwersja PDF na obrazy
pages = convert_from_path('test.pdf', 300)  # 300 dpi dla dobrej jakości OCR

# Wzory słów kluczowych
keyword_patterns = [
    # r"\bul\.",  # "ul."
    # r"\bulic",  # "ulic"
    r"\bdz\.",  # "dz."
    r"\bdziałk.*(?:\b [0-9]+\b|\b [0-9]+/[0-9]+\b)",  # "działk" połączone z liczbą lub liczba/liczba
    #r"\b [0-9]+/[0-9]+\b",  # Numeracja typu 123/456 (oddzielona spacjami)
    r"\bob\.",  # "ob."
    r"\bobręb",  # "obręb"
  #  r"\bnr\.",  # "nr."
  #  r"\bnumer.*(?:\b [0-9]+\b|\b [0-9]+/[0-9]+\b)"  # "numer" połączone z liczbą lub liczba/liczba
]

# Lista wyrażeń regularnych do wykluczenia
unwanted_regex_patterns = [
    r'dz\.u\.',   # "dz.u."
    r'dz\. u\.',  # "dz. u."
   # r'[0-9]+/[0-9]+/.+'  # Numeracja typu 123/456/
  #  r'\bulicz'  # "ulicz"
]

# Wyciąganie tekstu z każdej strony
for page_num, page in enumerate(pages, start=1):
    text = pytesseract.image_to_string(page, lang='pol')  # pol -> język polski

    # Wyciąganie połączonych linii spełniających kryteria i liczba dopasowań
    matching_lines = extract_combined_lines_with_criteria_and_count(text, keyword_patterns)

    # Filtrowanie linii, zawierających niechciane wzorce regex
    filtered_lines = filter_out_lines_with_regex(matching_lines, unwanted_regex_patterns)

    # Drukowanie przefiltrowanych wyników
    if filtered_lines:
        print(f"--- Dopasowane i przefiltrowane linie na stronie {page_num} ---")
        for line, count in filtered_lines:
            print(f"{line} (Dopasowania: {count})")
            print("\n" + "-" * 40 + "\n")
