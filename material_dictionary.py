import pandas as pd
import sys
import os

def normalize_name(name):
    return name[0].upper() + name[1:] if name else ''

def get_dict():
    if getattr(sys, 'frozen', False):  # Jeśli aplikacja jest skompilowana
        base_path = os.path.dirname(os.path.abspath(sys.executable))  # Ścieżka do folderu, gdzie jest .exe
    else:
        base_path = r'C:\Users\pwwesolo\Documents\skoroszyt'  # Ścieżka do folderu projektu (tryb deweloperski)

    file_path = os.path.join(base_path, 'baza.xlsx')

    sheet_name = 'slownik_material'

    df = pd.read_excel(file_path, sheet_name=sheet_name)

    name_list = df['name'].tolist()

    normalized_names = [normalize_name(name) for name in name_list]

    unique_names = sorted({name for name in normalized_names})

    return unique_names

