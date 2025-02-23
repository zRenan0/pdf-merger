from flask import Flask, request, send_file, send_from_directory
import os
from PyPDF2 import PdfMerger
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
MERGED_FILE = "merged.pdf"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = "static/imagens"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def convert_image_to_pdf(image_path, pdf_path):
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

@app.route('/static/imagens/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.config['STATIC_FOLDER'], filename)

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
            document.addEventListener("DOMContentLoaded", function () {
                let preview = document.getElementById("preview");

                function handleFileInput(event) {
                    let files = Array.from(event.target.files);
                    preview.innerHTML = "";

                    files.forEach(file => {
                        let div = document.createElement("div");
                        div.classList.add("file-item", "draggable");
                        div.setAttribute("draggable", "true");
                        div.setAttribute("data-filename", file.name);

                        let img = document.createElement("img");
                        img.classList.add("thumbnail");

                        if (file.type.startsWith("image")) {
                            img.src = URL.createObjectURL(file);
                        } else if (file.name.endsWith(".pdf")) {
                            img.src = "https://cdn-icons-png.flaticon.com/512/337/337946.png"; // Ícone de PDF
                        } else {
                            img.src = "https://cdn-icons-png.flaticon.com/512/833/833593.png"; // Ícone genérico
                        }

                        let text = document.createElement("p");
                        text.innerText = file.name;

                        div.appendChild(img);
                        div.appendChild(text);

                        div.addEventListener("dragstart", dragStart);
                        div.addEventListener("dragover", dragOver);
                        div.addEventListener("drop", drop);

                        preview.appendChild(div);
                    });

                    updateOrder();
                }

                function dragStart(event) {
                    event.dataTransfer.setData("text/plain", event.target.dataset.filename);
                    event.target.classList.add("dragging");
                }

                function dragOver(event) {
                    event.preventDefault();
                    const dragging = document.querySelector(".dragging");
                    const afterElement = getDragAfterElement(preview, event.clientY);
                    if (afterElement == null) {
                        preview.appendChild(dragging);
                    } else {
                        preview.insertBefore(dragging, afterElement);
                    }
                }

                function drop(event) {
                    event.preventDefault();
                    document.querySelector(".dragging").classList.remove("dragging");
                    updateOrder();
                }

                function getDragAfterElement(container, y) {
                    const draggableElements = [...container.querySelectorAll(".draggable:not(.dragging)")];

                    return draggableElements.reduce((closest, child) => {
                        const box = child.getBoundingClientRect();
                        const offset = y - box.top - box.height / 2;
                        if (offset < 0 && offset > closest.offset) {
                            return { offset: offset, element: child };
                        } else {
                            return closest;
                        }
                    }, { offset: Number.NEGATIVE_INFINITY }).element;
                }

                function updateOrder() {
                    let filesOrder = [];
                    document.querySelectorAll("#preview .file-item").forEach(div => {
                        filesOrder.push(div.getAttribute("data-filename"));
                    });
                    document.getElementById("orderedFiles").value = filesOrder.join(",");
                }

                document.getElementById("fileInput").addEventListener("change", handleFileInput);
            });
        </script>
        <style>
            /* Ajuste da imagem de fundo para cobrir toda a área do mesclador */
            body {
                background-image: url('/static/imagens/background.jpg');
                background-size: contain; /* Mantém a proporção da imagem */
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed; /* Mantém a imagem fixa enquanto rola a página */
            }

            .container {
                background-color: rgba(255, 255, 255, 0.9); /* Mais opaco para melhor visibilidade */
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                max-width: 800px;
                margin: auto;
            }

            /* Aumentando os ícones dos arquivos */
            .file-item {
                display: flex;
                align-items: center;
                padding: 15px;
                border: 2px solid #ccc;
                margin: 5px;
                background-color: #ffffff;
                cursor: move;
                border-radius: 8px;
                box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.2);
                width: 100%;
            }

            .file-item img.thumbnail {
                width: 70px; /* Ícones maiores */
                height: 70px;
                margin-right: 15px;
                border-radius: 5px;
            }

            .dragging {
                opacity: 0.6;
            }

            .card-header {
                text-align: center;
                font-size: 22px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <div class="card">
                <div class="card-header text-center">
                    <h2>Mesclar PDFs e Imagens</h2>
                </div>
                <div class="card-body">
                    <form method="post" enctype="multipart/form-data">
                        <div class="mb-3">
                            <label for="fileInput" class="form-label">Selecione seus arquivos</label>
                            <input type="file" id="fileInput" name="files" multiple class="form-control">
                        </div>
                        <div id="preview" class="d-flex flex-wrap"></div>
                        <input type="hidden" id="orderedFiles" name="filesOrder">
                        <button type="submit" class="btn btn-primary w-100 mt-3">Mesclar Arquivos</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
