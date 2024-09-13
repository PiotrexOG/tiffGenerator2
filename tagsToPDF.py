import os
import random
import string
from datetime import datetime, timedelta
from random import randint
from PIL import Image
import numpy as np
import json
import subprocess
import shutil

# Globalne zmienne
miasta = ['Gdańsk', 'Sopot', 'Gdynia', 'Rumia', 'Reda', 'Wejherowo', 'Pruszcz Gdański', 'Żukowo', 'Kartuzy',
          'Nowy Dwór Gdański']
ulice = ['Wałowa', 'Chmielna', 'Długa', 'Grunwaldzka', 'Szewska', 'Jaśkowa Dolina', 'Ogarna', 'Szeroka', 'Świętojańska',
         'Piotrkowska']
obreby = ['Orunia', 'Oliwa', 'Wrzeszcz', 'Letnica', 'Chełm', 'Suchanino', 'Brzeźno', 'Jelitkowo', 'Zaspa', 'Przymorze']
materialy = ['Amellinium', 'Stal', 'Żeliwo', 'Miedź', 'PVC', 'PEHD', 'Beton', 'Kamień', 'Drewno', 'Asfalt']
rodzaje_sieci = ['wodociągowa', 'kanalizacyjna', 'wodociągowa i kanalizacyjna']
rodzaje_srednic = [10,20,40,80,100,150,200,500]
Ids = ['EW', 'EWP', 'EWS', 'EKS', 'KSA', 'PZO', 'UL', 'N']
inwestorzy = ['Invest Komfort', 'Dekpol S.A.', 'Torus Sp. z o.o.', 'Euro Styl S.A.', 'Allcon S.A.', 'Inpro S.A.', 'Hossa S.A.']

base_path = "C:\\Users\\pwwesolo\\Documents\\n5\\NNN"
source_folder_path = os.path.join("C:\\Users\\pwwesolo\\Downloads")
dzejson = os.path.join("C:\\Users\\pwwesolo\\PycharmProjects\\tiffGenerator\\dzejson")
source_file_path = os.path.join(source_folder_path, "doc.pdf")

# Tworzymy listę unikalnych 5-cyfrowych numerów, które będą powtarzane
unique_numbers = [''.join(random.choices(string.digits, k=5)) for _ in range(10)]
info_cache = {}


def generate_random_filename(existing_numbers):
    letters = 'ABCDEFGH'
    X = random.choice(letters)
    Y = random.choices(
        population=['A', 'B', 'C', 'D'],
        weights=[2, 6, 6, 1],  # Szanse: 2/15 dla A, 6/15 dla B, 6/15 dla C, 1/15 dla D
        k=1
    )[0]

    if Y == 'A':
        Z_choices = 'AB'
    elif Y in ['B', 'C']:
        Z_choices = 'ABCDEF'
    elif Y == 'D':
        Z_choices = 'A'

    Z = random.choice(Z_choices)
    digits = ''.join(random.choice(existing_numbers))
    digits_end_pdf = ''.join(random.choices(string.digits, k=3))
    digits_end_tiff = ''.join(random.choices(string.digits, k=3))

    filename_pdf = f"{X}{digits}{Y}{Z}{digits_end_pdf}.pdf"
    filename_tiff = f"{X}{digits}{Y}{Z}{digits_end_tiff}.tiff"

    return X, filename_pdf, filename_tiff, digits


def generate_random_date(start_year=2020, end_year=2024):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime('%d.%m.%Y')

def randInfo(X, digits):
    info = {
        # 'Nr_teczki': f"{Ids[ord(X) - ord('A')]}{digits}",
        # 'Miejscowosc': random.choice(miasta),
        # 'Nazwa_ulicy': random.choice(ulice),
        # 'Numer_adresowy': random.randint(0, 1000),
        # 'Numer_dzialki': random.randint(0, 1000),
        # 'Obreb': random.choice(obreby),
        'Opis': 'Long#13@5/21@5/48@7/8&713,Short#6@36/27&719@7/8&713,Wide#19@216/2@540&0010,Narrow#3@257/4@323@324&0012',
        # 'Numer_uzgodnienia': f"UD-{random.randint(0, 2000)}.{random.randint(1,10)}/{random.randint(2018, 2023)}",
        # 'Data_uzgodnienia': generate_random_date(),
        # 'Data_projektu': generate_random_date(),
        # 'Inwestor': random.choice(inwestorzy),
        # 'Data_dokumentu': generate_random_date(),
        # 'Dlugosc': random.randint(0, 100),
        # 'Material': random.choice(materialy),
        # 'Srednica': random.choice(rodzaje_srednic),
        # 'Rodzaj_sieci': random.choice(rodzaje_sieci),
        # 'Numer_inwentarzowy': random.randint(0, 100)
    }
    return info

