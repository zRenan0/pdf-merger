from flask import Flask, render_template, request, send_file
import os
from PyPDF2 import PdfMerger, PdfReader
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
MERGED_FILE = "merged.pdf"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def convert_image_to_pdf(image_path, pdf_path):
    # Usando Pillow para converter a imagem para PDF
    image = Image.open(image_path)
    image.save(pdf_path, "PDF", resolution=100.0)

def split_pdf(input_pdf, output_folder):
    reader = PdfReader(input_pdf)
    output_files = []

    for page_num in range(len(reader.pages)):
        writer = PdfMerger()
        writer.append(input_pdf, pages=(page_num, page_num + 1))
        output_filename = os.path.join(output_folder, f"page_{page_num + 1}.pdf")
        writer.write(output_filename)
        output_files.append(output_filename)

    return output_files

def merge_pdfs_and_images(file_list, output_filename):
    merger = PdfMerger()
    image_pdfs = []

    for file in file_list:
        if file.lower().endswith(".pdf"):
            if len(PdfReader(file).pages) > 1:
                output_folder = os.path.join(UPLOAD_FOLDER, "split")
                os.makedirs(output_folder, exist_ok=True)
                split_pdfs = split_pdf(file, output_folder)
                for split_pdf in split_pdfs:
                    merger.append(split_pdf)
                # Remover arquivos de página após mesclagem
                for split_pdf in split_pdfs:
                    os.remove(split_pdf)
            else:
                merger.append(file)
        elif file.lower().endswith((".jpg", ".jpeg", ".png")):
            pdf_path = file + ".pdf"
            convert_image_to_pdf(file, pdf_path)
            image_pdfs.append(pdf_path)
            merger.append(pdf_path)

    merger.write(output_filename)
    merger.close()

    for img_pdf in image_pdfs:
        os.remove(img_pdf)

    return output_filename

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        uploaded_files = request.files.getlist('files')
        ordered_filenames = request.form.get('filesOrder', '').split(',')

        file_paths = []
        
        for file in uploaded_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            file_paths.append(file_path)
        
        # Ordenar os arquivos conforme a ordem fornecida pelo frontend
        ordered_file_paths = [fp for name in ordered_filenames for fp in file_paths if os.path.basename(fp) == name]

        output_pdf = os.path.join(app.config['UPLOAD_FOLDER'], MERGED_FILE)
        merged_file = merge_pdfs_and_images(ordered_file_paths, output_pdf)
        
        return send_file(merged_file, as_attachment=True)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
