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
    page = doc[0]  # Primeira página
    pix = page.get_pixmap()  # Converte a página para uma imagem
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.thumbnail((100, 150))  # Ajusta o tamanho da miniatura
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
        uploaded_files = request.form.getlist('files')  # Arquivos ordenados do formulário
        file_paths = []
        
        for file in uploaded_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
            file_paths.append(file_path)
            
            # Gerar miniatura para PDF, se for o caso
            if file.lower().endswith(".pdf"):
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
<script>
    let draggedElement = null;

    document.addEventListener("dragstart", function(e) {
        draggedElement = e.target;
    });

    document.addEventListener("dragover", function(e) {
        e.preventDefault();
    });

    document.addEventListener("drop", function(e) {
        if (e.target.classList.contains("draggable")) {
            e.preventDefault();
            draggedElement.parentNode.removeChild(draggedElement);
            e.target.parentNode.insertBefore(draggedElement, e.target);
            updateOrder();
        }
    });

    function updateOrder() {
        let filesOrder = [];
        let previewDivs = document.getElementById('preview').children;
        
        for (let div of previewDivs) {
            filesOrder.push(div.getAttribute('data-filename'));
        }

        document.getElementById('orderedFiles').value = filesOrder.join(',');
    }

    function handleFileInput(event) {
        let files = event.target.files;
        let preview = document.getElementById("preview");
        preview.innerHTML = ''; // Limpa a pré-visualização

        // Cria uma lista de arquivos e ordena por nome
        let fileArray = Array.from(files);
        fileArray.sort((a, b) => a.name.localeCompare(b.name));

        // Adiciona o conteúdo do arquivo ao preview
        fileArray.forEach(file => {
            let div = document.createElement("div");
            div.classList.add("col-md-3", "mb-3", "draggable");
            div.setAttribute("draggable", "true");
            div.setAttribute("data-filename", file.name);

            let reader = new FileReader();
            reader.onload = function(e) {
                div.innerHTML = `<img src="${e.target.result}" class="img-thumbnail" style="cursor: pointer;">`;
                preview.appendChild(div);
            };
            reader.readAsDataURL(file);
        });
    }
</script>

<style>
    body {
        background-image: url('/static/imagens/background.jpg');
        background-size: cover;
        background-position: center center;
        background-attachment: fixed;
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
                            <input type="file" id="fileInput" name="files" multiple class="form-control" onchange="handleFileInput(event)">
                        </div>
                        <div id="preview" class="preview-container"></div>
                        <!-- Lista ordenada dos arquivos -->
                        <input type="hidden" id="orderedFiles" name="filesOrder">
                        <button type="submit" class="btn btn-upload btn-lg w-100 mt-3" onclick="updateOrder()">Mesclar Arquivos</button>
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
