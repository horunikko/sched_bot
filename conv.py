import subprocess
import shlex
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError
import time
import os
from db import debug


# функция конвертации xlsx в pdf
def xlsx_to_pdf(input_file, output_dir):
    cmd = rf'/usr/bin/soffice --headless --convert-to pdf --outdir {output_dir} {input_file}'
    success = False
    while not success:
        try:
            if debug:
                print("Преобразуем xlsx в pdf...")
            subprocess.run(shlex.split(cmd), check=True)
            success = True
        except Exception as e:
            if debug:
                print("Ошибка преобразование xlsx в pdf. Пробуем снова")
            time.sleep(5)


# функция конвертации pdf в png
def pdf_to_png(poppler_path):
    success = False
    while not success:
        try:
            n_page = [0, 1, 3]
            pages = convert_from_path('sched.pdf', dpi=150)
            if debug:
                print("Преобразуем pdf в png...")
            for page in n_page:
                img = pages[page]
                img.save(f'page_{page+1}.png')
            success = True
        except PDFPageCountError as e:
            if debug:
                print("Ошибка преобразование pdf в png. Пробуем снова")
            time.sleep(5)