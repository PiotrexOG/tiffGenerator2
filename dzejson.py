import os
import json
import subprocess

#from saveFile import filename

dzejson = os.path.join("C:\\Users\\pwwesolo\\PycharmProjects\\tiffGenerator\\dzejson\\e.json")

info = {
    'Nr_teczki': f"EW/31041",
    'Miejscowosc': "Gdańsk",
    'Nazwa_ulicy': 'Baźyńskiego',
    'Numer_adresowy': '3',
    'Numer_dzialki': '',
    'Obreb': '',
    'Opis': ' ',
    'Numer_uzgodnienia': '',
    'Data_uzgodnienia': '',
    'Data_projektu': '',
    'Inwestor': 'GIWK',
    'Data_dokumentu': '14.06.2022',
    'Dlugosc': '6,25',
    'Material': '',
    'Srednica': '',
    'Rodzaj_sieci': 'wodociągowa',
    'Numer_inwentarzowy': ''
}
source_path = r"C:\Users\pwwesolo\Documents\31041\3_DOKUMENTACJA_POWYKONAWCZA"

nameOfFile = "A31041CB001.pdf"
nazwa = "A31041CA000.pdf"

source_file_path = os.path.join(source_path, nameOfFile)
#source_file_path = source_file_path.replace("\\", "\\\\")

exif_data = {}

if source_file_path.endswith(".tiff"):
    exif_data = {
        "SourceFile": source_file_path,
        **{f"EXIF:{key}": str(value) for key, value in info.items()}
    }
else:
    exif_data = {
        "SourceFile": source_file_path,
        **{key: str(value) for key, value in info.items()}
    }


with open(dzejson, 'w', encoding='utf-8') as exif_json_file:
    json.dump([info], exif_json_file, indent=4)

command = f'exiftool -j={dzejson} {source_file_path}'
print (command)
subprocess.run(['powershell', '-Command', command], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


nowaNazwa = os.path.join(source_path, nazwa)

os.rename(source_file_path, nowaNazwa)
original_file = f'{source_file_path}_original'
if os.path.exists(original_file):
     os.remove(original_file)