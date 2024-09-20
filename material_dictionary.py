import pandas as pd

def normalize_name(name):
    return name[0].upper() + name[1:] if name else ''

def get_dict():
    file_path = r'C:\Users\pwwesolo\Documents\skoroszyt\baza.xlsx'

    sheet_name = 'slownik_material'

    df = pd.read_excel(file_path, sheet_name=sheet_name)

    name_list = df['name'].tolist()

    normalized_names = [normalize_name(name) for name in name_list]

    unique_names = sorted({name for name in normalized_names})

    return unique_names

