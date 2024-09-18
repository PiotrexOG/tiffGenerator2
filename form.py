
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
import json
import ocr
import threading
import validate


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

        # Zmienne dla plików, tagów, itp.
        self.file_path = ""
        self.info = {}
        self.skip_empty = 1

        # Dane dla dynamicznej listy adresów
        self.data = []

        self.entries = []  # Lista na widgety do wpisywania danych
        self.dynamic_widgets = []
        self.create_widgets()

    def update_address_fields(self, result):
        """Aktualizowanie pól dynamicznych po zakończeniu OCR."""
        self.data = result

        # Usuwamy poprzednie dynamiczne wiersze, jeśli istnieją
        for widget_dict in self.dynamic_widgets:
            for widget in widget_dict.values():
                if isinstance(widget, tk.Widget):  # Sprawdzamy, czy jest to widget, a nie string
                    widget.destroy()

        self.dynamic_widgets = []

        tk.Label(self, text="Adresy:").grid(row=7, column=0, pady=50, sticky="w")
        fields_dynamic = ["Ulica", "Numer_adresowy", "Numer_działki", "Obręb"]
        if result:
            for i, item in enumerate(self.data):
                row_entries = {}

                entry = tk.Entry(self, width=20)
                entry.grid(row=8 + i, column=0, padx=10, pady=5, sticky="w")
                entry.insert(0, "Gdańsk")
                row_entries["Miejscowość"] = entry
                row_entries["Miejscowość_old"] = entry.get()  # Przechowujemy starą wartość

                col = 1
                for field in fields_dynamic:
                    entry = tk.Entry(self, width=20)
                    entry.grid(row=8 + i, column=col, padx=10, pady=5, sticky="w")
                    entry.insert(0, item[field.split()[0]])
                    row_entries[field] = entry
                    row_entries[field + "_old"] = entry.get()  # Przechowujemy starą wartość
                    col += 1

                # Przycisk Waliduj
                button_validate = tk.Button(self, text="Waliduj", command=lambda e=row_entries: self.validate_adress(e))
                button_validate.grid(row=8 + i, column=col, padx=10, pady=5)
                row_entries["Waliduj"] = button_validate

                # Dodajemy pusty przycisk Zatwierdź na początku
                button_confirm = tk.Button(self, text="Zatwierdź",
                                           command=lambda e=row_entries: self.confirm_address(e))
                button_confirm.grid(row=8 + i, column=col + 1, padx=10, pady=5)
                button_confirm.grid_remove()  # Na początku ukrywamy przycisk
                row_entries["Zatwierdź"] = button_confirm

                self.dynamic_widgets.append(row_entries)

    def create_widgets(self):
        # Wybór pliku
        tk.Label(self, text="Wybierz plik TIFF lub PDF:").grid(row=0, column=0, pady=10, sticky="w")
        tk.Button(self, text="Wybierz plik", command=self.choose_file).grid(row=0, column=1, pady=10, sticky="w")

        # Pola formularza - statyczne tagi
        fields = [
            ("Nr teczki", "Nr_teczki"),
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

        self.static_entries = {}  # Słownik na pola wejściowe statycznych tagów

        # Tworzenie pól dla statycznych tagów
        for i, (label_text, tag_key) in enumerate(fields):
            if i == 0:
                continue
            row = (i // 4) + 1
            col = (i % 4) * 2
            tk.Label(self, text=label_text).grid(row=row, column=col, padx=10, pady=5, sticky="w")

            entry = tk.Entry(self, width=30)
            entry.grid(row=row, column=col + 1, padx=10, pady=5, sticky="w")

            self.static_entries[tag_key] = entry


        # Pole wyboru Rodzaj sieci
        self.rodzaj_sieci_var = tk.StringVar()
        tk.Label(self, text="Rodzaj sieci:").grid(row=5, column=0, pady=50, sticky="w")
        rodzaj_sieci_menu = tk.OptionMenu(self, self.rodzaj_sieci_var, "wodociągowa", "kanalizacyjna")
        rodzaj_sieci_menu.config(width=20)
        rodzaj_sieci_menu.grid(row=5, column=1, pady=10, sticky="w")

        tk.Label(self, text="Numer pliku").grid(row=3, column=6, padx=10, pady=5, sticky="w")
        self.file_number_entry = tk.Entry(self, width=30)
        self.file_number_entry.grid(row=3, column=7, padx=10, pady=5, sticky="w")
        self.file_number_entry.bind("<KeyRelease>", lambda event: self.format_number(event, 3, self.file_number_entry))

        row = (0 // 4) + 1  # Wiersz, który będzie się zwiększał co cztery elementy
        col = (0 % 4) * 2  # Kolumna, która będzie od 0 do 6 (bo parzyste kolumny na label, nieparzyste na entry)
        tk.Label(self, text="Numer teczki").grid(row=row, column=col, padx=10, pady=5, sticky="w")
        self.dir_number_entry = tk.Entry(self, width=30)
        self.dir_number_entry.grid(row=row, column=col + 1, padx=10, pady=5, sticky="w")
        self.dir_number_entry.bind("<KeyRelease>", lambda event: self.format_number(event, 5, self.dir_number_entry))

        # Lista rozwijana i typy dokumentów
        self.folder_type_var = tk.StringVar()
        self.doc_type_var = tk.StringVar()
        self.subgroup_var = tk.StringVar()

        tk.Label(self, text="Rodzaj teczki dokumentów:").grid(row=6, column=0, pady=100, sticky="w")
        folder_type_menu = tk.OptionMenu(self, self.folder_type_var, "EW", "EWP", "EWS", "EKS", "KSA", "PZO", "UL", "N",
                                         command=self.update_doc_type)
        # folder_type_menu.config(width=20)
        folder_type_menu.grid(row=6, column=1, pady=50)

        tk.Label(self, text="Typ dokumentacji:").grid(row=6, column=2, pady=100, sticky="w")
        self.doc_type_menu = tk.OptionMenu(self, self.doc_type_var, "", command=self.update_subgroup)
        # self.doc_type_menu.config(width=20)
        self.doc_type_menu.grid(row=6, column=3, pady=50)

        tk.Label(self, text="Podgrupa dokumentów:").grid(row=6, column=4, pady=100, sticky="w")
        self.subgroup_menu = tk.OptionMenu(self, self.subgroup_var, "")
        # self.subgroup_menu.config(width=20)
        self.subgroup_menu.grid(row=6, column=5, pady=10)

        tk.Button(self, text="Dodaj tagi", command=self.apply_tags).grid(row=7, column=10, columnspan=4, pady=20)

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

    def validate_adress(self, row_entries):
        """Funkcja do wyświetlania i walidacji danych z dynamicznego wiersza."""

        result = {}
        for key, widget in row_entries.items():
            if isinstance(widget, tk.Entry):  # Sprawdzamy, czy widget jest polem Entry
                result[key] = widget.get()  # Pobieramy wartość z pola Entry
                widget.config(highlightbackground="black", highlightthickness=0)

        print("Wiersz dynamiczny:", result)

        # Pobranie danych z pól formularza
        ulica = result.get("Ulica")
        numer_adresowy = result.get("Numer_adresowy")
        numer_dzialki = result.get("Numer_działki")
        obreb = result.get("Obręb")

        gmIdTeryt = "2261011"

        # Walidacja ulicy
        znaleziona_ulica = validate.znajdz_ulice(ulica)
        if znaleziona_ulica:
            row_entries["Ulica"].config(highlightbackground="green", highlightthickness=2)

            # Aktualizacja pola "Ulica" jeśli znaleziono alternatywną nazwę
            if znaleziona_ulica[1]:
                print("Zmieniamy wartość pola 'Ulica' na:", znaleziona_ulica[1])
                row_entries["Ulica"].delete(0, tk.END)
                row_entries["Ulica"].insert(0, znaleziona_ulica[1])

            # Jeśli mamy ID ulicy i podano numer adresowy, walidujemy numer adresowy
            if znaleziona_ulica[0] and numer_adresowy != "brak":
                adresy_data = validate.pobierz_adresy(znaleziona_ulica[0])

                if not adresy_data:
                    messagebox.showwarning("Błąd połączenia", "Nie można zweryfikować poprawności numeru adresowego")
                else:
                    adres = validate.znajdz_adres(numer_adresowy, adresy_data)
                    if not adres:
                        messagebox.showwarning("Błąd", "Nie znaleziono pasującego numeru dla podanej ulicy")
                        row_entries["Numer_adresowy"].config(highlightbackground="red", highlightthickness=2)
                    else:
                        gmIdTeryt = adres['adres']['gmIdTeryt']
                        print (gmIdTeryt)
                        row_entries["Numer_adresowy"].config(highlightbackground="green", highlightthickness=2)
            else:
                # Jeśli numer adresowy nie podano, kolorujemy pole na żółto
                row_entries["Numer_adresowy"].config(highlightbackground="yellow", highlightthickness=2)
        else:
            # Jeśli nie znaleziono ulicy, pole Ulica zostaje oznaczone na czerwono
            row_entries["Ulica"].config(highlightbackground="red", highlightthickness=2)

        # Walidacja działki
        if validate.sprawdz_dzialke(gmIdTeryt, obreb, numer_dzialki):
            row_entries["Obręb"].config(highlightbackground="green", highlightthickness=2)
            row_entries["Numer_działki"].config(highlightbackground="green", highlightthickness=2)
        else:
            row_entries["Obręb"].config(highlightbackground="red", highlightthickness=2)
            row_entries["Numer_działki"].config(highlightbackground="red", highlightthickness=2)

        button_confirm = row_entries["Zatwierdź"]
        button_validate = row_entries["Waliduj"]
        button_confirm.grid()
        button_confirm.config(state="normal", bg="white")  # Odblokowanie przycisku Zatwierdź
        button_validate.config(bg="SystemButtonFace")  # Resetowanie koloru przycisku Waliduj

        # Przywróć stare wartości jako punkt odniesienia
        for key, widget in row_entries.items():
            if isinstance(widget, tk.Entry):
                row_entries[key + "_old"] = widget.get()  # Aktualizujemy wartość początkową


    def confirm_address(self, row_entries):
        """Funkcja do zatwierdzania adresu i blokowania pól do edycji."""
        # Sprawdzenie zmian przed zatwierdzeniem
        for key, widget in row_entries.items():
            if isinstance(widget, tk.Entry):
                # Porównujemy z przechowaną starą wartością
                print(row_entries[key + "_old"])
                if widget.get() != row_entries[key + "_old"]:
                    row_entries["Zatwierdź"].config(state="disabled", bg="lightgray")
                    row_entries["Waliduj"].config(bg="yellow")
                    return  # Przerwij, jeśli wykryto zmianę

        # Zatwierdzanie - blokowanie pól i zmiana przycisku
        for key, widget in row_entries.items():
            if isinstance(widget, tk.Entry):
                widget.config(state="disabled", bg="lightgray")

        # Zmiana przycisku na "Edytuj"
        button_confirm = row_entries["Zatwierdź"]
        button_confirm.config(text="Edytuj", command=lambda e=row_entries: self.edit_address(e))

    def edit_address(self, row_entries):
        """Funkcja do odblokowywania pól do edycji."""
        # Odblokowanie pól i zmiana tła na białe
        for key, widget in row_entries.items():
            if isinstance(widget, tk.Entry):
                widget.config(state="normal", bg="white")

        # Zmiana przycisku na "Zatwierdź"
        button_confirm = row_entries["Zatwierdź"]
        button_confirm.config(text="Zatwierdź", command=lambda e=row_entries: self.confirm_address(e))


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
        for key, entry in self.static_entries.items():
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
        file_number_entry = self.file_number_entry.get()

        f = chr(first.index(folderType) + 65)
        s = chr(second.index(groupType) + 65)
        t = 0
        if s == 'A':
            t = chr(secondA.index(subGroupType) + 65)
        elif s == 'B':
            t = chr(secondB.index(subGroupType) + 65)
        elif s == 'C':
            t = chr(secondC.index(subGroupType) + 65)
        else:
            t = chr(secondD.index(subGroupType) + 65)

        # siema = self.entries['Nr_teczki'].get()

        new_file_name = f"{f}{info['Nr_teczki']}{s}{t}{file_number_entry}"

        if file_extension == ".tiff":
            process_tiff(self.file_path, info, f"{new_file_name}.tiff")
        elif file_extension == ".pdf":
            process_pdf(self.file_path, info, f"{new_file_name}.pdf")

        messagebox.showinfo("Sukces",
                            f"Tagi zostały dodane do pliku. {f} {s} {t} {info['Nr_teczki']} {file_number_entry}")

        # Wyświetlenie dynamicznych adresów
        for row_entries in self.entries:
            row_data = {key: entry.get() for key, entry in row_entries.items()}
            print("Dynamiczny adres:", row_data)

        messagebox.showinfo("Sukces", "Tagi zostały zebrane!")

    def create_text_entry(self, label_text, tag_key, row, col):
        """Tworzy pole tekstowe do wpisywania wartości tagów, z grid layoutem."""
        tk.Label(self, text=label_text).grid(row=row, column=col, padx=10, pady=5, sticky="w")
        entry = tk.Entry(self)
        entry.grid(row=row, column=col + 1, padx=10, pady=5, sticky="w")
        self.info[tag_key] = entry

    def choose_file(self):
        """Funkcja do wybierania pliku."""
        self.file_path = filedialog.askopenfilename(filetypes=[("TIFF files", "*.tiff"), ("PDF files", "*.pdf")])
        if self.file_path:
            messagebox.showinfo("Wybrano plik", f"Wybrano plik: {self.file_path}")
            threading.Thread(target=self.process_ocr, daemon=True).start()

    def process_ocr(self):
        """Funkcja do przetwarzania OCR."""
        # Uruchom OCR i uzyskaj wynik (może to potrwać kilka sekund)
        result = ocr.rozpoznaj_adresy(self.file_path)

        # Po zakończeniu OCR wywołaj funkcję do aktualizacji GUI
        self.after(0, self.update_address_fields, result)

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
