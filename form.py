import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import filedialog, messagebox
import os
import material_dictionary
import diameter_dictionary
import filename_generator
import ocr
import threading
from PIL import Image, ImageTk
from pdf2image import convert_from_path

from LabeledEntry import LabeledEntry
from LabeledOptionMenu import LabeledOptionMenu
from validate import Validator
from exif_manager import ExifManager
from datetime import datetime
import concurrent.futures

# GUI z Tkinter



class Application(TkinterDnD.Tk):

    ROW_PAD = 7
    COL_PAD = 5
    ENTRY_WIDTH = 30

    def __init__(self):
        super().__init__()
        self.listbox_material = tk.Listbox(self, height=10, width=25)
        self.listbox_diameter = tk.Listbox(self, height=10, width=25)

        self.thumbnail_label = tk.Label(self)
        self.filename_label = tk.Label(self)
        self.title("Tagowanie plików TIFF/PDF")
        self.geometry("1920x1080")

        self.file_path = ""
        self.info = {}
        self.skip_empty = 1

        self.labeled_entries = {}

        self.diameter_and_material_entries = []

        # Przycisk dodawania nowego wiersza
        self.add_button = tk.Button(self, text="Dodaj nowy", command=self.add_new_rowDM)
        self.add_button.grid(row=8, column=9, pady=10, padx=10)

        # Pierwszy wiersz z materiałem i średnicą
        self.add_new_rowDM()

        self.required_entries = []
        self.folder_required_entries = []
        self.folder_possible_entries = []


        self.data = []
        self.valid_materials = material_dictionary.get_dict()
        self.valid_diameters = diameter_dictionary.get_dict()

        self.rodzaj_przewodu_var = tk.StringVar()
        self.typ_przewodu_var = tk.StringVar()
        # self.file_number_entry = tk.Entry(self, width=30)
        # self.dir_number_entry = tk.Entry(self, width=30)

        self.folder_type_var = tk.StringVar()
        self.doc_type_var = tk.StringVar()
        self.subgroup_var = tk.StringVar()

        self.labeled_entries["Rodzaj teczki dokumentów"] = LabeledOptionMenu(self, "Rodzaj\n teczki dokumentów:", self.folder_type_var, values=["EW", "EWP", "EWS", "EKS", "KSA", "NI", "UL","N"], row=1, col=0, bind=self.update_doc_type, hide=False)
        self.labeled_entries["Typ dokumentacji"] = LabeledOptionMenu(self, "Typ\n dokumentacji:", self.doc_type_var, values=[""], row=2, col=0, hide=False)
        self.labeled_entries["Podgrupa dokumentów"] = LabeledOptionMenu(self, "Podgrupa\n dokumentów:", self.subgroup_var, values=[""], row=2, col=2, hide=False)
        # self.labeled_entries["Rodzaj przewodu"] = LabeledOptionMenu(self, "Rodzaj przewodu:", self.rodzaj_przewodu_var, values=["wodociągowa", "kanalizacyjna",
        #                                                        "wodociągowo-kanalizacyjna"], row=2, col=8)
        # self.labeled_entries["Typ przewodu"] = LabeledOptionMenu(self, "Typ przewodu:", self.typ_przewodu_var, values=["sieć", "przyłącze", "sieć i przyłącze"], row=2, col=6)

        # self.folder_type_menu = self.create_option("Rodzaj teczki dokumentów:", self.folder_type_var,
        #                                            values=["EW", "EWP", "EWS", "EKS", "KSA", "PZO", "UL", "N"], row=1,
        #                                            col=0, bind=self.update_doc_type, hide=False)
        # self.doc_type_menu = self.create_option("Typ dokumentacji:", self.doc_type_var, values=[""], row=2, col=0,
        #                                         hide=False)
        # self.subgroup_menu = self.create_option("Podgrupa dokumentów:", self.subgroup_var, values=[""], row=2, col=2,
        #                                         hide=False)
        # self.rodzaj_przewodu_menu = self.create_option("Rodzaj przewodu:", self.rodzaj_przewodu_var,
        #                                                values=["wodociągowa", "kanalizacyjna",
        #                                                        "wodociągowo-kanalizacyjna"], row=2, col=8)
        # self.typ_przewodu_menu = self.create_option("Typ przewodu:", self.typ_przewodu_var,
        #                                             values=["sieć", "przyłącze", "sieć i przyłącze"], row=2, col=6)

        # self.entries = []  # Lista na widgety do wpisywania danych
        self.dynamic_widgets = []
        self.filtered_materials = []  # List to store filtered results
        self.filtered_diameters = []  # List to store filtered results
        self.create_widgets()
