from flask import Flask, request, send_file, jsonify, render_template
import os
from PyPDF2 import PdfMerger, PdfReader
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
THUMBNAIL_FOLDER = "static/thumbnails"
MERGED_FILE = "merged.pdf"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER

# Criando pastas se não existirem
for folder in [UPLOAD_FOLDER, THUMBNAIL_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def convert_image_to_pdf(image_path, pdf_path):
    image = Image.open(image_path)
    image.save(pdf_path, "PDF", resolution=100.0)

def extract_pdf_pages(pdf_path):
    """Extrai páginas de um PDF mesclado e as salva separadamente."""
    reader = PdfReader(pdf_path)
    extracted_files = []

    for i, page in enumerate(reader.pages):
        output_filename = os.path.join(UPLOAD_FOLDER, f"{os.path.basename(pdf_path)}_page_{i+1}.pdf")
        merger = PdfMerger()
        merger.append(pdf_path, pages=(i, i+1))
        merger.write(output_filename)
        merger.close()
        extracted_files.append(output_filename)

    return extracted_files

def generate_pdf_thumbnail(pdf_path):
    """Gera uma miniatura para um PDF."""
    thumb_path = os.path.join(THUMBNAIL_FOLDER, os.path.basename(pdf_path) + ".png")
    
    if not os.path.exists(thumb_path):
        try:
            reader = PdfReader(pdf_path)
            page = reader.pages[0]
            image = page.to_image(resolution=100)
            image.save(thumb_path, format="PNG")
        except:
            thumb_path = "static/imagens/pdf-icon.png"

    return thumb_path

def merge_pdfs_and_images(file_list, output_filename):
    merger = PdfMerger()
    image_pdfs = []

    for file in file_list:
        if file.lower().endswith(".pdf"):
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

@app.route('/download')
def download_file():
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], MERGED_FILE)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "Arquivo não encontrado", 404

@app.route('/thumbnails/<filename>')
def get_thumbnail(filename):
    return send_file(os.path.join(THUMBNAIL_FOLDER, filename))

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        uploaded_files = request.files.getlist('files')
        ordered_filenames = request.form.get('filesOrder', '').split(',')

        file_paths = []
        extracted_files = []

        for file in uploaded_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            file_paths.append(file_path)

            # Se for PDF mesclado, extrair páginas
            if file.filename.lower().endswith(".pdf"):
                extracted_files.extend(extract_pdf_pages(file_path))

        file_paths.extend(extracted_files)

        ordered_file_paths = [fp for name in ordered_filenames for fp in file_paths if os.path.basename(fp) == name]
        output_pdf = os.path.join(app.config['UPLOAD_FOLDER'], MERGED_FILE)
        merge_pdfs_and_images(ordered_file_paths, output_pdf)

        return jsonify({"download_url": "/download", "thumbnails": [generate_pdf_thumbnail(fp) for fp in file_paths]})

    return render_template("index.html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
