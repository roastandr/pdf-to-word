import os
import logging
from flask import Flask, render_template, request, send_file
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract
from docx import Document

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_pdf_to_word(pdf_path, output_path):
    """Convert PDF to DOCX with OCR fallback"""
    try:
        # Try text extraction first
        cv = Converter(pdf_path)
        cv.convert(output_path)
        cv.close()
        logger.info("Text-based conversion successful")
        return True
    except Exception as e:
        logger.warning(f"Text extraction failed, trying OCR: {e}")
        try:
            # OCR fallback
            images = convert_from_path(pdf_path, dpi=200, thread_count=2)
            doc = Document()
            for img in images:
                text = pytesseract.image_to_string(img)
                doc.add_paragraph(text)
            doc.save(output_path)
            logger.info("OCR conversion successful")
            return True
        except Exception as ocr_error:
            logger.error(f"OCR failed: {ocr_error}")
            return False

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def handle_conversion():
    if 'file' not in request.files:
        return {"error": "No file uploaded"}, 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return {"error": "No file selected"}, 400
    
    try:
        # Save uploaded file
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        word_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                               file.filename.replace('.pdf', '.docx'))
        file.save(pdf_path)
        
        # Convert
        if not convert_pdf_to_word(pdf_path, word_path):
            return {"error": "Conversion failed"}, 500
        
        # Return the file
        return send_file(word_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Server error: {e}")
        return {"error": str(e)}, 500
    finally:
        # Cleanup
        for path in [pdf_path, word_path]:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except:
                pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))