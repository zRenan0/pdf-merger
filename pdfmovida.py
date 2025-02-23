from flask import Flask, render_template, request, send_from_directory
import os
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import io

app = Flask(__name__)

# Caminho para salvar os arquivos temporários
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Verifica se a pasta de uploads existe, caso contrário, cria
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Função para mesclar PDFs
def merge_pdfs(pdf_files, output_path):
    pdf_writer = PdfWriter()

    for pdf in pdf_files:
        pdf_reader = PdfReader(pdf)
        for page in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page])

    with open(output_path, 'wb') as output_pdf:
        pdf_writer.write(output_pdf)

# Função para converter imagem em PDF
def image_to_pdf(image_file, output_pdf):
    img = Image.open(image_file)
    pdf_bytes = img.convert('RGB')
    pdf_bytes.save(output_pdf, "PDF", resolution=100.0)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('files')
        ordered_files = request.form.get('filesOrder').split(',')

        pdf_files = []
        image_files = []

        # Salva os arquivos temporários
        for i, file in enumerate(files):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"file_{i}_{file.filename}")
            file.save(file_path)

            # Classifica os arquivos entre PDFs e imagens
            if file.filename.lower().endswith('.pdf'):
                pdf_files.append(file_path)
            elif file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(file_path)

        # Ordena os arquivos conforme a ordem recebida
        ordered_files = [os.path.join(app.config['UPLOAD_FOLDER'], f"file_{i}_{ordered_files[i]}") for i in range(len(ordered_files))]

        # Mescla PDFs
        output_pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], 'merged_output.pdf')
        merge_pdfs(ordered_files, output_pdf_path)

        # Caso haja imagens, converte para PDF
        if image_files:
            for image_file in image_files:
                image_pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{os.path.basename(image_file)}.pdf')
                image_to_pdf(image_file, image_pdf_path)

        return send_from_directory(app.config['OUTPUT_FOLDER'], 'merged_output.pdf', as_attachment=True)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
