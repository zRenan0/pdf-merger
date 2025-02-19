from flask import Flask, render_template, request, send_file
import PyPDF2
from PIL import Image
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
MERGED_FILE = "merged.pdf"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def merge_pdfs_and_images(file_list, output_filename):
    merger = PyPDF2.PdfMerger()
    image_pdfs = []
    
    for file in file_list:
        if file.lower().endswith(".pdf"):
            merger.append(file)
        elif file.lower().endswith((".jpg", ".jpeg", ".png")):
            image = Image.open(file)
            pdf_path = file + ".pdf"
            image.convert("RGB").save(pdf_path)
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
        file_paths = []
        
        for file in uploaded_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            file_paths.append(file_path)
        
        output_pdf = os.path.join(app.config['UPLOAD_FOLDER'], MERGED_FILE)
        merged_file = merge_pdfs_and_images(file_paths, output_pdf)
        
        return send_file(merged_file, as_attachment=True)
    
    return '''
    <!doctype html>
    <html>
    <body>
        <h2>Envie seus arquivos PDF e imagens para mesclar</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="files" multiple>
            <input type="submit" value="Mesclar PDFs e Imagens">
        </form>
    </body>
    </html>
    '''

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Usa a porta do Render
    app.run(host="0.0.0.0", port=port, debug=False)  # Desative debug em produção

