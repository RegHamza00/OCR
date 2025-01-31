## Document OCR and Flight Ticket Invoice Classification

## Overview

This project is an OCR (Optical Character Recognition) and document classification system built using Flask, Google Cloud Vision API, OpenAI GPT models, and other Python libraries. It is designed to process uploaded documents (PDFs, images) to extract and classify information such as invoice details and flight ticket information. The application also integrates with ClickUp to create tasks based on the extracted information.

### Key Features

- **OCR (Text Extraction)**: Converts scanned PDFs and images to text using Google Cloud Vision API.
- **Document Classification**: Uses OpenAI GPT models to classify extracted information and handle various document types (e.g., invoices, flight tickets).
- **ClickUp Integration**: Automatically creates tasks on ClickUp based on document data.
- **User Authentication**: Users can log in to the platform to upload and process documents.

---

## Requirements

- Python 3.x
- Flask
- Flask-Session
- Flask-MySQLdb
- Google Cloud Vision API
- OpenAI API
- pdf2image
- PIL (Pillow)
- clickup
- requests
- tenacity
- spacy
- dateutil
- dotenv
- termcolor

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/your-repository.git
cd your-repository
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your environment variables:

```env
OPENAI_API_KEY=your_openai_api_key
GOOGLE_APPLICATION_CREDENTIALS=path_to_your_google_credentials_json
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
DB_HOST=your_database_host
SECRET_KEY=your_flask_secret_key
CLICKUP_API_KEY=your_clickup_api_key
```

---

## Usage

1. **Running the Application**

   After installation, you can run the Flask app with the following command:

   ```bash
   python app.py
   ```

   The app will run on `http://localhost:5000` by default.

2. **Login Process**

   - Access the application and log in with the user credentials stored in the MySQL database.
   - After login, the user can upload documents for processing.

3. **Document Upload**

   - Supported document types include PDFs, images (JPG, PNG, JPEG).
   - The application supports both invoice and flight ticket document types.
   - Users can select the document type to classify and upload the respective document.

4. **ClickUp Task Creation**

   After processing the document, relevant data is extracted, and tasks are automatically created on ClickUp (configured to integrate with ClickUp).

---

## Key Functions

- **detect_text()**: Extracts text from image files using Google Cloud Vision API.
- **convert_pdf_to_images()**: Converts PDF files to images for OCR processing.
- **initFatura()**: Processes the extracted text and classifies invoice-related data (e.g., ticket amounts).
- **clickup_callback()**: Creates tasks on ClickUp with the extracted data.

