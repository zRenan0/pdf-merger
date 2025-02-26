from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import PyPDF2
from PIL import Image
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    files = request.files.getlist('files')
    uploaded_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            uploaded_files.append({'name': filename, 'path': file_path})
    
    return jsonify({'pages': uploaded_files})

@app.route('/merge', methods=['POST'])
def merge_pdfs():
    data = request.json
    page_order = data.get('pageOrder', [])
    output_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged_document.pdf')
    
    merger = PyPDF2.PdfMerger()
    
    for pdf_path in page_order:
        if os.path.exists(pdf_path):
            merger.append(pdf_path)
    
    merger.write(output_pdf_path)
    merger.close()
    
    return send_file(output_pdf_path, as_attachment=True)

@app.route('/split', methods=['POST'])
def split_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
            split_files = []
            
            for i in range(num_pages):
                writer = PyPDF2.PdfWriter()
                writer.add_page(reader.pages[i])
                split_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f'split_{i+1}.pdf')
                with open(split_pdf_path, 'wb') as output_pdf:
                    writer.write(output_pdf)
                split_files.append({'name': f'split_{i+1}.pdf', 'path': split_pdf_path})
        
        return jsonify({'pages': split_files})
    
    return jsonify({'error': 'Arquivo inválido'}), 400

@app.route('/upload', methods=['POST'])
def upload_file():


if __name__ == '__main__':
    app.run(debug=True)