#        self.bind_events()
        self.selected_index = None  # Reset selection

        self.validation_cancelled = False  # Flaga anulowania walidacji
        self.validation_thread = None  # Przechowuje wątek walidacji

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.future = None

    def on_drop(self, event):
        self.file_path = event.data
        self.display_thumbnail(self.file_path)

    def display_thumbnail(self, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.tiff' or file_extension == '.tif':
            # Obsługa pliku TIFF
            image = Image.open(file_path)
            image.thumbnail((200, 200))  # Zmniejsz obraz do miniaturki
            photo = ImageTk.PhotoImage(image)

        elif file_extension == '.pdf':
            # Obsługa pliku PDF - konwersja pierwszej strony na obraz
            images = convert_from_path(file_path, first_page=0, last_page=1)
            image = images[0]
            width, height = image.size
            new_height = int(height * 0.3)  # Ustaw wysokość na 30% oryginalnej
            cropped_image = image.crop((0, 0, width, new_height))

            # Zmniejszenie obrazu do wyświetlenia jako miniaturka
            cropped_image.thumbnail((350, 700))  # Miniaturka zachowująca szerokość
            photo = ImageTk.PhotoImage(cropped_image)

            threading.Thread(target=self.process_ocr, daemon=True).start()

        else:
            # Obsługa nieznanych typów plików
            self.thumbnail_label.config(text="Nieobsługiwany format pliku.")
            return

        # Wyświetlanie obrazu w Label
        self.thumbnail_label.config(image=photo)
        filename = os.path.basename(self.file_path)
        self.filename_label.config(text=filename)
        self.thumbnail_label.image = photo  # Zapisanie referencji, aby nie usunąć obrazu z pamięci

    def update_address_fields(self, result):

        # Czyszczenie poprzednich widgetów
        for widget_dict in self.dynamic_widgets:
            for widget in widget_dict.values():
                if isinstance(widget, tk.Widget):
                    widget.destroy()
            del widget_dict

        self.dynamic_widgets = []

        fields_dynamic = ["Ulica", "Numer_adresowy", "Obręb", "Numer_działki"]

        if result:
            self.data = result
            for i, item in enumerate(self.data):
                self.add_row(i, item, fields_dynamic)

    def add_row(self, row_index, item, fields_dynamic):
        row_entries = {}

        entry = tk.Entry(self, width=10)
        entry.grid(row=9 + row_index, column=0, padx=10, pady=5, sticky="w")
        entry.insert(0, "Gdańsk")
        row_entries["Miejscowość"] = entry
        row_entries["Miejscowość_old"] = entry.get()

        col = 1
        for field in fields_dynamic:
            if field == "Ulica":
                entry = tk.Entry(self, width=20)
            else:
                entry = tk.Entry(self, width=10)
            entry.grid(row=9 + row_index, column=col, padx=10, pady=5, sticky="w")
            entry.insert(0, item[field.split()[0]])
            row_entries[field] = entry
            row_entries[field + "_old"] = entry.get()
            col += 1

        button_validate = tk.Button(self, text="Waliduj", command=lambda e=row_entries: self.validate_address(e))
        button_validate.grid(row=9 + row_index, column=col, padx=5, pady=5)
        row_entries["Waliduj"] = button_validate

        button_confirm = tk.Button(self, text="Zatwierdź", command=lambda e=row_entries: self.confirm_address(e))
        button_confirm.grid(row=9 + row_index, column=col + 1, padx=5, pady=5)
        button_confirm.grid_remove()
        row_entries["Zatwierdź"] = button_confirm

        button_delete = tk.Button(self, text="Usuń", command=lambda e=row_entries: self.delete_row(e))
        button_delete.grid(row=9 + row_index, column=col + 2, padx=5, pady=5)
        row_entries["Usuń"] = button_delete

        self.dynamic_widgets.append(row_entries)

    def reposition_rows(self):
        """Aktualizuje pozycje dynamicznych wierszy, przestawiając je po usunięciu wiersza."""
        fields_dynamic = ["Ulica", "Numer_adresowy", "Numer_działki", "Obręb"]

        # Przestaw wszystkie pozostałe wiersze na nowe pozycje w siatce
        for i, row_entries in enumerate(self.dynamic_widgets):
            # Ustawienie pozycji "Miejscowość"
            row_entries["Miejscowość"].grid(row=9 + i, column=0, padx=10, pady=5, sticky="w")

            col = 1
            for field in fields_dynamic:
                row_entries[field].grid(row=9 + i, column=col, padx=10, pady=5, sticky="w")
                col += 1

            # Ustawienie pozycji przycisków
            row_entries["Waliduj"].grid(row=9 + i, column=col, padx=5, pady=5)
            row_entries["Zatwierdź"].grid(row=9 + i, column=col + 1, padx=5, pady=5)
            row_entries["Zatwierdź"].grid_remove()
            row_entries["Usuń"].grid(row=9 + i, column=col + 2, padx=5, pady=5)

    def add_new_row(self):
        """Funkcja dodająca nowy pusty wiersz na końcu formularza."""
        # Pusty słownik dla nowego wiersza
        fields_dynamic = ["Ulica", "Numer_adresowy", "Numer_działki", "Obręb"]
        empty_item = {field.split()[0]: "" for field in fields_dynamic}

        # Dodaj nowy wiersz do danych
        self.data.append(empty_item)

        # Dodaj nowy wiersz do dynamicznych widgetów
        self.add_row(len(self.dynamic_widgets), empty_item, fields_dynamic)

    def delete_row(self, row_entries):
        """Funkcja usuwająca wybrany wiersz i aktualizująca pozycje pozostałych."""
        # Usuń widgety z interfejsu dla usuwanego wiersza
        for widget in row_entries.values():
            if isinstance(widget, tk.Widget):
                widget.grid_forget()  # Usuwa widget z widoku, ale nie niszczy go

        # Znajdź indeks usuwanego wiersza
        row_index = None
        for i, widget_dict in enumerate(self.dynamic_widgets):
            if widget_dict == row_entries:
                row_index = i
                break

        if row_index is not None:
            # Usuń wiersz z danych i dynamicznych widgetów
            del self.data[row_index]
            self.dynamic_widgets.remove(row_entries)

            # Przestaw pozostałe wiersze
            self.reposition_rows()

    def filter_materials(self, typed_text):
        return [material for material in self.valid_materials if
                any(word.lower().startswith(typed_text.lower()) for word in material.split())]

    def filter_diameters(self, typed_text):
        try:
            typed_number = int(typed_text)
            return [diameter for diameter in self.valid_diameters if str(diameter).startswith(str(typed_number))]
        except ValueError:
            return []  # Jeśli wpisany tekst nie może być przekonwertowany na liczbę

    def show_material_listbox(self, event):
        typed_text = self.labeled_entries["Materiał"].get_value()
        self.listbox_material.delete(0, tk.END)

        if typed_text:
            self.filtered_materials = self.filter_materials(typed_text)
            for item in self.filtered_materials:
                self.listbox_material.insert(tk.END, item)
        else:
            sorted_materials = sorted(self.valid_materials)
            for item in sorted_materials:
                self.listbox_material.insert(tk.END, item)

        self.update_listbox_height(self.listbox_material)
        self.update_material_entry_background()
        self.listbox_material.grid()

    def show_diameter_listbox(self, event):
        typed_text = self.labeled_entries["Średnica"].get_value()
        self.listbox_diameter.delete(0, tk.END)

        if typed_text:
            self.filtered_diameters = self.filter_diameters(typed_text)
            for item in self.filtered_diameters:
                self.listbox_diameter.insert(tk.END, item)
        else:
            sorted_diameters = sorted(self.valid_diameters)
            for item in sorted_diameters:
                self.listbox_diameter.insert(tk.END, item)

        self.update_listbox_height(self.listbox_diameter)
        self.update_diameter_entry_background()
        self.listbox_diameter.grid()

    def on_click_outside(self, event):
        # Sprawdzenie, czy klucz "Materiał" istnieje w labeled_entries
        if "Materiał" in self.labeled_entries and event.widget not in [self.labeled_entries["Materiał"].get_entry(),
                                                                       self.listbox_material]:
            self.listbox_material.grid_remove()
            self.check_entry(self.labeled_entries["Materiał"], self.valid_materials)

        # Sprawdzenie, czy klucz "Średnica" istnieje w labeled_entries
        if "Średnica" in self.labeled_entries and event.widget not in [self.labeled_entries["Średnica"].get_entry(),
                                                                       self.listbox_diameter]:
            self.listbox_diameter.grid_remove()
            self.check_entry(self.labeled_entries["Średnica"], self.valid_diameters)

        # Sprawdzenie kluczy dat w labeled_entries
        for date_key in ["Data projektu","Data uzgodnienia","Data dokumentu"]:
            if date_key in self.labeled_entries:
                if event.widget not in [self.labeled_entries[date_key].get_entry()]:
                    self.check_entry_dates(self.labeled_entries[date_key])

    def highlight_selection(self, event, listbox_widget):
        index = listbox_widget.nearest(event.y)
        if index != self.selected_index:
            self.selected_index = index
            listbox_widget.selection_clear(0, tk.END)
            listbox_widget.selection_set(index)

    def confirm_selection(self, entry_widget, listbox_widget, entryName):
        if self.selected_index is not None:
            selected = listbox_widget.get(self.selected_index)
            entry_widget.insert(selected)
            listbox_widget.grid_remove()  # Hide Listbox after selection
            self.selected_index = None  # Reset selection
            if entryName == 'material':
                self.update_material_entry_background()
            else:
                self.update_diameter_entry_background()

    def update_entry_background(self, entry_widget, valid_items, filtered_items, isString):
        typed_text = entry_widget.get_value()

        if typed_text != '' and typed_text != '1':
            if isString:
                if typed_text in valid_items:
                    entry_widget.config_entry(bg="lightgreen")
                elif any(typed_text.lower() in item.lower() for item in filtered_items):
                    entry_widget.config_entry(bg="lightyellow")
                else:
                    entry_widget.config_entry(bg="lightcoral")
            else:
                try:
                    typed_diameter = int(typed_text)
                    if typed_diameter in valid_items:
                        entry_widget.config_entry(bg="lightgreen")
                    else:
                        entry_widget.config_entry(bg="lightcoral")
                except ValueError:
                    # Jeśli wprowadzone dane nie są liczbą
                    entry_widget.config_entry(bg="lightcoral")

    def check_entry(self, labeledEntry, dictionary):
        typed_text = labeledEntry.get_value()
        if typed_text != ''and typed_text not in dictionary and labeledEntry.get_color('bg') != "lightgreen":
            self.flash_entry(labeledEntry)

    def check_entry_dates(self, labeledEntry):
        if labeledEntry.get_value() != '':
            try:
                valid_date = datetime.strptime(labeledEntry.get_value(), '%d-%m-%Y')
                if valid_date > datetime.now():
                    self.flash_entry(labeledEntry)

            except ValueError:
                self.flash_entry(labeledEntry)

    def flash_entry(self, labeledEntry):
        if labeledEntry:
            original_color = labeledEntry.get_color('bg')
            labeledEntry.config_entry(bg="red")

            # Sprawdzamy, czy obiekt nadal istnieje po 500ms
            def restore_color():
                if labeledEntry and labeledEntry.label.winfo_exists():  # Sprawdzamy, czy widget nadal istnieje
                    labeledEntry.config_entry(bg="white")

            self.after(500, restore_color)

    def update_listbox_height(self, listbox_widget):
        num_items = listbox_widget.size()
        listbox_widget.config(height=min(num_items, 5))

    def create_file_selection_widgets(self):
        tk.Label(self, text="Wybierz plik\nTIFF lub PDF:").grid(row=0, column=0, pady=5, sticky="w")
        tk.Button(self, text="Wybierz plik", command=self.choose_file).grid(row=0, column=1, pady=5,sticky="w")

    def create_file_drop_widget(self):
        self.drop_label = tk.Label(self,
                                   text="Przeciągnij plik tutaj",
                                   bg="lightgray",  # kolor tła
                                   fg="blue",  # kolor tekstu
                                   highlightbackground="red",  # kolor ramki
                                   highlightthickness=2,  # grubość ramki
                                   padx=20, pady=20)  # odstępy wewnętrzn
        self.drop_label.grid(row=0, column=3, padx=10, pady=5)

        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.on_drop)

        self.thumbnail_label.grid(row=0, column=5, padx=10, pady=5)
        self.filename_label.grid(row=0, column=6, padx=10, pady=5)

    def create_option(self, label_text, option_value, values, row, col, bind = None, hide = False):
        lab = tk.Label(self, text=label_text)
        lab.grid(row=row, column=col, padx=self.COL_PAD, pady=self.ROW_PAD, sticky="w")

        if bind:
            option_menu = tk.OptionMenu(self, option_value, *values, command=bind)
        else:
            option_menu = tk.OptionMenu(self, option_value, *values)
        option_menu.grid(row=row, column=col + 1, padx=self.COL_PAD, pady=self.ROW_PAD, sticky="w")
        if hide:
            option_menu.grid_remove()
            lab.grid_remove()
        return option_menu

    def createAdresLabels(self):
        tk.Label(self, text="Adresy:").grid(row=7, column=0, pady=5, sticky="w")
        tk.Label(self, text="Miasto:").grid(row=8, column=0, pady=20, sticky="w")
        tk.Label(self, text="Ulica:").grid(row=8, column=1, pady=20, sticky="w")
        tk.Label(self, text="Numer\n adresowy:").grid(row=8, column=2, pady=20, sticky="w")
        tk.Label(self, text="Numer\n obrębu:").grid(row=8, column=3, pady=20, sticky="w")
        tk.Label(self, text="Numer\n działki:").grid(row=8, column=4, pady=20, sticky="w")
        tk.Label(self, text="Średnica:").grid(row=8, column=8, pady=20, sticky="w")
        tk.Label(self, text="Materiał:").grid(row=8, column=10, pady=20, sticky="w")

    def create_widgets(self):

        self.create_file_selection_widgets()
        self.create_file_drop_widget()

        self.createAdresLabels()

        self.listbox_material.grid(row=11, column=9, padx=self.COL_PAD, pady=self.ROW_PAD)
        self.listbox_material.grid_remove()
        self.listbox_diameter.grid(row=11, column=11, padx=self.COL_PAD, pady=self.ROW_PAD)
        self.listbox_diameter.grid_remove()

        tk.Button(self, text="Dodaj nowy", command=self.add_new_row).grid(row=8, column=6, padx=5, pady=5)
        tk.Button(self, text="Dodaj tagi", command=self.apply_tags).grid(row=7, column=8, columnspan=4, pady=20)

    def create_folder_entries(self):
        if "Numer uzgodnienia" not in self.labeled_entries:
            self.labeled_entries["Numer uzgodnienia"] = LabeledEntry(self, "Numer uzgodnienia", 1, 4,entry_width=15)
        self.labeled_entries["Numer uzgodnienia"].config_entry(highlightbackground="black", highlightthickness=0)

        if "Data uzgodnienia" not in self.labeled_entries or not self.labeled_entries["Data uzgodnienia"]:
            self.labeled_entries["Data uzgodnienia"] = LabeledEntry(self, "Data uzgodnienia", 1, 6,
                                                                    bind=format_date_entry)
        self.labeled_entries["Data uzgodnienia"].config_entry(highlightbackground="black", highlightthickness=0)

        if "Data projektu" not in self.labeled_entries or not self.labeled_entries["Data projektu"]:
            self.labeled_entries["Data projektu"] = LabeledEntry(self, "Data projektu", 1, 8, bind=format_date_entry)
        self.labeled_entries["Data projektu"].config_entry(highlightbackground="black", highlightthickness=0)

        if "Inwestor" not in self.labeled_entries or not self.labeled_entries["Inwestor"]:
            self.labeled_entries["Inwestor"] = LabeledEntry(self, "Inwestor", 1, 10,entry_width=15)
        self.labeled_entries["Inwestor"].config_entry(highlightbackground="black", highlightthickness=0)

       # self.bind_events()

    def update_entries_group(self, value):

        self.folder_required_entries.clear()
        self.folder_possible_entries.clear()

        if value == 'EW' or value == 'UL':
            self.create_folder_entries()
            self.folder_required_entries.append("Numer uzgodnienia")
            self.folder_required_entries.append("Data projektu")
            self.folder_required_entries.append("Data uzgodnienia")
            self.folder_required_entries.append("Inwestor")
        elif value == 'N':
            self.create_folder_entries()
            self.folder_possible_entries.append("Numer uzgodnienia")
            self.folder_possible_entries.append("Data projektu")
            self.folder_possible_entries.append("Data uzgodnienia")
            self.folder_possible_entries.append("Inwestor")
        elif value == 'KSA' or value == 'UL':
            if "Inwestor" not in self.labeled_entries or not self.labeled_entries["Inwestor"]:
                self.labeled_entries["Inwestor"] = LabeledEntry(self, "Inwestor", 1, 10,entry_width=15)
            self.labeled_entries["Inwestor"].config_entry(highlightbackground="black", highlightthickness=0)
            self.folder_required_entries.append("Inwestor")

        self.labeled_entries["Numer teczki"] = LabeledEntry(self, "Numer teczki", 1, 2,
                                                            bind=lambda event: format_number(5, self.labeled_entries[
                                                                "Numer teczki"].entry))

        self.folder_required_entries.append("Numer teczki")
        self.folder_required_entries.append("Rodzaj teczki dokumentów")
        self.folder_required_entries.append("Typ dokumentacji")
        self.folder_required_entries.append("Podgrupa dokumentów")

        for key, labeledEntry in list(self.labeled_entries.items()):
                if key not in self.folder_required_entries:
                    if key not in self.folder_possible_entries:
                        labeledEntry.destroy()
                        self.labeled_entries.pop(key)


