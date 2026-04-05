import fitz
import os

def split_pdf_to_images(pdf_path):
    pdf = fitz.open(pdf_path)
    image_paths = []

    for page_num in range(len(pdf)):
        page = pdf.load_page(page_num)
        pix = page.get_pixmap()
        img_path = f"{pdf_path}_page_{page_num}.png"
        pix.save(img_path)
        image_paths.append(img_path)

    return image_paths