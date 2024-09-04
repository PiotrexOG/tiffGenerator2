import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
import json

# Przygotowany kod do dodawania tagów EXIF
def add_exif_data(dest_file_path, exif_data, new_file_name):
    exif_json_path = os.path.join(os.path.dirname(dest_file_path), 'exif_data.json')
    with open(exif_json_path, 'w', encoding='utf-8') as exif_json_file:
        json.dump([exif_data], exif_json_file, indent=4)
    command = f'exiftool -j={exif_json_path} {dest_file_path}'
    subprocess.run(['powershell', '-Command', command], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    new_file_path = os.path.join(os.path.dirname(dest_file_path), new_file_name)
    os.rename(dest_file_path, new_file_path)
    os.remove(exif_json_path)

def process_tiff(dest_file_path, info, new_file_name):
    exif_data_tiff = {
        "SourceFile": dest_file_path,
        **{f"EXIF:{key}": str(value) for key, value in info.items()}
    }
    add_exif_data(dest_file_path, exif_data_tiff, new_file_name)

def process_pdf(dest_file_path, info, new_file_name):
    exif_data_pdf = {
        "SourceFile": dest_file_path,
        **{key: str(value) for key, value in info.items()}
    }
    add_exif_data(dest_file_path, exif_data_pdf, new_file_name)

# GUI z Tkinter
first = ["EW", "EWP", "EWS", "EKS", "KSA", "PZO", "UL", "N"]
second = ["Dokumentacja projektowa", "Dokumentacja odbiorowa", "Dokumentacja powykonawcza","Dokumenty niesklasyfikowane"]

secondA = ["Projekty tekstowe", "Projekty graficzne"]
secondB = ["Zgłoszenie rozpoczęcia robót", "Notatki z robót zanikowych", "Szkice do robót zanikowych", "Wyniki badania wody", "Wyniki prób ciśnieniowych", "Niesklasyfikowane"]
secondC = ["Protokoły odbioru końcowego sieci wodociągowej","Protokoły odbioru sieci kanalizacji sanitarnej", "Protokoły odbioru końcowego przyłączy","Mapy pomiaru powykonawczego sieci", "Mapy pomiaru powykonawczego przyłaczy","Niesklasyfikowane"]
secondD = ["Dokumenty niesklasyfikowane"]

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tagowanie plików TIFF/PDF")
        self.geometry("1920x1080")

        self.file_path = ""
        self.info = {}
        self.skip_empty = 1

        self.create_widgets()

    def create_widgets(self):
        # Wybór pliku
        tk.Label(self, text="Wybierz plik TIFF lub PDF:").grid(row=0, column=0, pady=10, sticky="w")
        tk.Button(self, text="Wybierz plik", command=self.choose_file).grid(row=0, column=1, pady=10, sticky="w")

        # Pola formularza
        fields = [
            ("Nr teczki", "Nr_teczki"),
            ("Miejscowość", "Miejscowosc"),
            ("Nazwa ulicy", "Nazwa_ulicy"),
            ("Numer adresowy", "Numer_adresowy"),
            ("Numer działki", "Numer_dzialki"),
            ("Obręb", "Obreb"),
            ("Opis", "Opis"),
            ("Numer uzgodnienia", "Numer_uzgodnienia"),
            ("Data uzgodnienia", "Data_uzgodnienia"),
            ("Data projektu", "Data_projektu"),
            ("Inwestor", "Inwestor"),
            ("Data dokumentu", "Data_dokumentu"),
            ("Długość", "Dlugosc"),
            ("Materiał", "Material"),
            ("Średnica", "Srednica"),
            ("Numer inwentarzowy", "Numer_inwentarzowy"),
        ]

        self.entries = {}  # Dictionary to hold the entry widgets

        for i, (label_text, tag_key) in enumerate(fields):
            if i == 0:
                continue;
            row = (i // 4) + 1  # Wiersz, który będzie się zwiększał co cztery elementy
            col = (i % 4) * 2  # Kolumna, która będzie od 0 do 6 (bo parzyste kolumny na label, nieparzyste na entry)
            tk.Label(self, text=label_text).grid(row=row, column=col, padx=10, pady=5, sticky="w")

            entry = tk.Entry(self, width=30)
            entry.grid(row=row, column=col + 1, padx=10, pady=5, sticky="w")

            self.entries[tag_key] = entry  # Store entry widget in dictionary with tag_key as key

        # Pole wyboru Rodzaj sieci
        self.rodzaj_sieci_var = tk.StringVar()
        tk.Label(self, text="Rodzaj sieci:").grid(row=5, column=0, pady=10, sticky="w")
        rodzaj_sieci_menu = tk.OptionMenu(self, self.rodzaj_sieci_var, "wodociągowa", "kanalizacyjna")
        rodzaj_sieci_menu.config(width=20)
        rodzaj_sieci_menu.grid(row=5, column=1, pady=10, sticky="w")

        tk.Label(self, text="Numer pliku").grid(row=5, column=2, padx=10, pady=5, sticky="w")
        self.file_number_entry =  tk.Entry(self, width=30)
        self.file_number_entry.grid(row=5, column=3, padx=10, pady=5, sticky="w")
        self.file_number_entry.bind("<KeyRelease>", lambda event: self.format_number(event, 3,self.file_number_entry ))

        row = (0 // 4) + 1  # Wiersz, który będzie się zwiększał co cztery elementy
        col = (0 % 4) * 2  # Kolumna, która będzie od 0 do 6 (bo parzyste kolumny na label, nieparzyste na entry)
        tk.Label(self, text="Numer teczki").grid(row=row, column=col, padx=10, pady=5, sticky="w")
        self.dir_number_entry =  tk.Entry(self, width=30)
        self.dir_number_entry.grid(row=row, column=col+1, padx=10, pady=5, sticky="w")
        self.dir_number_entry.bind("<KeyRelease>", lambda event: self.format_number(event, 5,self.dir_number_entry ))

        # Formularz dynamiczny (Rodzaj teczki i powiązane)
        self.folder_type_var = tk.StringVar()
        self.doc_type_var = tk.StringVar()
        self.subgroup_var = tk.StringVar()

        tk.Label(self, text="Rodzaj teczki dokumentów:").grid(row=6, column=0, pady=10, sticky="w")
        folder_type_menu = tk.OptionMenu(self, self.folder_type_var, "EW", "EWP", "EWS", "EKS", "KSA", "PZO", "UL", "N",
                                         command=self.update_doc_type)
       # folder_type_menu.config(width=20)
        folder_type_menu.grid(row=6, column=1, pady=10)

        tk.Label(self, text="Typ dokumentacji:").grid(row=6, column=2, pady=10, sticky="w")
        self.doc_type_menu = tk.OptionMenu(self, self.doc_type_var, "", command=self.update_subgroup)
       # self.doc_type_menu.config(width=20)
        self.doc_type_menu.grid(row=6, column=3, pady=10)

        tk.Label(self, text="Podgrupa dokumentów:").grid(row=6, column=4, pady=10, sticky="w")
        self.subgroup_menu = tk.OptionMenu(self, self.subgroup_var, "")
        #self.subgroup_menu.config(width=20)
        self.subgroup_menu.grid(row=6, column=5, pady=10)

        tk.Button(self, text="Dodaj tagi", command=self.apply_tags).grid(row=8, column=0, columnspan=4, pady=20)

    def format_number(self, event, max_digits, number_entry):
        current_value = number_entry.get()

        if current_value.isdigit():
            # Usuń wszystkie zera z przodu, ale zachowaj przynajmniej jedno zero, jeśli wpisano same zera
            formatted_value = current_value.lstrip('0') or '0'

            # Jeśli liczba znaków po usunięciu zer jest mniejsza niż 5, uzupełnij zerami z przodu
            if len(formatted_value) < max_digits:
                formatted_value = formatted_value.zfill(max_digits)
            # Jeśli liczba znaków wynosi już 5 i wpisano kolejną cyfrę, usuń pierwszą cyfrę
            elif len(formatted_value) > max_digits:
                formatted_value = formatted_value[-max_digits:]  # Zatrzymuje tylko ostatnie 5 znaków

            number_entry.delete(0, tk.END)
            number_entry.insert(0, formatted_value)
        elif current_value == "":
            # Jeśli pole jest puste, nie robi nic
            return
        else:
            # Jeśli wpisane dane są nieprawidłowe, czyszczenie pola
            number_entry.delete(0, tk.END)

    def apply_tags(self):
        if not self.file_path:
            messagebox.showwarning("Brak pliku", "Nie wybrano pliku do tagowania.")
            return

        file_extension = os.path.splitext(self.file_path)[1].lower()
        info = {}
        if file_extension not in [".tiff", ".pdf"]:
            messagebox.showwarning("Niepoprawny format", "Wybierz plik TIFF lub PDF.")
            return

        # Przetwarzanie pól na podstawie flagi skip_empty
        for key, entry in self.entries.items():
            value = entry.get()
            if self.skip_empty == 1:
                # Pomijanie pustych pól
                if value:
                    info[key] = value
            else:
                # Ustawianie pustych tagów, jeśli pole jest puste
                info[key] = value if value else ""

        # Tutaj można użyć 'info' do dalszego przetwarzania np. dodania tagów
        print("Przetworzone tagi:", info)
        messagebox.showinfo("Informacja", f"Przetworzone tagi: {info}")

        info['Rodzaj sieci'] = self.rodzaj_sieci_var.get()
        print(info['Rodzaj sieci'])
        info['Nr_teczki'] = self.dir_number_entry.get()
        folderType = self.folder_type_var.get()
        groupType = self.doc_type_var.get()
        subGroupType = self.subgroup_var.get()
        file_number_entry= self.file_number_entry.get()

        f = chr(first.index(folderType) + 65)
        s = chr(second.index(groupType) + 65)
        t = 0
        if s == 'A':
            t = chr(secondA.index(subGroupType) + 65)
        elif s == 'B':
            t = chr(secondB.index(subGroupType) + 65)
        elif s =='C':
            t = chr(secondC.index(subGroupType) + 65)
        else:
            t = chr(secondD.index(subGroupType) + 65)

       # siema = self.entries['Nr_teczki'].get()

        new_file_name = f"{f}{info['Nr_teczki']}{s}{t}{file_number_entry}"

        if file_extension == ".tiff":
            process_tiff(self.file_path, info, f"{new_file_name}.tiff")
        elif file_extension == ".pdf":
            process_pdf(self.file_path, info,f"{new_file_name}.pdf")

        messagebox.showinfo("Sukces", f"Tagi zostały dodane do pliku. {f} {s} {t} {info['Nr_teczki']} {file_number_entry}")

    def create_text_entry(self, label_text, tag_key, row, col):
        """Tworzy pole tekstowe do wpisywania wartości tagów, z grid layoutem."""
        tk.Label(self, text=label_text).grid(row=row, column=col, padx=10, pady=5, sticky="w")
        entry = tk.Entry(self)
        entry.grid(row=row, column=col+1, padx=10, pady=5, sticky="w")
        self.info[tag_key] = entry

    def choose_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("TIFF files", "*.tiff"), ("PDF files", "*.pdf")])
        if self.file_path:
            messagebox.showinfo("Wybrano plik", f"Wybrano plik: {self.file_path}")

    def update_doc_type(self, value):
        self.doc_type_var.set('')  # Resetowanie wyboru w `Typ dokumentacji`
        self.subgroup_var.set('')  # Resetowanie wyboru w `Podgrupa dokumentów`

        self.doc_type_menu["menu"].delete(0, "end")  # Czyszczenie starego menu
        self.subgroup_menu["menu"].delete(0, "end")  # Czyszczenie menu Podgrupa dokumentów

        if value in {"EW", "EWP", "EWS", "EKS"}:
            doc_type_options = second
        elif value in {"KSA", "PZO", "UL", "N"}:
            doc_type_options = second
        else:
            doc_type_options  = []


        for option in doc_type_options:
            self.doc_type_menu["menu"].add_command(label=option,
                                                   command=tk._setit(self.doc_type_var, option, self.update_subgroup))

    def update_subgroup(self, value):
        self.subgroup_var.set('')  # Resetowanie wyboru w `Podgrupa dokumentów`
        self.subgroup_menu["menu"].delete(0, "end")  # Czyszczenie starego menu

        if value == "Dokumentacja projektowa":
            subgroup_options = ["Projekty tekstowe", "Projekty graficzne"]
        elif value == "Dokumentacja odbiorowa":
            subgroup_options = ["Zgłoszenie rozpoczęcia robót", "Notatki z robót zanikowych", "Szkice do robót zanikowych",   "Wyniki badania wody", "Wyniki prób ciśnieniowych", "Niesklasyfikowane"]
        elif value == "Dokumentacja powykonawcza":
            subgroup_options = ["Protokoły odbioru końcowego sieci wodociągowej", "Protokoły odbioru sieci kanalizacji sanitarnej", "Protokoły odbioru końcowego przyłączy", "Mapy pomiaru powykonawczego sieci", "Mapy pomiaru powykonawczego przyłaczy", "Niesklasyfikowane"]
        elif value == "Dokumenty niesklasyfikowane":
            subgroup_options = ["Dokumenty niesklasyfikowane"]
        else:
            subgroup_options = []



        for option in subgroup_options:
            self.subgroup_menu["menu"].add_command(label=option, command=tk._setit(self.subgroup_var, option))



if __name__ == "__main__":
    app = Application()
    app.mainloop()
