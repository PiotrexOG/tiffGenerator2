import json
from tkinter import messagebox
import requests

class Validator:
    @staticmethod
    def znajdz_ulice(nazwa_ulicy, limit=5):
        # Odczyt danych z pliku JSON
        with open('skr.json', 'r', encoding='utf-8') as file:
            ulice_data = json.load(file)

        # Rozbicie zapytania użytkownika na słowa kluczowe
        slowa_kluczowe = nazwa_ulicy.lower().split()
        dopasowane_ulice = []

        # Szukanie ulic, które zawierają przynajmniej jedno z słów kluczowych
        for ulica in ulice_data['ulice']:
            ul_nazwa = ulica['ulica']['ulNazwaGlowna'].lower()
            if any(slowo in ul_nazwa for slowo in slowa_kluczowe):
                dopasowane_ulice.append(ulica['ulica'])

        # Jeśli znaleziono kilka wyników
        if len(dopasowane_ulice) > 1:
            title = "Proszę doprecyzować nazwę ulicy.\n"
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
            info = "Nie znaleziono ulicy o podanej nazwie."
            messagebox.showwarning("Uwaga", info)
            return None

    @staticmethod
    def pobierz_adresy(ulIIPId):
        url = f'https://mapy.geoportal.gov.pl/wss/service/SLN/guest/sln/adr/ul/PL.PZGIK.200/{ulIIPId}/pel.json'
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    @staticmethod
    def znajdz_adres(numer_adresowy, adresy_data):
        for adres in adresy_data['adresy']:
            if adres['adres']['pktNumer'] == str(numer_adresowy) and adres['adres']['pktStatus'] == 'istniejacy':
                return adres
        return None

    @staticmethod
    def sprawdz_dzialke(gmIdTeryt, obreb, numer_dzialki):
        first_part = gmIdTeryt[:-1]  # Wszystko oprócz ostatniej cyfry
        second_part = gmIdTeryt[-1]  # Ostatnia cyfra

        url = f'https://uldk.gugik.gov.pl/?request=GetParcelByIdOrNr&id={first_part}_{second_part}.{obreb}.{numer_dzialki}'
        print(url)
        response = requests.get(url)
        if response.text.startswith("1"):
            return True
        return False

    @staticmethod
    def waliduj_adres(nazwa_ulicy, numer_adresowy, obreb, numer_dzialki):
        ulIIPId = Validator.znajdz_ulice(nazwa_ulicy)[0]
        if not ulIIPId:
            return "Nie znaleziono ulicy."

        adresy_data = Validator.pobierz_adresy(ulIIPId)
        if not adresy_data:
            return "Błąd pobierania danych adresowych."

        adres = Validator.znajdz_adres(numer_adresowy, adresy_data)
        if not adres:
            return "Nie znaleziono adresu."

        gmIdTeryt = adres['adres']['gmIdTeryt']
        if Validator.sprawdz_dzialke(gmIdTeryt, obreb, numer_dzialki):
            return "Adres istnieje i działka istnieje."
        return "Adres istnieje, ale działka nie istnieje."

# Przykładowe wywołanie
# info = Validator.waliduj_adres("Wałowa", "15", "0719", "36/27")
# print(info)