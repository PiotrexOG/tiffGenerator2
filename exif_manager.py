import os
import json
import subprocess
import sys

class ExifManager:
    @staticmethod
    def _get_exiftool_path():
        if getattr(sys, 'frozen', False):  # Sprawdza, czy aplikacja działa w trybie zamrożonym (np. exe)
            base_path = os.path.dirname(sys.executable)  # Folder z .exe
            exiftool_path = os.path.join(base_path, '_internal', 'exiftool', 'exiftool.exe')
        else:
            base_path = r'C:\Users\pwwesolo\Downloads\exiftool-12.93_64\exiftool-12.93_64'
            exiftool_path = os.path.join(base_path, 'exiftool.exe')

        # Ścieżka do spakowanej wersji ExifTool


        return exiftool_path

    @staticmethod
    def _add_exif_data(dest_file_path, exif_data, new_file_name):
        exiftool_path = ExifManager._get_exiftool_path()  # Używa funkcji do uzyskania ścieżki

        # Sprawdzenie, czy exiftool.exe istnieje
        if not os.path.exists(exiftool_path):
            print(f"Plik {exiftool_path} nie istnieje!")
            return

        # Tworzenie pliku JSON z danymi EXIF
        exif_json_path = f"{os.path.dirname(dest_file_path)}" + "/exif_data.json"
        with open(exif_json_path, 'w', encoding='utf-8') as exif_json_file:
            json.dump([exif_data], exif_json_file, indent=4)

        # Tworzenie polecenia do uruchomienia ExifTool z plikiem JSON
        command = f'{exiftool_path} -j={exif_json_path} {dest_file_path}'
        print (command)
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Zmienianie nazwy pliku po przetworzeniu przez ExifTool
        new_file_path = os.path.join(os.path.dirname(dest_file_path), new_file_name)
        os.rename(dest_file_path, new_file_path)
        os.remove(exif_json_path)

    @staticmethod
    def process_tiff(dest_file_path, info, new_file_name):
        exif_data_tiff = {
            "SourceFile": dest_file_path,
            **{f"EXIF:{key}": str(value) for key, value in info.items()}
        }
        ExifManager._add_exif_data(dest_file_path, exif_data_tiff, new_file_name)

    @staticmethod
    def process_pdf(dest_file_path, info, new_file_name):
        exif_data_pdf = {
            "SourceFile": dest_file_path,
            **{key: str(value) for key, value in info.items()}
        }
        ExifManager._add_exif_data(dest_file_path, exif_data_pdf, new_file_name)
