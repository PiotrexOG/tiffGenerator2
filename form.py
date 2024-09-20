import tkinter as tk
from tkinter import filedialog, messagebox
import os
import material_dictionary
import filename_generator
import ocr
import threading

from filename_generator import dates
from validate import Validator
from exif_manager import ExifManager
from datetime import datetime


# GUI z Tkinter
class Application(tk.Tk):

    ROW_PAD = 10
    COL_PAD = 5
    ENTRY_WIDTH = 30

    def __init__(self):
        super().__init__()
        self.listbox_material = tk.Listbox(self, height=10, width=50)
        self.material_entry = tk.Entry(self, width=self.ENTRY_WIDTH)
        self.title("Tagowanie plików TIFF/PDF")
        self.geometry("1920x1080")

        self.file_path = ""
        self.info = {}
        self.skip_empty = 1

        self.data = []
        self.valid_materials = material_dictionary.get_dict()

        self.rodzaj_sieci_var = tk.StringVar()
        self.file_number_entry = tk.Entry(self, width=30)
        self.dir_number_entry = tk.Entry(self, width=30)
        self.folder_type_var = tk.StringVar()
        self.doc_type_var = tk.StringVar()
        self.subgroup_var = tk.StringVar()

        self.entries = []  # Lista na widgety do wpisywania danych
        self.static_entries = {}
        self.dynamic_widgets = []
        self.filtered_materials = []  # List to store filtered results
        self.create_widgets()
        self.bind_events()
        self.selected_index = None  # Reset selection

    def update_address_fields(self, result):
        self.data = result

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

                button_validate = tk.Button(self, text="Waliduj", command=lambda e=row_entries: self.validate_adress(e))
                button_validate.grid(row=8 + i, column=col, padx=10, pady=5)
                row_entries["Waliduj"] = button_validate

                button_confirm = tk.Button(self, text="Zatwierdź",
                                           command=lambda e=row_entries: self.confirm_address(e))
                button_confirm.grid(row=8 + i, column=col + 1, padx=10, pady=5)
                button_confirm.grid_remove()  # Na początku ukrywamy przycisk
                row_entries["Zatwierdź"] = button_confirm

                self.dynamic_widgets.append(row_entries)

    def filter_names(self, event):
        typed_text = self.material_entry.get()
        self.listbox_material.delete(0, tk.END)

        if typed_text:
            self.filtered_materials = [material for material in self.valid_materials if
                                       any(word.lower().startswith(typed_text.lower()) for word in material.split())]
            for item in self.filtered_materials:
                self.listbox_material.insert(tk.END, item)
        else:
            sorted_materials = sorted(self.valid_materials)
            for item in sorted_materials:
                self.listbox_material.insert(tk.END, item)

        self.update_entry_background()
        self.update_listbox_height()

    def show_listbox(self, event):
        self.listbox_material.grid()
        self.filter_names(event)

    def on_click_outside(self, event):
        if event.widget not in [self.material_entry, self.listbox_material]:
            self.listbox_material.grid_remove()
            self.check_entry()
        dates = filename_generator.dates
        if event.widget not in [self.static_entries[date] for date in dates]:
            self.check_entry_dates()

    def highlight_selection(self, event=None):
        index = self.listbox_material.nearest(event.y)
        if index != self.selected_index:
            # Highlight the item but do not confirm
            self.selected_index = index
            self.listbox_material.selection_clear(0, tk.END)
            self.listbox_material.selection_set(index)

    def confirm_selection(self, event=None):
        if self.selected_index is not None:
            selected = self.listbox_material.get(self.selected_index)

            self.material_entry.delete(0, tk.END)
            self.material_entry.insert(0, selected)
            self.listbox_material.grid_remove()  # Hide Listbox after selection
            self.selected_index = None  # Reset selection

            self.update_entry_background()

    def update_entry_background(self):
        typed_text = self.material_entry.get()
        if typed_text in self.valid_materials:
            self.material_entry.config(bg="lightgreen")
        elif any(typed_text.lower() in material.lower() for material in self.filtered_materials):
            self.material_entry.config(bg="lightyellow")
        else:
            self.material_entry.config(bg="lightcoral")

    def check_entry(self):
        typed_text = self.material_entry.get()
        if typed_text != ''and typed_text not in self.valid_materials and self.material_entry.cget('bg') != "lightgreen":
            self.flash_entry()

        dates = filename_generator.dates
        for i, (label_text, tag_key) in enumerate(dates):
            typed_date = self.static_entries[tag_key].get()
            if typed_date != '':
                try:
                    valid_date = datetime.strptime(typed_date, '%d-%m-%Y')
                    if valid_date > datetime.now():
                        self.flash_entry_date(tag_key)

                except ValueError:
                    self.flash_entry_date(tag_key)


    



    def format_date_entry(self, event):
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

    def flash_entry(self):
        original_color = self.material_entry.cget('bg')
        self.material_entry.config(bg="red")
        self.after(500, lambda: self.material_entry.config(bg=original_color))

    def flash_entry_date(self, tag):
        original_color = self.static_entries[tag].cget('bg')
        self.static_entries[tag].config(bg="red")
        self.after(500, lambda: self.static_entries[tag].config(bg=original_color))

    def validate_entry(self):
        typed_text = self.material_entry.get()
        if typed_text not in self.valid_materials:
            messagebox.showerror("Błąd", "Wpisany materiał nie jest poprawny!")
        else:
            messagebox.showinfo("Sukces", "Tag dodany pomyślnie!")

    def update_listbox_height(self):
        num_items = self.listbox_material.size()
        self.listbox_material.config(height=min(num_items, 5))

    def create_file_selection_widgets(self):
        tk.Label(self, text="Wybierz plik TIFF lub PDF:").grid(row=0, column=0, pady=10, sticky="w")
        tk.Button(self, text="Wybierz plik", command=self.choose_file).grid(row=0, column=1, pady=10,sticky="w")

    def create_static_entries(self):
        fields = filename_generator.fields
        for i, (label_text, tag_key) in enumerate(fields):
            if i == 0:
                continue
            self.create_labeled_entry(label_text, tag_key, row=(i // 4) + 1, column=(i % 4) * 2)

    def create_labeled_entry(self, label_text, tag_key, row, column):
        tk.Label(self, text=label_text).grid(row=row, column=column, padx=self.COL_PAD, pady=self.ROW_PAD, sticky="w")
        entry = tk.Entry(self, width=self.ENTRY_WIDTH)
        entry.grid(row=row, column=column + 1, padx=self.COL_PAD, pady=self.ROW_PAD, sticky="w")
        self.static_entries[tag_key] = entry

    def create_material_selection_widgets(self):
        tk.Label(self, text="Materiał").grid(row=10, column=10, padx=self.COL_PAD, pady=self.ROW_PAD, sticky="w")
        self.material_entry.grid(row=10, column=11, padx=self.COL_PAD, pady=self.ROW_PAD, sticky="w")
        self.listbox_material.grid(row=11, column=11, padx=self.COL_PAD, pady=self.ROW_PAD)
        self.listbox_material.grid_remove()

    def bind_events(self):
        self.material_entry.bind('<KeyRelease>', self.show_listbox)
        self.material_entry.bind('<Button-1>', self.show_listbox)
        self.listbox_material.bind('<ButtonRelease-1>', self.highlight_selection)
        self.listbox_material.bind('<Return>', self.confirm_selection)
        self.listbox_material.bind('<Double-Button-1>', self.confirm_selection)
        self.bind('<Button-1>', self.on_click_outside)

    def create_rodzaj_sieci(self):
        tk.Label(self, text="Rodzaj sieci:").grid(row=5, column=0, pady=50, sticky="w")
        rodzaj_sieci_menu = tk.OptionMenu(self, self.rodzaj_sieci_var, "wodociągowa", "kanalizacyjna", "wodociągowo-kanalizacyjna")
        rodzaj_sieci_menu.config(width=20)
        rodzaj_sieci_menu.grid(row=5, column=1, pady=10, sticky="w")

    def create_date_entry(self):
        dates = filename_generator.dates
        for i, (label_text, tag_key) in enumerate(dates):
            self.create_labeled_entry(label_text, tag_key, row=i+1, column=9)
            self.static_entries[tag_key].bind('<KeyRelease>', self.format_date_entry)


    def create_file_number_entry(self):
        tk.Label(self, text="Numer pliku").grid(row=3, column=6, padx=10, pady=5, sticky="w")
        self.file_number_entry.grid(row=3, column=7, padx=10, pady=5, sticky="w")
        self.file_number_entry.bind("<KeyRelease>", lambda event: format_number(3, self.file_number_entry))

    def create_dir_number_entry(self):
        tk.Label(self, text="Numer teczki").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.dir_number_entry.grid(row=1, column= 1, padx=10, pady=5, sticky="w")
        self.dir_number_entry.bind("<KeyRelease>", lambda event: format_number(5, self.dir_number_entry))

    def create_documentation_widgets(self):
        tk.Label(self, text="Rodzaj teczki dokumentów:").grid(row=6, column=0, pady=100, sticky="w")
        folder_type_menu = tk.OptionMenu(self, self.folder_type_var, "EW", "EWP", "EWS", "EKS", "KSA", "PZO", "UL", "N",
                                         command=self.update_doc_type)
        folder_type_menu.grid(row=6, column=1, pady=50)

        tk.Label(self, text="Typ dokumentacji:").grid(row=6, column=2, pady=100, sticky="w")
        self.doc_type_menu = tk.OptionMenu(self, self.doc_type_var, "", command=self.update_subgroup)
        self.doc_type_menu.grid(row=6, column=3, pady=50)

        tk.Label(self, text="Podgrupa dokumentów:").grid(row=6, column=4, pady=100, sticky="w")
        self.subgroup_menu = tk.OptionMenu(self, self.subgroup_var, "")
        self.subgroup_menu.grid(row=6, column=5, pady=10)

    def create_widgets(self):
        self.create_file_selection_widgets()
        self.create_static_entries()
        tk.Label(self, text="Adresy:").grid(row=7, column=0, pady=50, sticky="w")
        self.create_material_selection_widgets()
        self.create_rodzaj_sieci()
        self.create_file_number_entry()
        self.create_dir_number_entry()
        self.create_documentation_widgets()
        self.create_date_entry()
        tk.Button(self, text="Dodaj tagi", command=self.apply_tags).grid(row=7, column=10, columnspan=4, pady=20)

    def validate_adress(self, row_entries):
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

            self.update_button_states(row_entries)
        except Exception as e:
            messagebox.showerror("Błąd walidacji", f"Wystąpił problem: {e}")

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
        try:
            if not self.file_path:
                messagebox.showwarning("Brak pliku", "Nie wybrano pliku do tagowania.")
                return

            file_extension = os.path.splitext(self.file_path)[1].lower()
            info = {key: entry.get() for key, entry in self.static_entries.items()}
            info['Rodzaj sieci'] = self.rodzaj_sieci_var.get()
            info['Nr_teczki'] = self.dir_number_entry.get()
            info['Material'] = self.material_entry.get()

            folderType = self.folder_type_var.get()
            groupType = self.doc_type_var.get()
            subGroupType = self.subgroup_var.get()
            file_number_entry = self.file_number_entry.get()

            f, s, t = filename_generator.generate_file_name_tags(folderType, groupType, subGroupType)

            new_file_name = f"{f}{info['Nr_teczki']}{s}{t}{file_number_entry}"
            if file_extension == ".tiff":
                ExifManager.process_tiff(self.file_path, info, f"{new_file_name}.tiff")
            elif file_extension == ".pdf":
                ExifManager.process_pdf(self.file_path, info, f"{new_file_name}.pdf")
            else:
                messagebox.showerror("Błąd formatu", "Niewłaściwy format pliku. Wybierz TIFF lub PDF.")
        except Exception as e:
            messagebox.showerror("Błąd tagowania", f"Wystąpił problem: {e}")

    def choose_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf"),("TIFF files", "*.tiff")])
        if self.file_path:
            threading.Thread(target=self.process_ocr, daemon=True).start()

    def process_ocr(self):
        try:
            result = ocr.rozpoznaj_adresy(self.file_path)
            self.after(0, self.update_address_fields, result)
        except Exception as e:
            messagebox.showerror("Błąd OCR", f"Wystąpił problem podczas przetwarzania OCR: {e}")

    def update_doc_type(self, value):
            self.doc_type_var.set('')  # Resetowanie wyboru w `Typ dokumentacji`
            self.subgroup_var.set('')  # Resetowanie wyboru w `Podgrupa dokumentów`

            self.doc_type_menu["menu"].delete(0, "end")  # Czyszczenie starego menu
            self.subgroup_menu["menu"].delete(0, "end")  # Czyszczenie menu Podgrupa dokumentów

            doc_type_options = filename_generator.get_group(value)

            for option in doc_type_options:
                self.doc_type_menu["menu"].add_command(label=option,
                                                       command=tk._setit(self.doc_type_var, option, self.update_subgroup))

    def update_subgroup(self, value):
        self.subgroup_var.set('')  # Resetowanie wyboru w `Podgrupa dokumentów`
        self.subgroup_menu["menu"].delete(0, "end")  # Czyszczenie starego menu

        subgroup_options = filename_generator.get_subgroup(value)
        for option in subgroup_options:
            self.subgroup_menu["menu"].add_command(label=option, command=tk._setit(self.subgroup_var, option))

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

if __name__ == "__main__":
    app = Application()
    app.mainloop()