def myInfo():
    info = {
        'Nr_teczki': f"EW/30854",
        'Miejscowosc':"Gdańsk",
        'Nazwa_ulicy': 'Wałowa',
        'Numer_adresowy': 27,
        'Numer_dzialki': 4,
        'Obreb': 'Orunia',
        'Opis': ' ',
        'Numer_uzgodnienia': 'UD',
        'Data_uzgodnienia': '21.11.2022',
        'Data_projektu': '16.02.2021',
        'Inwestor': 'Inpro S.A.',
        'Data_dokumentu': '12.04.2019',
        'Dlugosc': 80,
        'Material': 'Stal',
        'Srednica': 120,
        'Rodzaj_sieci': 'wodociągowa',
        'Numer_inwentarzowy': 7
    }
    return info

def getInfo(X, digits):
    key = f"{X}{digits}"

    if key not in info_cache:
        info = randInfo(X, digits)
        info_cache[key] = info
    else:
        # 30% szansy na wygenerowanie nowych danych
        if randint(1, 10) <= 3:
            info = randInfo(X, digits)
        else:
            info = info_cache[key]

    return info


def save_image_as_tiff(dest_file_path_tiff):
    data = np.random.rand(100, 100, 3) * 255
    image = Image.fromarray(data.astype('uint8'), 'RGB')
    image.save(dest_file_path_tiff)


def copy_pdf(source_file_path, dest_file_path_pdf):
    shutil.copy2(source_file_path, dest_file_path_pdf)


def add_exif_data(dest_file_path, exif_data):
    exif_json_path = os.path.join(os.path.dirname(dest_file_path), 'exif_data.json')
    with open(exif_json_path, 'w', encoding='utf-8') as exif_json_file:
        json.dump([exif_data], exif_json_file, indent=4)
    command = f'exiftool -j={exif_json_path} {dest_file_path}'
    print (command)
    subprocess.run(['powershell', '-Command', command], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # os.remove(exif_json_path)
    # original_file = f'{dest_file_path}_original'
    # if os.path.exists(original_file):
    #     os.remove(original_file)

def process_tiff(dest_folder_path, filename_tiff, info):
    dest_file_path_tiff = os.path.join(dest_folder_path, filename_tiff)
    exif_data_tiff = {
        "SourceFile": dest_file_path_tiff,
        **{f"EXIF:{key}": str(value) for key, value in info.items()}
    }
    save_image_as_tiff(dest_file_path_tiff)
    add_exif_data(dest_file_path_tiff, exif_data_tiff)
    print(f"Plik zapisany jako: {dest_file_path_tiff}")

def process_pdf(dest_folder_path, filename_pdf, info):
    dest_file_path_pdf = os.path.join(dest_folder_path, filename_pdf)
    exif_data_pdf = {
        "SourceFile": dest_file_path_pdf,
        **{key: str(value) for key, value in info.items()}
    }
    copy_pdf(source_file_path, dest_file_path_pdf)
    add_exif_data(dest_file_path_pdf, exif_data_pdf)
    print(f"Plik zapisany jako: {dest_file_path_pdf}")

def process_files(X, filename_pdf, filename_tiff, digits):
    dest_folder_path = os.path.join(base_path, f"FOLDER_{X}")
    os.makedirs(dest_folder_path, exist_ok=True)
    info = getInfo(X, digits)

    if randint(1,10) <= 7:
        process_pdf(dest_folder_path, filename_pdf, info)
    if randint(1,10) <= 7:
        process_tiff(dest_folder_path, filename_tiff, info)


def main():
    for i in range(1):
        X, filename_pdf, filename_tiff, digits = generate_random_filename(unique_numbers)
        process_files(X, filename_pdf, filename_tiff, digits)
    print("Cleanup completed.")





if __name__ == "__main__":
    main()
