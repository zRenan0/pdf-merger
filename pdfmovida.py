from flask import Flask, request, render_template, send_file, jsonify, send_from_directory
import os
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image

app = Flask(__name__)

# Configurações do Upload
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # Limite de tamanho de arquivo (50MB)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Função para validar se um arquivo é uma imagem ou PDF
def allowed_file(filename):
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    try:
        if request.method == 'POST':
            if 'files' not in request.files:
                return jsonify({"error": "Nenhum arquivo enviado!"}), 400
            
            files = request.files.getlist('files')
            
            if not files or all(file.filename == '' for file in files):
                return jsonify({"error": "Nenhum arquivo válido enviado!"}), 400
            
            file_paths = []
            
            for file in files:
                if file and allowed_file(file.filename):
                    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filename)
                    file_paths.append(filename)
                else:
                    return jsonify({"error": f"Arquivo inválido: {file.filename}"}), 400

            # Desmembrar PDFs e converter imagens
            pages, image_paths = split_pdfs_and_convert_images(file_paths)
            
            return jsonify({"pages": pages, "images": image_paths})

        return render_template('index.html')

    except Exception as e:
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

@app.route('/merge', methods=['POST'])
def merge_pages():
    try:
        page_order = request.json['pageOrder']
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged_output.pdf')
        
        merge_pdf_pages(page_order, output_path)
        
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Erro ao mesclar páginas: {str(e)}"}), 500
    
@app.route('/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def split_pdfs_and_convert_images(file_paths):
    pages = []
    image_paths = []  # Lista para armazenar as imagens geradas
    
    for path in file_paths:
        if path.endswith('.pdf'):
            pdf = PdfReader(path)
            for i, page in enumerate(pdf.pages):
                output = PdfWriter()
                output.add_page(page)
                page_path = f"{path}_page_{i+1}.pdf"
                with open(page_path, "wb") as output_stream:
                    output.write(output_stream)
                pages.append({"path": page_path, "name": f"{os.path.basename(path)} - Página {i+1}"})
        elif path.lower().endswith(('png', 'jpg', 'jpeg')):
            img = Image.open(path)
            image_filename = f"{os.path.basename(path)}_converted.jpg"  # Definindo um nome para a imagem convertida
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            img.save(image_path, 'JPEG')
            image_paths.append(image_path)  # Adiciona o caminho da imagem à lista
            pages.append({"path": image_path, "name": os.path.basename(path)})

    return pages, image_paths  # Retorna também os caminhos das imagens

def merge_pdf_pages(page_order, output_path):
    merger = PdfWriter()
    for page in page_order:
        pdf = PdfReader(page)
        merger.add_page(pdf.pages[0])
    with open(output_path, "wb") as output_file:
        merger.write(output_file)

# Erro 404 personalizado
@app.errorhandler(404)
def page_not_found(error):
    return jsonify({"error": "Página não encontrada"}), 404

# Erro 413 - Arquivo muito grande
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "Arquivo muito grande. O tamanho máximo permitido é 50MB."}), 413

if __name__ == '__main__':
    app.run(debug=True)