#
        for key in self.folder_required_entries:
            self.labeled_entries[key].config_entry(highlightbackground="blue", highlightthickness=1)

    def create_file_entries(self, value):
        if value == "Materiał":
            if "Materiał" not in self.labeled_entries or not self.labeled_entries["Materiał"]:
                self.labeled_entries["Materiał"] = LabeledEntry(self, "Materiał", 10, 8)
                self.bind_materials()
        if value == "Średnica":
            if "Średnica" not in self.labeled_entries or not self.labeled_entries["Średnica"]:
                self.labeled_entries["Średnica"] = LabeledEntry(self, "Średnica", 10, 10)
                self.bind_diameters()
        if value == "Rodzaj przewodu":
            if "Rodzaj przewodu" not in self.labeled_entries or not self.labeled_entries["Rodzaj przewodu"]:
                self.labeled_entries["Rodzaj przewodu"] = LabeledOptionMenu(
                    self, "Rodzaj przewodu:", self.rodzaj_przewodu_var,
                    values=["wodociągowa", "kanalizacyjna", "wodociągowo-kanalizacyjna"],
                    row=2, col=8
                )
        if value == "Typ przewodu":
            if "Typ przewodu" not in self.labeled_entries or not self.labeled_entries["Typ przewodu"]:
                self.labeled_entries["Typ przewodu"] = LabeledOptionMenu(
                    self, "Typ przewodu:", self.typ_przewodu_var,
                    values=["sieć", "przyłącze", "sieć i przyłącze"],
                    row=2, col=6
                )
        if value == "Data dokumentu":
            if "Data dokumentu" not in self.labeled_entries or not self.labeled_entries["Data dokumentu"]:
                self.labeled_entries["Data dokumentu"] = LabeledEntry(self, "Data dokumentu", 2, 10, bind=format_date_entry)

        if value == "Numer dokumentu":
            if "Numer dokumentu" not in self.labeled_entries or not self.labeled_entries["Numer dokumentu"]:
                self.labeled_entries["Numer dokumentu"] = LabeledEntry(self, "Numer dokumentu", 3, 10,entry_width=15)

        if value == "Numer inwentarzowy":
            if "Numer inwentarzowy" not in self.labeled_entries or not self.labeled_entries["Numer inwentarzowy"]:
                self.labeled_entries["Numer inwentarzowy"] = LabeledEntry(self, "Numer inwentarzowy", 3, 6,entry_width=15)

        if value == "Numer księgi inwentarzowej":
            if "Numer księgi inwentarzowej" not in self.labeled_entries or not self.labeled_entries["Numer księgi inwentarzowej"]:
                self.labeled_entries["Numer księgi inwentarzowej"] = LabeledEntry(self, "Numer księgi inwentarzowej", 3, 8,entry_width=15)

        if value == "Numer teczki EW":
            if "Numer teczki EW" not in self.labeled_entries or not self.labeled_entries["Numer teczki EW"]:
                self.labeled_entries["Numer teczki EW"] = LabeledEntry(self, "Numer teczki EW", 3, 8)

        self.bind_events()

    def update_entries_file1(self, value):
        self.required_entries.clear()

        for key, labeledEntry in list(self.labeled_entries.items()):
                    if key not in self.folder_required_entries:
                        if key not in self.folder_possible_entries:
                            labeledEntry.destroy()
                            self.labeled_entries.pop(key)

        if self.folder_type_var.get() == 'NI':
            entryListNI = filename_generator.get_int_list(self.folder_type_var.get(), self.doc_type_var.get(), value)

            fieldsNI = [
                ("Numer inwentarzowy", entryListNI[0]),
                ("Numer księgi inwentarzowej", entryListNI[1]),
                ("Numer teczki EW", entryListNI[2]),
                ("Data dokumentu", entryListNI[3]),
                ("Numer dokumentu", 2),
            ]

            for field, value in fieldsNI:
                if value != 0:
                    self.create_file_entries(field)
                    if value == 2:
                        self.required_entries.append(field)
        else:

            entryList = filename_generator.get_int_list(self.folder_type_var.get(), self.doc_type_var.get(), value)

            fields = [
                ("Materiał", entryList[1]),
                ("Średnica", entryList[2]),
                ("Rodzaj przewodu", entryList[3]),
                ("Typ przewodu", entryList[4]),
                ("Data dokumentu", entryList[5]),
            ]

            for field, value in fields:
                self.process_field(field, value)




        if self.folder_type_var.get() == 'KSA' or self.folder_type_var.get() == 'UL':
            self.create_file_entries("Numer dokumentu")
            self.required_entries.append("Numer dokumentu")

        for key in self.required_entries:
            self.labeled_entries[key].config_entry(highlightbackground="blue", highlightthickness=1)

    def process_field(self, field, value):
        if value != 0:
            self.create_file_entries(field)
            if value == 2:
                self.required_entries.append(field)
            elif isinstance(value, str):
                if field == "Rodzaj przewodu":
                     self.rodzaj_przewodu_var.set(value)
                elif field == "Typ przewodu":
                     self.typ_przewodu_var.set(value)
                self.labeled_entries[field].config_entry(state="disabled")



    def bind_materials(self):
        # Materiały
        self.labeled_entries["Materiał"].bind('<KeyRelease>', self.show_material_listbox)
        self.labeled_entries["Materiał"].bind('<Button-1>', self.show_material_listbox)
        self.labeled_entries["Materiał"].bind('<KeyRelease>', self.show_material_listbox)
        self.labeled_entries["Materiał"].bind('<Button-1>', self.show_material_listbox)
        self.listbox_material.bind('<ButtonRelease-1>', lambda event: self.highlight_selection(event, self.listbox_material))
        self.listbox_material.bind('<Return>', self.confirm_material_selection)
        self.listbox_material.bind('<Double-Button-1>', self.confirm_material_selection)

    def bind_diameters(self):
        # Średnice
        self.labeled_entries["Średnica"].bind('<KeyRelease>', self.show_diameter_listbox)
        self.labeled_entries["Średnica"].bind('<Button-1>', self.show_diameter_listbox)
        self.labeled_entries["Średnica"].bind('<KeyRelease>', self.show_diameter_listbox)
        self.labeled_entries["Średnica"].bind('<Button-1>', self.show_diameter_listbox)
        self.listbox_diameter.bind('<ButtonRelease-1>', lambda event: self.highlight_selection(event, self.listbox_diameter))
        self.listbox_diameter.bind('<Return>', self.confirm_diameter_selection)
        self.listbox_diameter.bind('<Double-Button-1>', self.confirm_diameter_selection)

    def bind_events(self):




        self.bind('<Button-1>', self.on_click_outside)

    def validate_address(self, row_entries):
        """Rozpocznij proces walidacji i zmień przycisk na 'Anuluj'."""
        if not self.future or self.future.done():
            # Rozpoczęcie walidacji, zmień przycisk na 'Anuluj'
            row_entries["Waliduj"].config(text="Anuluj", command=lambda: self.cancel_validation(row_entries))
            self.future = self.executor.submit(self._validate_address_thread, row_entries)
        else:
            pass  # Nic nie rób, jeśli walidacja jest w toku

    def cancel_validation(self, row_entries):
        """Anuluj proces walidacji."""
        if self.future:
            self.future.cancel()  # Próba anulowania zadania
            row_entries["Waliduj"].config(text="Waliduj", command=lambda: self.validate_address(row_entries))
            print("Proces walidacji został anulowany.")

    def _validate_address_thread(self, row_entries):
        try:
            #result = {key: widget.get() for key, widget in row_entries.items() if isinstance(widget, tk.Entry)}
            result = {}
            for key, widget in row_entries.items():
                if isinstance(widget, tk.Entry):  # Sprawdzamy, czy widget jest polem Entry
                    result[key] = widget.get()  # Pobieramy wartość z pola Entry
                    widget.config(highlightbackground="black", highlightthickness=0)

            ulica = result.get("Ulica")
            numer_adresowy = result.get("Numer_adresowy")
            numer_dzialki = result.get("Numer_działki")
            obreb = result.get("Obręb")

            gmIdTeryt = "2261011" #Id gminy Gdańsk

            znaleziona_ulica = Validator.znajdz_ulice(ulica)
            if self.validation_cancelled:
                return  # Wyjdź z wątku, jeśli walidacja została anulowana

            if znaleziona_ulica:
                row_entries["Ulica"].config(highlightbackground="green", highlightthickness=2)

                if znaleziona_ulica[1]:
                    row_entries["Ulica"].delete(0, tk.END)
                    row_entries["Ulica"].insert(0, znaleziona_ulica[1])

                if znaleziona_ulica[0] and numer_adresowy != "brak":
                    adresy_data = Validator.pobierz_adresy(znaleziona_ulica[0])

                    if not adresy_data:
                        messagebox.showwarning("Błąd połączenia", "Nie można zweryfikować poprawności numeru adresowego")
                    else:
                        adres = Validator.znajdz_adres(numer_adresowy, adresy_data)
                        if not adres:
                            messagebox.showwarning("Błąd", "Nie znaleziono pasującego numeru dla podanej ulicy")
                            row_entries["Numer_adresowy"].config(highlightbackground="red", highlightthickness=2)
                        else:
                            gmIdTeryt = adres['adres']['gmIdTeryt']
                            row_entries["Numer_adresowy"].config(highlightbackground="green", highlightthickness=2)
                else:
                    row_entries["Numer_adresowy"].config(highlightbackground="yellow", highlightthickness=2)
            else:
                row_entries["Ulica"].config(highlightbackground="red", highlightthickness=2)

            if Validator.sprawdz_dzialke(gmIdTeryt, obreb, numer_dzialki):
                row_entries["Obręb"].config(highlightbackground="green", highlightthickness=2)
                row_entries["Numer_działki"].config(highlightbackground="green", highlightthickness=2)
            else:
                row_entries["Obręb"].config(highlightbackground="red", highlightthickness=2)
                row_entries["Numer_działki"].config(highlightbackground="red", highlightthickness=2)

            row_entries["Waliduj"].after(0, lambda: row_entries["Waliduj"].config(text="Waliduj",
                                                                                  command=lambda: self.validate_address(
                                                                                      row_entries)))

            self.update_button_states(row_entries)
        except Exception as e:
            messagebox.showerror("Błąd walidacji", f"Wystąpił problem: {e}")
            row_entries["Waliduj"].after(0, lambda: row_entries["Waliduj"].config(text="Waliduj",
                                                                                  command=lambda: self.validate_address(
                                                                                      row_entries)))

    @staticmethod
    def update_button_states(row_entries):
        button_confirm = row_entries["Zatwierdź"]
        button_validate = row_entries["Waliduj"]
        button_confirm.grid()
        button_confirm.config(state="normal", bg="white")
        button_validate.config(bg="SystemButtonFace")
        # Przywróć stare wartości jako punkt odniesienia
        for key, widget in row_entries.items():
            if isinstance(widget, tk.Entry):
                row_entries[key + "_old"] = widget.get()  # Aktualizujemy wartość początkową

    def confirm_address(self, row_entries):
        try:
            for key, widget in row_entries.items():
                if isinstance(widget, tk.Entry):
                    if widget.get() != row_entries[key + "_old"]:
                        row_entries["Zatwierdź"].config(state="disabled", bg="lightgray")
                        row_entries["Waliduj"].config(bg="yellow")
                        return

            for key, widget in row_entries.items():
                if isinstance(widget, tk.Entry):
                    widget.config(state="disabled", bg="lightgray")

                row_entries["Zatwierdź"].config(text="Edytuj", command=lambda e=row_entries: self.edit_address(e))
        except Exception as e:
            messagebox.showerror("Błąd zatwierdzania", f"Wystąpił problem: {e}")

    def edit_address(self, row_entries):
        try:
            for key, widget in row_entries.items():
                if isinstance(widget, tk.Entry):
                    widget.config(state="normal", bg="white")

            row_entries["Zatwierdź"].config(text="Zatwierdź", command=lambda e=row_entries: self.confirm_address(e))
        except Exception as e:
            messagebox.showerror("Błąd edytowania", f"Wystąpił problem: {e}")

    def apply_tags(self):
        # try:
            if not self.file_path:
                messagebox.showwarning("Brak pliku", "Nie wybrano pliku do tagowania.")
                return

            # Zbieranie danych z pól
            file_extension = os.path.splitext(self.file_path)[1].lower()
            info = {}
            info['Rodzaj sieci'] = self.rodzaj_sieci_var.get()
            info['Nr_teczki'] = self.dir_number_entry.get()
            info['Material'] = self.material_entry.get()
            info['Srednica'] = self.diameter_entry.get()
            info['Dlugosc'] = self.lenght_entry.get()

            address_structure = create_address_structure(self.dynamic_widgets)
            formatted_result = format_address_structure(address_structure)

            folderType = self.folder_type_var.get()
            groupType = self.doc_type_var.get()
            subGroupType = self.subgroup_var.get()
            file_number_entry = self.file_number_entry.get()

            # Sprawdzanie wymaganych pól
            required_fields = {
                self.dir_number_entry: self.dir_number_entry.get(),
                self.file_number_entry: self.file_number_entry.get(),
                self.folder_type_menu: folderType,
                self.doc_type_menu: groupType,
                self.subgroup_menu: subGroupType
            }

            # Sprawdzenie, czy któreś z wymaganych pól nie jest puste
            isMissing = False
            for entry, value in required_fields.items():
                if value == '':
                    isMissing = True
                    self.flash_entry(entry)  # Zmieniamy kolor pola na czerwony
            if isMissing:
                return

            # Generowanie nowej nazwy pliku
            f, s, t = filename_generator.generate_file_name_tags(folderType, groupType, subGroupType)
            new_file_name = f"{f}{info['Nr_teczki']}{s}{t}{file_number_entry}"

            # Przetwarzanie pliku w zależności od formatu
            if file_extension == ".tiff":
                info['Artist'] = formatted_result
                ExifManager.process_tiff(self.file_path, info, f"{new_file_name}.tiff")
            elif file_extension == ".pdf":
                info['Adres'] = formatted_result
                ExifManager.process_pdf(self.file_path, info, f"{new_file_name}.pdf")
            else:
                messagebox.showerror("Błąd formatu", "Niewłaściwy format pliku. Wybierz TIFF lub PDF.")

            #todo Wyczyść wszystkie pola po zakończeniu operacji

            #self.rodzaj_sieci_var.set('')  # Wyczyść zmienną rodzaju sieci
            file_number_text = self.file_number_entry.get()
            new_file_number = int(file_number_text) + 1

            self.file_number_entry.delete(0, 'end')  # Wyczyść numer pliku
            self.file_number_entry.insert(0, f"{new_file_number:03d}")

    def choose_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf"),("TIFF files", "*.tiff")])
        if self.file_path:
            self.display_thumbnail(self.file_path)

    def process_ocr(self):
        try:
            result = ocr.rozpoznaj_adresy(self.file_path)
            self.after(0, self.update_address_fields, result)
        except Exception as e:
            messagebox.showerror("Błąd OCR", f"Wystąpił problem podczas przetwarzania OCR: {e}")

    def update_doc_type(self, value):
            self.doc_type_var.set('')  # Resetowanie wyboru w `Typ dokumentacji`
            self.subgroup_var.set('')  # Resetowanie wyboru w `Podgrupa dokumentów`


            if self.labeled_entries["Typ dokumentacji"]:
                self.labeled_entries["Typ dokumentacji"].clear()

            if self.labeled_entries["Podgrupa dokumentów"]:
                self.labeled_entries["Podgrupa dokumentów"].clear()


            self.update_entries_group(value)
            doc_type_options = filename_generator.get_group(value)

            for option in doc_type_options:
                if "Typ dokumentacji" in self.labeled_entries:
                    self.labeled_entries["Typ dokumentacji"].get_menu().add_command(label=option,
                                                       command=tk._setit(self.doc_type_var, option, self.update_subgroup))

    def update_subgroup(self, value):
        self.subgroup_var.set('')  # Resetowanie wyboru w `Podgrupa dokumentów`


        for key, labeledEntry in list(self.labeled_entries.items()):
                    if key not in self.folder_required_entries:
                        if key not in self.folder_possible_entries:
                            labeledEntry.destroy()
                            self.labeled_entries.pop(key)

        if"Podgrupa dokumentów" in self.labeled_entries:
            self.labeled_entries["Podgrupa dokumentów"].clear()
        sub_group_value = self.labeled_entries["Rodzaj teczki dokumentów"].get_value()
        subgroup_options = filename_generator.get_subgroup(sub_group_value,value)
        for option in subgroup_options:
            self.labeled_entries["Podgrupa dokumentów"].get_menu().add_command(label=option, command=tk._setit(self.subgroup_var, option, self.update_sub_subgroup))

    def update_sub_subgroup(self, value, *args):
        self.update_entries_file1(value)

    def confirm_material_selection(self, event=None):
        self.confirm_selection(self.labeled_entries["Materiał"], self.listbox_material, 'material')

    def update_material_entry_background(self):
        self.update_entry_background(self.labeled_entries["Materiał"], self.valid_materials, self.filtered_materials, True)

    def confirm_diameter_selection(self, event=None):
        self.confirm_selection(self.labeled_entries["Średnica"], self.listbox_diameter, 'diameter')

    def update_diameter_entry_background(self):
        self.update_entry_background(self.labeled_entries["Średnica"], self.valid_diameters, self.filtered_diameters, False)

    def add_new_rowDM(self):
        """Dodaje nowy wiersz z polami dla materiału i średnicy"""
        row_index = len(self.diameter_and_material_entries) + 1

        # Stwórz pola dla materiału i średnicy
        material_entry = tk.Entry(self)
        material_entry.grid(row = row_index + 8, column = 10, padx=10, pady=5)
        diameter_entry = tk.Entry(self)
        diameter_entry.grid(row = row_index + 8, column = 8, padx=10, pady=5)

        # Przycisk do usuwania tego wiersza
        delete_button = tk.Button(self, text="Usuń", command=lambda idx=row_index-1: self.delete_rowDM(idx))
        delete_button.grid(row=row_index + 8, column=12, padx=10, pady=5)

        # Przechowuj wiersz w liście
        self.diameter_and_material_entries.append({
            "material": material_entry,
            "diameter": diameter_entry,
            "delete_button": delete_button
        })

    def delete_rowDM(self, index):
        """Usuwa dany wiersz na podstawie indeksu"""
        row_entries = self.diameter_and_material_entries[index]

        # Ukryj i usuń widgety
        row_entries["material"].grid_remove()
        row_entries["diameter"].grid_remove()
        row_entries["delete_button"].grid_remove()

        # Usuń wiersz z listy
        self.diameter_and_material_entries.pop(index)

        # Przestaw pozostałe wiersze i zaktualizuj ich przyciski
        self.reposition_rowsDM()

    def reposition_rowsDM(self):
        """Przestawia pozostałe wiersze po usunięciu jednego z nich i aktualizuje ich indeksy"""
        for i, row_entries in enumerate(self.diameter_and_material_entries):
            row_index = i + 9
            row_entries["material"].grid(row=row_index, column=10, padx=10, pady=5, sticky="w")
            row_entries["diameter"].grid(row=row_index, column=8, padx=10, pady=5, sticky="w")

            # Aktualizacja przycisku "Usuń", by używał nowego indeksu
            row_entries["delete_button"].config(command=lambda idx=i: self.delete_rowDM(idx))
            row_entries["delete_button"].grid(row=row_index, column=12, padx=10, pady=5)

