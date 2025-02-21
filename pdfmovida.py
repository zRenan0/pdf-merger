from flask import Flask, render_template, request, send_file
import PyPDF2
from PIL import Image
import os
import fitz  # PyMuPDF para renderizar miniaturas de PDFs

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
MERGED_FILE = "merged.pdf"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def generate_pdf_thumbnail(pdf_path, thumbnail_path):
    doc = fitz.open(pdf_path)
    page = doc[0]
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.thumbnail((100, 150))
    img.save(thumbnail_path)

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
            
            if file.filename.lower().endswith(".pdf"):
                thumbnail_path = file_path + "_thumb.jpg"
                generate_pdf_thumbnail(file_path, thumbnail_path)
        
        output_pdf = os.path.join(app.config['UPLOAD_FOLDER'], MERGED_FILE)
        merged_file = merge_pdfs_and_images(file_paths, output_pdf)
        
        return send_file(merged_file, as_attachment=True)
    
    return '''
  <!doctype html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mesclar PDFs e Imagens</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f4f7fa;
            font-family: 'Arial', sans-serif;
        }
        .card {
            border-radius: 15px;
            overflow: hidden;
        }
        .card-header {
            background-color: #007bff;
            color: white;
            text-align: center;
            padding: 20px 0;
            font-size: 1.5rem;
        }
        .preview-container {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 20px;
        }
        .preview-container .preview-item {
            width: 120px;
            height: 120px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .preview-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .btn-upload {
            background-color: #28a745;
            border-color: #28a745;
        }
        .btn-upload:hover {
            background-color: #218838;
            border-color: #1e7e34;
        }
    </style>
    <script>
        function previewFiles() {
            let preview = document.getElementById('preview');
            preview.innerHTML = "";
            let files = document.getElementById('fileInput').files;
            
            let fileArray = Array.from(files);
            fileArray.sort((a, b) => a.name.localeCompare(b.name));
            
            for (let file of fileArray) {
                let reader = new FileReader();
                reader.onload = function(e) {
                    let div = document.createElement("div");
                    div.classList.add("preview-item");
                    div.innerHTML = `<img src="${e.target.result}" class="img-thumbnail">`;
                    preview.appendChild(div);
                };
                
                if (file.type.startsWith("image")) {
                    reader.readAsDataURL(file);
                }
            }
        }
    </script>
</head>
<body>
    <div class="container mt-5">
        <div class="card">
            <div class="card-header">
                <h2><i class="fas fa-upload"></i> Mesclar PDFs e Imagens</h2>
            </div>
            <div class="card-body">
                <form method="post" enctype="multipart/form-data">
                    <div class="mb-3">
                        <label for="fileInput" class="form-label">Selecione seus arquivos PDF e Imagens</label>
                        <input type="file" id="fileInput" name="files" multiple class="form-control" onchange="previewFiles()">
                    </div>
                    <div id="preview" class="preview-container"></div>
                    <button type="submit" class="btn btn-upload btn-lg w-100 mt-3">Mesclar Arquivos</button>
                </form>
            </div>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    '''

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
