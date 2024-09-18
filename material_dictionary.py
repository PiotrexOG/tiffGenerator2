import pandas as pd



# Funkcja do normalizacji nazwy (pierwsza litera wielka, reszta jak jest)
def normalize_name(name):
    return name[0].upper() + name[1:] if name else ''

def get_dict():
    # Ścieżka do pliku Excel
    file_path = r'C:\Users\pwwesolo\Documents\skoroszyt\baza.xlsx'

    # Nazwa zakładki, którą chcesz wybrać
    sheet_name = 'slownik_material'

    # Odczytaj zakładkę do DataFrame
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Zamień kolumnę 'name' na listę
    name_list = df['name'].tolist()

    # Normalizuj wszystkie nazwy w liście
    normalized_names = [normalize_name(name) for name in name_list]

    # Usuwanie duplikatów, ignorując wielkość liter
    unique_names = sorted({name for name in normalized_names})

    return unique_names