def format_number(max_digits, number_entry):
        try:
            current_value = number_entry.get()

            if current_value.isdigit():
                formatted_value = current_value.lstrip('0') or '0'

                if len(formatted_value) < max_digits:
                    formatted_value = formatted_value.zfill(max_digits)
                elif len(formatted_value) > max_digits:
                    formatted_value = formatted_value[-max_digits:]

                number_entry.delete(0, tk.END)
                number_entry.insert(0, formatted_value)
            elif current_value == "":
                return
            else:
                number_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Błąd formatowania", f"Wystąpił problem: {e}")

def format_date_entry(event):
    entry = event.widget
    current_value = entry.get()

    # Usuń wszystko, co nie jest cyfrą lub myślnikiem
    current_value = ''.join([char for char in current_value if char.isdigit() or char == '-'])

    # Dodaj myślniki w odpowiednich miejscach
    if len(current_value) == 2 and current_value[1] != '-':
        current_value += '-'
    if len(current_value) == 5 and current_value[4] != '-':
        current_value += '-'

    # Ogranicz długość wpisu do 10 znaków
    if len(current_value) > 10:
        current_value = current_value[:10]

    # Ustaw zaktualizowaną wartość w polu Entry
    entry.delete(0, tk.END)
    entry.insert(0, current_value)

