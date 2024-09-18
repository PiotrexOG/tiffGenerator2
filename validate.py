import json
from tkinter import messagebox

import requests

# Odczyt danych z pliku JSON
with open('skr.json', 'r', encoding='utf-8') as file:
    ulice_data = json.load(file)

# Funkcja do wyszukania ulicy
def znajdz_ulice(nazwa_ulicy, limit=5):
    # Rozbicie zapytania użytkownika na słowa kluczowe
    slowa_kluczowe = nazwa_ulicy.lower().split()
    #print()
    # Lista do przechowywania dopasowań
    dopasowane_ulice = []
   # info =""
 #   title =""
    # Szukanie ulic, które zawierają przynajmniej jedno z słów kluczowych
    for ulica in ulice_data['ulice']:
        ul_nazwa = ulica['ulica']['ulNazwaGlowna'].lower()
        if any(slowo in ul_nazwa for slowo in slowa_kluczowe):
            dopasowane_ulice.append(ulica['ulica'])

    # Jeśli znaleziono kilka wyników
    if len(dopasowane_ulice) > 1:
        title = "Proszę doprecyzować nazwę ulicy.\n"
        # Jeśli znaleziono więcej niż limit, wyświetl tylko pierwsze 5
        if len(dopasowane_ulice) > limit:
            info = f"Znaleziono {len(dopasowane_ulice)} ulic. Oto pierwsze {limit}:\n"
            for ulica in dopasowane_ulice[:limit]:
                info += f"- {ulica['ulNazwaGlowna']}\n"

        else:
            info = f"Znaleziono {len(dopasowane_ulice)} ulic:\n"
            for ulica in dopasowane_ulice:
                info += f"- {ulica['ulNazwaGlowna']}\n"
        messagebox.showinfo(title, info)
    elif len(dopasowane_ulice) == 1:
        res = ""
        zmieniona = ""
        if nazwa_ulicy != dopasowane_ulice[0]['ulNazwaGlowna']:
            res = messagebox.askquestion('Różnica w nazwie', f"Czy chcesz aby zmienić ulicę na: {dopasowane_ulice[0]['ulNazwaGlowna']}")
            if res == 'yes':
                zmieniona = dopasowane_ulice[0]['ulNazwaGlowna']
        return dopasowane_ulice[0]['ulIIPId'], zmieniona
    else:
        # Jeśli nie znaleziono żadnej ulicy
        info = "Nie znaleziono ulicy o podanej nazwie."
        messagebox.showwarning("Uwaga", info)
        return None


def pobierz_adresy(ulIIPId):
    url = f'https://mapy.geoportal.gov.pl/wss/service/SLN/guest/sln/adr/ul/PL.PZGIK.200/{ulIIPId}/pel.json'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def znajdz_adres(numer_adresowy, adresy_data):
    for adres in adresy_data['adresy']:
        if adres['adres']['pktNumer'] == str(numer_adresowy) and adres['adres']['pktStatus'] == 'istniejacy':
            return adres
    return None


def sprawdz_dzialke(gmIdTeryt, obreb, numer_dzialki):
    # Podzielenie gmIdTeryt na pierwsze 6 cyfr i ostatnią cyfrę
    first_part = gmIdTeryt[:-1]  # Wszystko oprócz ostatniej cyfry
    second_part = gmIdTeryt[-1]  # Ostatnia cyfra

    # Zbudowanie URL zgodnie z wymogami
    url = f'https://uldk.gugik.gov.pl/?request=GetParcelByIdOrNr&id={first_part}_{second_part}.{obreb}.{numer_dzialki}'

    # Wysłanie żądania HTTP
    response = requests.get(url)

    # Sprawdzenie odpowiedzi
    if response.text.startswith("1"):
        return True
    return False


def waliduj_adres(nazwa_ulicy, numer_adresowy, obreb, numer_dzialki):
    ulIIPId = znajdz_ulice(nazwa_ulicy)[0]
    if not ulIIPId:
        return "Nie znaleziono ulicy."

    adresy_data = pobierz_adresy(ulIIPId)
    if not adresy_data:
        return "Błąd pobierania danych adresowych."

    adres = znajdz_adres(numer_adresowy, adresy_data)
    if not adres:
        return "Nie znaleziono adresu."

    gmIdTeryt = adres['adres']['gmIdTeryt']
    if sprawdz_dzialke(gmIdTeryt, obreb, numer_dzialki):
        return "Adres istnieje i działka istnieje."
    return "Adres istnieje, ale działka nie istnieje."

# ulica = "Wałowa"
# numer_adresowy = "15"
# obreb = "0719"
# numer_dzialki = "36/27"
#
# info = waliduj_adres(ulica,numer_adresowy,obreb,numer_dzialki)
# print (info)
