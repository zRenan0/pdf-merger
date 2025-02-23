from flask import Flask, request, render_template, send_from_directory, jsonify
import os
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image

app = Flask(__name__)

# Configuração do Upload
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # Limite de 50MB
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Função para verificar se o arquivo tem a extensão permitida
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

            ordered_files = request.form['filesOrder'].split(',')
            
            file_paths = []
            for file in files:
                if file and allowed_file(file.filename):
                    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filename)
                    file_paths.append(filename)

            # Reorganizar os arquivos conforme a ordem recebida
            file_paths_sorted = [file_paths[ordered_files.index(file)] for file in ordered_files]

            merged_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged_output.pdf')
            split_pdf_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'split_pdfs')
            os.makedirs(split_pdf_folder, exist_ok=True)

            # Mesclar os PDFs e imagens
            merge_pdfs(file_paths_sorted, merged_pdf_path)

            # Desmembrar o PDF mesclado
            split_pdf_files = split_pdf(merged_pdf_path, split_pdf_folder)

            # Retornar os PDFs desmembrados como resposta
            return jsonify({
                'message': 'Mesclagem e desmembramento realizados com sucesso!',
                'split_pdfs': [os.path.basename(file) for file in split_pdf_files]
            })

        return render_template('index.html')
    
    except Exception as e:
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

# Função para mesclar os arquivos PDF ou imagens
def merge_pdfs(file_paths, output_path):
    pdf_merger = PdfMerger()
    
    for path in file_paths:
        try:
            if path.endswith('.pdf'):
                pdf_merger.append(path)
            elif path.lower().endswith(('png', 'jpg', 'jpeg')):
                img = Image.open(path)
                img_pdf_path = path.replace(img.format, 'pdf')
                img.save(img_pdf_path, 'PDF')
                pdf_merger.append(img_pdf_path)
        except Exception as e:
            raise Exception(f"Erro ao processar o arquivo {path}: {str(e)}")

    pdf_merger.write(output_path)
    pdf_merger.close()

# Função para dividir um PDF em páginas individuais
def split_pdf(input_pdf_path, output_folder):
    pdf_reader = PdfReader(input_pdf_path)
    split_files = []

    for i, page in enumerate(pdf_reader.pages):
        pdf_writer = PdfWriter()
        pdf_writer.add_page(page)

        output_path = os.path.join(output_folder, f"page_{i + 1}.pdf")
        with open(output_path, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)

        split_files.append(output_path)

    return split_files

# Endpoint para o download do PDF
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Função para limpar arquivos temporários após o processamento
def clean_up_files(file_paths):
    for file in file_paths:
        try:
            os.remove(file)
        except Exception as e:
            print(f"Erro ao remover arquivo {file}: {str(e)}")

# Erro 404
@app.errorhandler(404)
def page_not_found(error):
    return jsonify({"error": "Página não encontrada"}), 404

# Erro 413 - Arquivo muito grande
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "Arquivo muito grande. O tamanho máximo permitido é 50MB."}), 413

if __name__ == '__main__':
    app.run(debug=True)