def create_address_structure(rows):
    address_tree = {}  # Główna struktura przechowująca dane

    for row in rows:
        city = row['Miejscowość'].get()
        street = row['Ulica'].get()
        number = row['Numer_adresowy'].get()
        district = row['Obręb'].get()
        plot = row['Numer_działki'].get()

        # Sprawdzenie, czy miasto jest już w drzewie
        if city not in address_tree:
            address_tree[city] = {}

        # Sprawdzenie, czy ulica jest już w danym mieście
        if street not in address_tree[city]:
            address_tree[city][street] = {}

        # Sprawdzenie, czy numer adresowy jest już dla danej ulicy
        if number not in address_tree[city][street]:
            address_tree[city][street][number] = {}

        # Sprawdzenie, czy obręb jest już dla danego numeru
        if district not in address_tree[city][street][number]:
            address_tree[city][street][number][district] = []

        # Dodanie działki, jeśli jej jeszcze nie ma
        if plot not in address_tree[city][street][number][district]:
            address_tree[city][street][number][district].append(plot)

    return address_tree

def format_address_structure(address_structure):
    formatted_output = []

    for city, streets in address_structure.items():
        city_part = city  # Miejscowość
        street_parts = []

        for street, numbers in streets.items():
            street_part = '!' + street  # Ulica

            number_parts = []
            for number, districts in numbers.items():
                number_part = '#' + number  # Numer_adresowy

                district_parts = []
                for district, plots in districts.items():
                    district_part = '&' + district  # Obręb

                    plot_parts = '@' + '@'.join(plots)  # Numer_działki

                    district_parts.append(district_part + plot_parts)

                number_parts.append(number_part + ''.join(district_parts))

            street_parts.append(street_part + ''.join(number_parts))

        formatted_output.append(city_part + ''.join(street_parts))

    return ';'.join(formatted_output)

def validate_entry():
    messagebox.showinfo("Sukces", "Tag dodany pomyślnie!")

app = Application()
app.mainloop()
