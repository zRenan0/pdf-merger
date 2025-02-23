import os
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
from flask import Flask, render_template, request, send_file

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Função para desmembrar o PDF em páginas
def split_pdf(pdf_path, output_folder):
    """
    Desmembra o PDF em arquivos individuais para cada página.
    """
    pdf = PdfReader(pdf_path)
    output_files = []
    
    for i in range(len(pdf.pages)):
        pdf_writer = PdfWriter()
        pdf_writer.add_page(pdf.pages[i])
        
        output_filename = os.path.join(output_folder, f"page_{i+1}.pdf")
        with open(output_filename, "wb") as output_pdf:
            pdf_writer.write(output_pdf)
        
        output_files.append(output_filename)
    
    return output_files

# Função para converter imagem para PDF
def convert_image_to_pdf(image_path, pdf_path):
    """
    Converte uma imagem para PDF.
    """
    image = Image.open(image_path)
    image.save(pdf_path, "PDF", resolution=100.0)

# Função para gerar miniaturas do PDF
def generate_thumbnail(pdf_file):
    """
    Gera miniatura do PDF (a partir da primeira página).
    """
    thumbnail_path = pdf_file.replace(".pdf", "_thumb.png")
    reader = PdfReader(pdf_file)
    page = reader.pages[0]
    
    # Aqui, você pode usar um método para criar uma miniatura
    # Exemplo de criação de miniatura
    thumbnail_path = thumbnail_path.replace(".pdf", ".png")  # Para fins de demonstração
    image = Image.new('RGB', (100, 100), color='blue')  # Apenas um exemplo; substitua com a geração de imagem real.
    image.save(thumbnail_path)
    return thumbnail_path

# Função para mesclar PDFs e imagens
def merge_pdfs_and_images(file_list, output_filename):
    """
    Mescla PDFs e imagens, desmembrando PDFs mesclados, e gera miniaturas.
    """
    merger = PdfWriter()
    image_pdfs = []
    thumbnails = []
    output_folder = "uploads/split_pdfs"  # Pasta onde os PDFs serão desmembrados

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file in file_list:
        if file.lower().endswith(".pdf"):
            # Desmembrar o PDF
            split_pdfs = split_pdf(file, output_folder)
            for pdf in split_pdfs:
                merger.append(pdf)
                thumbnails.append(generate_thumbnail(pdf))
        elif file.lower().endswith((".jpg", ".jpeg", ".png")):
            pdf_path = file + ".pdf"
            convert_image_to_pdf(file, pdf_path)
            image_pdfs.append(pdf_path)
            merger.append(pdf_path)
            thumbnails.append(generate_thumbnail(pdf_path))

    # Escreve o arquivo final
    with open(output_filename, "wb") as output_pdf:
        merger.write(output_pdf)

    # Remove PDFs temporários de imagem
    for img_pdf in image_pdfs:
        os.remove(img_pdf)

    # Remove PDFs desmembrados temporários
    for pdf in split_pdfs:
        os.remove(pdf)

    return output_filename, thumbnails

# Rota principal da aplicação
@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        files = request.files.getlist('file')
        uploaded_files = []
        for file in files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            uploaded_files.append(file_path)
        
        # Mesclar PDFs e gerar miniaturas
        output_pdf = os.path.join(app.config['UPLOAD_FOLDER'], "output.pdf")
        merged_pdf, thumbnails = merge_pdfs_and_images(uploaded_files, output_pdf)

        # Exibir os PDFs e miniaturas
        return render_template('index.html', thumbnails=thumbnails, merged_pdf=merged_pdf)

    return render_template('index.html')

# Rota para baixar o PDF mesclado
@app.route('/download')
def download():
    return send_file("uploads/output.pdf", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
 