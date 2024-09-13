import os
import subprocess

def update_inwestor_tag(root_folder, tag_name, new_value):
    # Przechodzenie przez każdy plik w podanym katalogu
    for subdir, dirs, files in os.walk(root_folder):
        for file in files:
            # Sprawdzenie rozszerzenia pliku
            if file.lower().endswith(('.tiff', '.pdf')):
                file_path = os.path.join(subdir, file)
                try:
                    # Wywołanie exiftool do aktualizacji tagu
                    subprocess.run(['exiftool', f'-{tag_name}={new_value}', file_path, '-overwrite_original'], check=True)
                    print(f"Zaktualizowano plik: {file_path}")
                except subprocess.CalledProcessError as e:
                    print(f"Błąd podczas aktualizacji pliku: {file_path}. Szczegóły: {e}")

# Ustawienia skryptu
root_folder = r"C:\Users\pwwesolo\Documents\n5\tiff&pdfTagged"
tag_name = "Ulica"
new_value = "Long#13&713@5/21@5/48@7/8;Short#6&714@36/27&719@7/8;Wide#19&130@216/2@540;Narrow#3&543@257/4@323@324"

# Uruchomienie skryptu
update_inwestor_tag(root_folder, tag_name, new_value)
