from flask import Flask, request, render_template, send_file, jsonify
import os
from PyPDF2 import PdfMerger
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
            # Verifica se algum arquivo foi enviado
            if 'files' not in request.files:
                return jsonify({"error": "Nenhum arquivo enviado!"}), 400
            
            files = request.files.getlist('files')
            
            # Verifica se existem arquivos válidos
            if not files or all(file.filename == '' for file in files):
                return jsonify({"error": "Nenhum arquivo válido enviado!"}), 400
            
            ordered_files = request.form['filesOrder'].split(',')
            
            file_paths = []
            
            # Salvar os arquivos recebidos
            for file in files:
                if file and allowed_file(file.filename):
                    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filename)
                    file_paths.append(filename)
                else:
                    return jsonify({"error": f"Arquivo inválido: {file.filename}"}), 400

            # Reordenar os arquivos conforme a ordem recebida
            file_paths_sorted = [file_paths[ordered_files.index(file)] for file in ordered_files]

            # Realiza a mesclagem dos PDFs e imagens
            try:
                merged_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged_output.pdf')
                merge_pdfs(file_paths_sorted, merged_pdf_path)
                return send_file(merged_pdf_path, as_attachment=True)
            except Exception as e:
                return jsonify({"error": f"Erro ao mesclar arquivos: {str(e)}"}), 500
            finally:
                # Limpeza dos arquivos temporários após o processamento
                clean_up_files(file_paths)

        return render_template('index.html')

    except Exception as e:
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

# Função para mesclar arquivos PDF ou converter imagens para PDF e mesclar
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

# Função para limpar arquivos temporários
def clean_up_files(file_paths):
    for file in file_paths:
        try:
            os.remove(file)
        except Exception as e:
            print(f"Erro ao remover arquivo {file}: {str(e)}")
    
    # Também limpa arquivos PDF temporários criados durante a conversão de imagens
    for file in os.listdir(UPLOAD_FOLDER):
        if file.endswith('.pdf') and file != 'merged_output.pdf':
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, file))
            except Exception as e:
                print(f"Erro ao remover arquivo {file}: {str(e)}")

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
