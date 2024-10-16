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
        self.listbox_material = tk.Listbox(self, height=10, width=50)
        self.listbox_diameter = tk.Listbox(self, height=10, width=50)
        self.material_entry = tk.Entry(self, width=self.ENTRY_WIDTH)
        self.lenght_entry = tk.Entry(self, width=self.ENTRY_WIDTH)
        self.diameter_entry = tk.Entry(self, width=self.ENTRY_WIDTH)
        self.invesor_entry = tk.Entry(self, width=self.ENTRY_WIDTH)
        self.numer_uzgodnienia_entry = tk.Entry(self, width=self.ENTRY_WIDTH)
        self.data_uzgodnienia_entry = tk.Entry(self, width=self.ENTRY_WIDTH)
        self.data_projektu_entry = tk.Entry(self, width=self.ENTRY_WIDTH)
        self.data_dokumentu_entry = tk.Entry(self, width=self.ENTRY_WIDTH)

        self.thumbnail_label = tk.Label(self)
        self.filename_label = tk.Label(self)
        self.title("Tagowanie plików TIFF/PDF")
        self.geometry("1920x1080")

        self.file_path = ""
        self.info = {}
        self.skip_empty = 1

        self.required_entries = []
        self.folder_required_entries = []

        self.data = []
        self.valid_materials = material_dictionary.get_dict()
        self.valid_diameters = diameter_dictionary.get_dict()

        self.rodzaj_przewodu_var = tk.StringVar()
        self.typ_przewodu_var = tk.StringVar()
        self.file_number_entry = tk.Entry(self, width=30)
        self.dir_number_entry = tk.Entry(self, width=30)

        self.folder_type_var = tk.StringVar()
        self.doc_type_var = tk.StringVar()
        self.subgroup_var = tk.StringVar()

        self.folder_type_menu = self.create_option("Rodzaj teczki dokumentów:", self.folder_type_var, values=["EW", "EWP", "EWS", "EKS", "KSA", "PZO", "UL","N"], row=1, col=5, bind=self.update_doc_type, hide=False)
        self.doc_type_menu = self.create_option("Typ dokumentacji:",  self.doc_type_var, values=[""], row=1, col=7, hide=False)
        self.subgroup_menu = self.create_option("Podgrupa dokumentów:", self.subgroup_var, values=[""], row=1, col=9, hide=False)
        self.rodzaj_przewodu_menu = self.create_option("Rodzaj przewodu:", self.rodzaj_przewodu_var, values=["wodociągowa", "kanalizacyjna", "wodociągowo-kanalizacyjna"], row=2, col=7)
        self.typ_przewodu_menu = self.create_option("Typ przewodu:", self.typ_przewodu_var, values=["sieć", "przyłącze", "sieć i przyłącze"], row=3, col=7)

        self.entries = []  # Lista na widgety do wpisywania danych
        self.dynamic_widgets = []
        self.filtered_materials = []  # List to store filtered results
        self.filtered_diameters = []  # List to store filtered results
        self.create_widgets()
        self.bind_events()
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

        entry = tk.Entry(self, width=20)
        entry.grid(row=9 + row_index, column=0, padx=10, pady=5, sticky="w")
        entry.insert(0, "Gdańsk")
        row_entries["Miejscowość"] = entry
        row_entries["Miejscowość_old"] = entry.get()

        col = 1
        for field in fields_dynamic:
            entry = tk.Entry(self, width=20)
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
        typed_text = self.material_entry.get()
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
        typed_text = self.diameter_entry.get()
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
        if event.widget not in [self.material_entry, self.listbox_material]:
            self.listbox_material.grid_remove()
            self.check_entry(self.material_entry, self.valid_materials)
        if event.widget not in [self.diameter_entry, self.listbox_diameter]:
            self.listbox_diameter.grid_remove()
            self.check_entry(self.diameter_entry, self.valid_diameters)
        if event.widget not in [self.data_projektu_entry, self.data_dokumentu_entry, self.data_uzgodnienia_entry]:
            self.check_entry_dates(self.data_projektu_entry)
            self.check_entry_dates(self.data_dokumentu_entry)
            self.check_entry_dates(self.data_uzgodnienia_entry)

    def highlight_selection(self, event, listbox_widget):
        index = listbox_widget.nearest(event.y)
        if index != self.selected_index:
            self.selected_index = index
            listbox_widget.selection_clear(0, tk.END)
            listbox_widget.selection_set(index)

    def confirm_selection(self, entry_widget, listbox_widget, entryName):
        if self.selected_index is not None:
            selected = listbox_widget.get(self.selected_index)
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, selected)
            listbox_widget.grid_remove()  # Hide Listbox after selection
            self.selected_index = None  # Reset selection
            if entryName == 'material':
                self.update_material_entry_background()
            else:
                self.update_diameter_entry_background()

    def update_entry_background(self, entry_widget, valid_items, filtered_items, isString):
        typed_text = entry_widget.get()

        if typed_text != '' and typed_text != '1':
            if isString:
                if typed_text in valid_items:
                    entry_widget.config(bg="lightgreen")
                elif any(typed_text.lower() in item.lower() for item in filtered_items):
                    entry_widget.config(bg="lightyellow")
                else:
                    entry_widget.config(bg="lightcoral")
            else:
                typed_diameter = int(typed_text)
                if typed_diameter in valid_items:
                    entry_widget.config(bg="lightgreen")
                else:
                    entry_widget.config(bg="lightcoral")

    def check_entry(self, entry, dictionary):
        typed_text = entry.get()
        if typed_text != ''and typed_text not in dictionary and entry.cget('bg') != "lightgreen":
            self.flash_entry(entry)

    def check_entry_dates(self, entry):
        if entry.get() != '':
            try:
                valid_date = datetime.strptime(entry.get(), '%d-%m-%Y')
                if valid_date > datetime.now():
                    self.flash_entry(entry)

            except ValueError:
                self.flash_entry(entry)

    def flash_entry(self, entry):
        original_color = entry.cget('bg')
        entry.config(bg="red")
        self.after(500, lambda: entry.config(bg=original_color))

    def update_listbox_height(self, listbox_widget):
        num_items = listbox_widget.size()
        listbox_widget.config(height=min(num_items, 5))

    def create_file_selection_widgets(self):
        tk.Label(self, text="Wybierz plik TIFF lub PDF:").grid(row=0, column=0, pady=10, sticky="w")
        tk.Button(self, text="Wybierz plik", command=self.choose_file).grid(row=0, column=1, pady=10,sticky="w")

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

    def create_entry(self, label, entry, row, col, bind = None, hide = False):
        lab = tk.Label(self, text=label)
        lab.grid(row=row, column=col, padx=self.COL_PAD, pady=self.ROW_PAD, sticky="w")
        entry.grid(row=row, column=col+1, padx=self.COL_PAD, pady=self.ROW_PAD, sticky="w")
        if bind:
            entry.bind('<KeyRelease>', bind)
        if hide:
            entry.grid_remove()
            lab.grid_remove()

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
        tk.Label(self, text="Numer adresowy:").grid(row=8, column=2, pady=20, sticky="w")
        tk.Label(self, text="Numer obrębu:").grid(row=8, column=3, pady=20, sticky="w")
        tk.Label(self, text="Numer działki:").grid(row=8, column=4, pady=20, sticky="w")

    def create_widgets(self):

        self.create_file_selection_widgets()
        self.create_file_drop_widget()

        self.createAdresLabels()
        #self.create_rodzaj_sieci()

        self.create_entry("Materiał", self.material_entry, 10, 8)
        self.create_entry("Średnica", self.diameter_entry, 12, 8)

        self.listbox_material.grid(row=11, column=9, padx=self.COL_PAD, pady=self.ROW_PAD)
        self.listbox_material.grid_remove()
        self.listbox_diameter.grid(row=13, column=9, padx=self.COL_PAD, pady=self.ROW_PAD)
        self.listbox_diameter.grid_remove()

        self.create_entry("Długość", self.lenght_entry, 14, 8)
        self.create_entry("Numer pliku", self.file_number_entry, 1, 2)
        self.create_entry("Numer teczki", self.dir_number_entry, 1, 0,)

        self.file_number_entry.bind("<KeyRelease>", lambda event: format_number(3, self.file_number_entry))
        self.dir_number_entry.bind("<KeyRelease>", lambda event: format_number(5, self.dir_number_entry))

        self.create_entry("Data projektu", self.data_projektu_entry, 2, 0, bind=format_date_entry)
        self.create_entry("Numer uzgodnienia", self.numer_uzgodnienia_entry, 2, 3)
        self.create_entry("Data uzgodnienia", self.data_uzgodnienia_entry, 3, 0,bind=format_date_entry)
        self.create_entry("Data dokumentu", self.data_dokumentu_entry, 4, 0,bind=format_date_entry)
        self.create_entry("Inwestor", self.invesor_entry, 3, 3)
        tk.Button(self, text="Dodaj nowy", command=self.add_new_row).grid(row=8, column=6, padx=5, pady=5)
        tk.Button(self, text="Dodaj tagi", command=self.apply_tags).grid(row=7, column=8, columnspan=4, pady=20)


    def update_entries_group(self, value):
        if len(self.folder_required_entries) > 0:
            for entry in self.folder_required_entries:
                entry.config(highlightbackground="SystemButtonFace", highlightthickness=1)
        self.folder_required_entries.clear()

        if value == 'EW':
            self.folder_required_entries.append(self.dir_number_entry)
            self.folder_required_entries.append(self.numer_uzgodnienia_entry)
            self.folder_required_entries.append(self.data_projektu_entry)
            self.folder_required_entries.append(self.data_uzgodnienia_entry)


        self.folder_required_entries.append(self.invesor_entry)

        for entry in self.folder_required_entries:
            entry.config(highlightbackground="blue", highlightthickness=1)

    def update_entries_file(self, value):
        if len(self.required_entries) > 0:
            for entry in self.required_entries:
                entry.config(highlightbackground="SystemButtonFace", highlightthickness=1)
        self.required_entries.clear()

        self.required_entries.append(self.material_entry)
        self.required_entries.append(self.diameter_entry)
        self.required_entries.append(self.rodzaj_przewodu_menu)
        self.required_entries.append(self.typ_przewodu_menu)
        self.required_entries.append(self.data_dokumentu_entry)

        if value == 'Projekty tekstowe':
            pass
        elif value == 'Projekty graficzne':
            pass

        elif value == 'Zgłoszenie rozpoczęcia robót':
            self.required_entries.remove(self.material_entry)
            self.required_entries.remove(self.diameter_entry)
        elif value == 'Notatki z robót zanikowych':
            self.required_entries.remove(self.material_entry)
            self.required_entries.remove(self.diameter_entry)
        elif value == 'Szkice do robót zanikowych':
            self.required_entries.remove(self.material_entry)
            self.required_entries.remove(self.diameter_entry)
            self.required_entries.remove(self.data_dokumentu_entry)
        elif value == 'Wyniki badania wody':
            self.required_entries.remove(self.material_entry)
            self.required_entries.remove(self.diameter_entry)
            self.rodzaj_przewodu_var.set('wodociągowa')
            self.rodzaj_przewodu_menu.config(state="disabled")
        elif value == 'Wyniki prób ciśnieniowych':
            self.rodzaj_przewodu_var.set('wodociągowa')
            self.rodzaj_przewodu_menu.config(state="disabled")
        elif value == 'Dokument tekstowy':
            pass
        elif value == 'Multimedia':
            pass
        elif value == 'Mapa z zakresem monitoringu':
            self.required_entries.remove(self.data_dokumentu_entry)

        elif value == 'Protokoły odbioru końcowego':
            pass
        elif value == 'Protokoły odbioru końcowego przyłączy':
            self.typ_przewodu_var.set('przyłącze')
            self.typ_przewodu_menu.config(state="disabled")
        elif value == 'Mapy pomiaru powykonawczego sieci':
            self.typ_przewodu_var.set('sieć')
            self.typ_przewodu_menu.config(state="disabled")
        elif value == 'Mapy pomiaru powykonawczego przyłaczy':
            self.typ_przewodu_var.set('przyłącze')
            self.typ_przewodu_menu.config(state="disabled")
        elif value == 'Zlecenie montażu wodomierza':
            self.required_entries.remove(self.material_entry)
            self.required_entries.remove(self.diameter_entry)
            self.typ_przewodu_var.set('przyłącze')
            self.typ_przewodu_menu.config(state="disabled")
            self.rodzaj_przewodu_var.set('wodociągowa')
            self.rodzaj_przewodu_menu.config(state="disabled")

        elif value == 'Niesklasyfikowane':
            self.required_entries.remove(self.material_entry)
            self.required_entries.remove(self.diameter_entry)
            self.required_entries.remove(self.rodzaj_przewodu_menu)
            self.required_entries.remove(self.typ_przewodu_menu)
            self.required_entries.remove(self.data_dokumentu_entry)


        for entry in self.required_entries:
            entry.config(highlightbackground="blue", highlightthickness=1)

    def bind_events(self):
        # Materiały
        self.material_entry.bind('<KeyRelease>', self.show_material_listbox)
        self.material_entry.bind('<Button-1>', self.show_material_listbox)
        self.listbox_material.bind('<ButtonRelease-1>', lambda event: self.highlight_selection(event, self.listbox_material))
        self.listbox_material.bind('<Return>', self.confirm_material_selection)
        self.listbox_material.bind('<Double-Button-1>', self.confirm_material_selection)

        # Średnice
        self.diameter_entry.bind('<KeyRelease>', self.show_diameter_listbox)
        self.diameter_entry.bind('<Button-1>', self.show_diameter_listbox)
        self.listbox_diameter.bind('<ButtonRelease-1>', lambda event: self.highlight_selection(event, self.listbox_diameter))
        self.listbox_diameter.bind('<Return>', self.confirm_diameter_selection)
        self.listbox_diameter.bind('<Double-Button-1>', self.confirm_diameter_selection)

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

        # except Exception as e:
        #         messagebox.showerror("Błąd tagowania", f"Wystąpił problem: {e}")

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

            if  self.doc_type_menu:
                self.doc_type_menu["menu"].delete(0, "end")  # Czyszczenie starego menu
            if  self.subgroup_menu:
                self.subgroup_menu["menu"].delete(0, "end")  # Czyszczenie menu Podgrupa dokumentów

            self.update_entries_group(value)
            doc_type_options = filename_generator.get_group(value)

            for option in doc_type_options:
                if self.doc_type_menu:
                    self.doc_type_menu["menu"].add_command(label=option,
                                                       command=tk._setit(self.doc_type_var, option, self.update_subgroup))

    def update_subgroup(self, value):
        self.subgroup_var.set('')  # Resetowanie wyboru w `Podgrupa dokumentów`
        self.subgroup_menu["menu"].delete(0, "end")  # Czyszczenie starego menu

        subgroup_options = filename_generator.get_subgroup(value)
        for option in subgroup_options:
            self.subgroup_menu["menu"].add_command(label=option, command=tk._setit(self.subgroup_var, option, self.update_sub_subgroup))

    def update_sub_subgroup(self, value):
        self.update_entries_file(value)

    def confirm_material_selection(self, event=None):
        self.confirm_selection(self.material_entry, self.listbox_material, 'material')

    def update_material_entry_background(self):
        self.update_entry_background(self.material_entry, self.valid_materials, self.filtered_materials, True)

    def confirm_diameter_selection(self, event=None):
        self.confirm_selection(self.diameter_entry, self.listbox_diameter, 'diameter')

    def update_diameter_entry_background(self):
        self.update_entry_background(self.diameter_entry, self.valid_diameters, self.filtered_diameters, False)


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
