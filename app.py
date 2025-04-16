from flask import Flask, render_template, request, send_file, after_this_request
import os
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract
from docx import Document

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def convert_pdf_to_word(pdf_path, output_path):
    try:
        # Try text-based conversion first
        cv = Converter(pdf_path)
        cv.convert(output_path)
        cv.close()
    except:
        # Fallback to OCR for scanned PDFs
        images = convert_from_path(pdf_path)
        doc = Document()
        for img in images:
            text = pytesseract.image_to_string(img)
            doc.add_paragraph(text)
        doc.save(output_path)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'file' not in request.files:
            return "No file uploaded", 400
        
        file = request.files['file']
        if file.filename == '':
            return "No file selected", 400
        
        if file and file.filename.endswith('.pdf'):
            # Save uploaded PDF
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(pdf_path)
            
            # Convert to Word
            word_filename = file.filename.replace('.pdf', '.docx')
            word_path = os.path.join(app.config['UPLOAD_FOLDER'], word_filename)
            convert_pdf_to_word(pdf_path, word_path)
            
            # Clean up files after download
            @after_this_request
            def remove_files(response):
                try:
                    os.remove(pdf_path)
                    os.remove(word_path)
                except:
                    pass
                return response
            
            return send_file(word_path, as_attachment=True)
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))