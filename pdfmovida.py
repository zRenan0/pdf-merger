from flask import Flask, render_template, request, send_file
import os
from PyPDF2 import PdfMerger
from PIL import Image
from urllib.parse import urlencode



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
    
    return '''
    <!doctype html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mesclar PDFs e Imagens</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
        <script>
            function handleFileInput(event) {
                let files = Array.from(event.target.files);
                let preview = document.getElementById("preview");
                preview.innerHTML = "";

                files.forEach(file => {
                    let div = document.createElement("div");
                    div.classList.add("file-item", "draggable");
                    div.setAttribute("draggable", "true");
                    div.setAttribute("data-filename", file.name);
                    div.innerText = file.name;
                    preview.appendChild(div);
                });

                updateOrder();
            }

            function updateOrder() {
                let filesOrder = [];
                document.querySelectorAll("#preview .file-item").forEach(div => {
                    filesOrder.push(div.getAttribute("data-filename"));
                });
                document.getElementById("orderedFiles").value = filesOrder.join(",");
            }
        </script>
        <style>
            .file-item {
                padding: 10px;
                border: 1px solid #ccc;
                margin: 5px;
                background-color: #f8f9fa;
                cursor: move;
            }
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <div class="card">
                <div class="card-header">
                    <h2>Mesclar PDFs e Imagens</h2>
                </div>
                <div class="card-body">
                    <form method="post" enctype="multipart/form-data">
                        <div class="mb-3">
                            <label for="fileInput" class="form-label">Selecione seus arquivos</label>
                            <input type="file" id="fileInput" name="files" multiple class="form-control" onchange="handleFileInput(event)">
                        </div>
                        <div id="preview"></div>
                        <input type="hidden" id="orderedFiles" name="filesOrder">
                        <button type="submit" class="btn btn-primary w-100 mt-3" onclick="updateOrder()">Mesclar Arquivos</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
