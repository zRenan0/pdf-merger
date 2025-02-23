from flask import Flask, render_template, request, send_file, jsonify
import os
from PyPDF2 import PdfReader, PdfMerger
from PIL import Image
import io

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
MERGED_FILE = "merged.pdf"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Função para converter imagem para PDF
def convert_image_to_pdf(image_path, pdf_path):
    image = Image.open(image_path)
    image.save(pdf_path, "PDF", resolution=100.0)

# Função para criar miniaturas de uma página PDF
def create_pdf_thumbnail(pdf_path, page_number):
    reader = PdfReader(pdf_path)
    page = reader.pages[page_number]
    writer = PdfMerger()
    writer.append(pdf_path, pages=(page_number, page_number + 1))

    # Salvar a página em uma imagem
    pdf_io = io.BytesIO()
    writer.write(pdf_io)
    pdf_io.seek(0)
    
    image = Image.open(pdf_io)
    thumbnail_path = pdf_path + f"_thumb_{page_number}.png"
    image.thumbnail((100, 150))  # Tamanho da miniatura
    image.save(thumbnail_path)
    return thumbnail_path

# Função para desmembrar um PDF em várias páginas e criar miniaturas
def split_pdf(input_pdf, output_folder):
    reader = PdfReader(input_pdf)
    output_files = []
    thumbnails = []

    for page_num in range(len(reader.pages)):
        writer = PdfMerger()
        writer.append(input_pdf, pages=(page_num, page_num + 1))
        output_filename = os.path.join(output_folder, f"page_{page_num + 1}.pdf")
        writer.write(output_filename)
        output_files.append(output_filename)

        # Criar miniatura para a página
        thumb_path = create_pdf_thumbnail(input_pdf, page_num)
        thumbnails.append(thumb_path)

    return output_files, thumbnails

# Função para mesclar PDFs e imagens
def merge_pdfs_and_images(file_list, output_filename):
    merger = PdfMerger()
    image_pdfs = []
    all_thumbnails = []

    for file in file_list:
        if file.lower().endswith(".pdf"):
            if len(PdfReader(file).pages) > 1:
                output_folder = os.path.join(UPLOAD_FOLDER, "split")
                os.makedirs(output_folder, exist_ok=True)
                split_pdfs, thumbnails = split_pdf(file, output_folder)
                for split_pdf in split_pdfs:
                    merger.append(split_pdf)
                all_thumbnails.extend(thumbnails)
                for split_pdf in split_pdfs:
                    os.remove(split_pdf)
            else:
                merger.append(file)
                all_thumbnails.append(create_pdf_thumbnail(file, 0))  # Thumbnail para PDF de uma página
        elif file.lower().endswith((".jpg", ".jpeg", ".png")):
            pdf_path = file + ".pdf"
            convert_image_to_pdf(file, pdf_path)
            image_pdfs.append(pdf_path)
            merger.append(pdf_path)
            all_thumbnails.append(pdf_path + "_thumb_0.png")  # Miniatura para imagem

    merger.write(output_filename)
    merger.close()

    for img_pdf in image_pdfs:
        os.remove(img_pdf)

    return output_filename, all_thumbnails

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
        merged_file, thumbnails = merge_pdfs_and_images(ordered_file_paths, output_pdf)
        
        # Passar os thumbnails para o frontend
        return jsonify({'merged_file': merged_file, 'thumbnails': thumbnails})
    
    return '''
    <!doctype html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mesclar PDFs e Imagens</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
        <style>
            /* CSS atualizado para um design mais clean */
            body {
                background: url("/static/imagens/background.jpg") no-repeat center center fixed;
                background-size: cover;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            .container {
                background: rgba(255, 255, 255, 0.9);
                padding: 35px;
                border-radius: 12px;
                margin-top: 100px;
                box-shadow: 0px 15px 30px rgba(0, 0, 0, 0.1);
                max-width: 800px;
                text-align: center;
            }

            h2 {
                color: #333;
                font-weight: 700;
                margin-bottom: 30px;
                font-size: 32px;
            }

            .btn-submit {
                background: linear-gradient(135deg, #007bff, #0056b3);
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 10px;
                transition: 0.3s;
                border: none;
                width: 100%;
                font-size: 16px;
            }

            .btn-submit:hover {
                background: linear-gradient(135deg, #0056b3, #003c80);
            }

            #fileInput {
                margin-top: 30px;
            }

            .file-item {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                width: 120px;
                height: 150px;
                padding: 15px;
                border: 2px solid #ddd;
                background-color: rgba(255, 255, 255, 0.8);
                cursor: move;
                text-align: center;
                font-size: 12px;
                border-radius: 12px;
                box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s, box-shadow 0.2s;
                margin: 10px;
            }

            .file-item:hover {
                transform: scale(1.05);
                box-shadow: 0px 5px 20px rgba(0, 0, 0, 0.2);
            }

            .file-item img {
                width: 90px;
                height: 90px;
                object-fit: cover;
                border-radius: 8px;
                margin-bottom: 8px;
                border: 1px solid #ccc;
            }

            #preview {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                justify-content: center;
                margin-top: 20px;
            }

            .draggable {
                cursor: grab;
            }

            .draggable:active {
                cursor: grabbing;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Mesclar PDFs e Imagens</h2>

            <form id="uploadForm" method="post" enctype="multipart/form-data">
                <div class="mb-3">
                    <label for="fileInput" class="form-label">Selecione seus arquivos</label>
                    <input type="file" id="fileInput" name="files" multiple class="form-control" onchange="handleFileInput(event)">
                </div>
                <div id="preview" class="file-list"></div>
                <input type="hidden" id="orderedFiles" name="filesOrder">
                <button type="submit" class="btn-submit mt-3">Mesclar Arquivos</button>
            </form>
        </div>

        <script>
            function handleFileInput(event) {
                let files = Array.from(event.target.files);
                let preview = document.getElementById("preview");
                preview.innerHTML = "";

                files.forEach(file => {
                    let div = document.createElement("div");
                    div.classList.add("file-item", "draggable");
                    div.setAttribute("data-filename", file.name);
                    div.draggable = true;

                    let img = document.createElement("img");
                    if (file.type.includes("image")) {
                        img.src = URL.createObjectURL(file);
                    } else if (file.type === "application/pdf") {
                        img.src = "/static/imagens/pdf-icon.png";
                    }

                    let span = document.createElement("span");
                    span.innerText = file.name;

                    div.appendChild(img);
                    div.appendChild(span);
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
    </body>
</html>
    '''
