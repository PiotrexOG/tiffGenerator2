import os
import json
import subprocess

class ExifManager:
    @staticmethod
    def _add_exif_data(dest_file_path, exif_data, new_file_name):
        exif_json_path = os.path.join(os.path.dirname(dest_file_path), 'exif_data.json')
        with open(exif_json_path, 'w', encoding='utf-8') as exif_json_file:
            json.dump([exif_data], exif_json_file, indent=4)

        command = f'exiftool -j={exif_json_path} {dest_file_path}'
        subprocess.run(['powershell', '-Command', command], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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
