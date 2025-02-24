from flask import Flask, request, render_template, send_file, jsonify, send_from_directory
import os
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import io
import shutil

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
            pages = split_pdfs_and_convert_images(file_paths)
            
            return jsonify({"pages": pages})

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
    
@app.route('/pdf/<path:filename>')
def serve_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def split_pdfs_and_convert_images(file_paths):
    pages = []
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
            pdf_path = f"{path}.pdf"
            img.save(pdf_path, 'PDF')
            pages.append({"path": pdf_path, "name": os.path.basename(path)})
    return pages

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

port = int(os.environ.get('PORT', 5000))  # Se a variável de ambiente não for definida, usa 5000
app.run(host='0.0.0.0', port=port, debug=True)



if __name__ == '__main__':
    app.run(debug=True)