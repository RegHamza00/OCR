from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from flask_session import Session 
from dotenv import load_dotenv
import configparser
import os
import openai
from PIL import Image
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError
from google.cloud import vision
from google.cloud import vision_v1
from google.cloud import storage #not used anymore 
from google.cloud import exceptions
from datetime import datetime
import io
import json
import re
from flask_mysqldb import MySQL
import clickup
import requests
import asyncio
import time
import json
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored
import spacy
from dateutil import parser
import base64
import locale



GPT_MODEL = os.getenv("OPENAI_MODEL")  


# Set the path to your Google Cloud API credentials JSON file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'ocr-theprime-d9f4cdb8014e.json'

# Initialize the Vision client
client = vision_v1.ImageAnnotatorClient()


load_dotenv()  # Load environment variables from the .env file

app = Flask(__name__)
mysql = MySQL(app)
app.secret_key = os.getenv("secret_key")

# Configure MySQL database
app.config['MYSQL_USER'] = os.environ["DB_USER"]
app.config['MYSQL_PASSWORD'] = os.environ["DB_PASSWORD"]
app.config['MYSQL_DB'] = os.environ["DB_NAME"]
app.config['MYSQL_HOST'] = os.environ["DB_HOST"]
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_MAX_SIZE'] = 4096
app.config['SESSION_TYPE'] = 'filesystem'  # file-based storage
Session(app)


# OpenAI API Auth
api_key = os.getenv("key")
openai.api_key = api_key
api_endpoint = 'https://api.openai.com/v1/engines/gpt-3.5-turbo-0613/completions'  # Endpoint for GPT-3



@app.route('/clickup/callback')
def clickup_callback(billet_tutar, incintive, toplam_totari, passenger_name, choosen_checkbox):   # NEED TO BE CHANGED ON NEXT VERSION FOR GENERAL USE <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    list_id = ""

    url = "https://api.clickup.com/api/v2/list/" + list_id + "/task/"

    try:
        
        query = {
        "custom_task_ids": "true",
        "team_id": 
        }

        payload = {
        "name": f" {choosen_checkbox} > {passenger_name}",   
        "description": f"Bill Amount: {billet_tutar} - Incintive: {incintive} - Total amount: {toplam_totari} - Passenger name: {passenger_name}" ,
        "check_required_custom_fields": True,
        "custom_fields": [
            {
            "id": "*****************************",
            "value": 
            }
        ]
        
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": os.getenv("clickup_api_key")
        }
       

        response = requests.post(url, json=payload, headers=headers, params=query)

        data = response.json()
        return data

    except requests.exceptions.HTTPError as http_err:
        # Log the HTTP error and return an error response
        print(f"HTTP error occurred: {http_err}")
        return {"error": "HTTP error occurred"}

    except Exception as e:
        # Log any other exception and return an error response
        print(f"An error occurred: {e}")
        return {"error": "An error occurred"}
    
def extract_information_for_Flight_ticket(result):
    try:
        flight_amount_match = re.search(r'flight\s*amount\s*([^\n]+)', result, re.IGNORECASE)
        flight_amount = flight_amount_match.group(1).strip() if flight_amount_match else None
       
        # Extracting currency
        currency_match = re.search(r'Currency:\s*([A-Z]{3})', result, re.IGNORECASE)
        currency = currency_match.group(1).strip() if currency_match else None

    except Exception as e:
        print(f"Error during flight ticket information extraction: {e}")
        return None, None
    
    

def extract_information_for_Fatura(result):
    try:
        # Extracting BİLET TUTAR
        billet_tutar_match = re.search(r'BİLET\s*TUTAR:\s*([^\n]+)', result, re.IGNORECASE)
        billet_tutar = billet_tutar_match.group(1).strip() if billet_tutar_match else None

        # Extracting İND. BED.(%60)
        incintive_match = re.search(r'İND\.\s*BED\.\(%\d+\):\s*([^\n]+)', result, re.IGNORECASE)
        incintive = incintive_match.group(1).strip() if incintive_match else None

        toplam_totari_match = re.search(r'Toplam\s*Tutar.*?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', result, re.I)
        toplam_totari = toplam_totari_match.group(1).strip() if toplam_totari_match else None

        passenger_name_match = re.search(r'Passenger\s+Name:\s*([^\n]+)', result, re.IGNORECASE)
        passenger_name = passenger_name_match.group(1).strip() if passenger_name_match else None


        return billet_tutar, incintive, toplam_totari, passenger_name

    except Exception as e:
        print(f"Error during extraction: {e}")
        return None, None

@retry(wait=wait_random_exponential(multiplier=1, max=40))
def initFatura(text_extracted, company_name, tools=None, tool_choice=None, model=GPT_MODEL):
    
    if text_extracted is None:
        print("Error: Text to be processed is None.")
        return None

    
    conversation = [
        {"role": "system", "content": "You are a document classifier, and you must give brief response."},
        {"role": "user", "content": f"******************."},
        {"role": "assistant", "content": str(text_extracted)}
    ]
    try:
          
        print("OpenAI API...")
          
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=conversation,
            temperature=0.5,
            timeout=20, 
        )
                
        result = response.choices[-1].message.get("content", "")

        billet_tutar, incintive, toplam_totari, passenger_name  = extract_information_for_Fatura(result)


        if billet_tutar and incintive and toplam_totari:
            print("billet tutar", billet_tutar)
            print("Incintive", incintive)
            print("Toplam Totari", toplam_totari)
            print("Passenger name", passenger_name)
            #need to CREATE NEW PARAMETER THAT INCLUDE ONLY TWO 
            #clickup_callback(billet_tutar, incintive, toplam_totari, passenger_name, company_name)

        else:
            print("Toplam totari or Fatura tarihi not found in the Document")

        return billet_tutar, incintive, toplam_totari, passenger_name
        
    except Exception as e:
        print(f"Error during API request - : {e}")
        return None

# @retry(wait=wait_random_exponential(multiplier=1, max=40))
# def initFlight(passenger, text_extracted, company_name, tools=None, tool_choice=None, model=GPT_MODEL):
   
#     conversation = [
#         {"role": "system", "content": "You are an assistant answering questions based on document content."},
#         {"role": "user", "content": f"is {passenger} existe on this document, Answer by Yes or No."},
#         {"role": "assistant", "content": str(text_extracted)}
#     ]
#     try:
        
#         print("OpenAI API...")
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo-0613",
#             messages=conversation,
#             temperature=0.6,
#             timeout=20, 
#         )
                
#         result = response.choices[-1].message.get("content", "")

#         if "yes" in result.lower().strip():
#             print("Flight ticket belongs to The invoice uploaded.")      
#             # ClickUp Calling Function
#             # clickup_callback(passenger_name, booking_date, flight_date, Booking_reference, company_name, choosen_checkbox)
#             return True
#         else:
#             print(passenger, " not found ")
#             return False

#         return "Flight ticket belongs to The invoice uploaded."

#     except Exception as e:
#         print(f"Error during API request: - {e}")
#         return None

# Helper function to get the last uploaded OCR JSON file
def get_last_uploaded_blob(bucket, prefix):
    blobs = list(bucket.list_blobs(prefix=prefix))
    if blobs:
        # Sort blobs by their updated time in descending order
        blobs.sort(key=lambda x: x.updated, reverse=True)
        return blobs[0]
    else:
        return None

def convert_pdf_to_images(path):
    """Converts PDF to images and returns the list of image paths."""
    try:
        # Use pdf2image library to convert PDF to images
        pages = convert_from_path(path, 300)  # You can adjust the DPI as needed
        image_paths = []

        for i, page in enumerate(pages):
            # Save each page as an image
            image_path = f"page_{i + 1}.png"
            page.save(image_path, "PNG")
            image_paths.append(image_path)

        return image_paths
    except PDFPageCountError:
        print("PDFPageCountError: Unable to get page count. The file may not be a valid PDF.")
        return []
    except Exception as e:
        print(f"Error during PDF conversion: {e}")
        return []


def async_detect_document(path):
    # Converting PDF to images
    image_paths = convert_pdf_to_images(path)

    # Process each image using detect_text function
    all_text = []
    for image_path in image_paths:
        text = detect_text(image_path)
        all_text.append(text)
    return ''.join(all_text)

#Detecting Text in Images
def detect_text(path):
    """Detects text in the file."""
    
    allowed_extensions = {'.jpg', '.jpeg', '.png'}

    client = vision.ImageAnnotatorClient()

    # Get the file extension
    file_extension = os.path.splitext(path)[1].lower()

    if file_extension not in allowed_extensions:
        raise Exception("Desteklenmeyen dosya formatı. Yalnızca JPG, JPEG ve PNG dosyalarına izin verilir.")

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    try:
        response = client.text_detection(image=image)
    except Exception as e:
        print(f"Error during text detection: {e}")

    texts = response.text_annotations
    extracted_text = ""

    for text in texts:
        extracted_text+=text.description + '\n'

        vertices = [
            f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
        ]

        print("bounds: {}".format(",".join(vertices)))

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )
    
    return extracted_text

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            # Authenticate user - MySQL query
            with mysql.connection.cursor() as cursor:
                query = "SELECT username, password, company_name FROM users WHERE username = %s AND password = %s"
                cursor.execute(query, (username, password))
                user = cursor.fetchone()

            if user:
                # Successful login, store user information in the session
                print("User authenticated successfully")
                session["user_id"] = user[0]
                session["company_name"] = user[2]

                # Store ClickUp session data in the session
                clickup_data = clickup_callback()
                # session["clickup_data"] = clickup_data

                return redirect(url_for("form"))
            else:
                error = "Invalid username or password."
                print("User authentication failed")

        except Exception as e:
            error = "Unable to connect to the database. Please try again later."
            print(f"Error connecting to the database: {e}")

    return render_template("login.html", error=error if "error" in locals() else None)

@app.route("/form", methods=["GET", "POST"])
def form():
    if "user_id" in session and "company_name" in session:
        return render_template("form.html")
    else:
        return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if 'user_id' in session and "company_name" in session:
        if request.method == "POST":
            
            selected_document_types = request.form.getlist("document_type")
            
            try:
                uploaded_file = request.files["file"] 
                # flight_ticket = request.files["flight"] 
                
                if not uploaded_file :
                    flash("One or more file not uploaded.")
                    return redirect(url_for("form"))
            except Exception as e:
                # Handle file upload errors
                print(f"Error handling file upload: {e}")
                flash("Error uploading file. Please try again.")
                return redirect(url_for("form"))

            selected_checkbox = ', '.join(selected_document_types)

            company_name = session.get("company_name", "")
            
            uploads_directory = os.path.join(app.root_path, "Uploads")
            # Create the "Uploads" directory if it doesn't exist
            os.makedirs(uploads_directory, exist_ok=True)
            # Saving the file to >>>
            file_path = os.path.join(uploads_directory, uploaded_file.filename)
            uploaded_file.save(file_path)

            # Check if extension is a PDF
            file_extension = uploaded_file.filename.split(".")[-1].lower()


            #for Flight Ticket
            # flight_ticket_path = os.path.join(uploads_directory, flight_ticket.filename)
            # flight_ticket.save(flight_ticket_path)
            # flight_ticket_extension = flight_ticket.filename.split(".")[-1].lower()

            
            # Saving the file to >>> Only work with Windows <<<<<<<
            #file_path = f"\\Users\\HP\\OneDrive\\Bureau\\PDFSCAN\\Uploads\\{uploaded_file.filename}"
            

            

            
            if uploaded_file:
                if file_extension == "pdf":
                    start_time=time.time()
                    text_extracted = async_detect_document(file_path)
                    # # Define the GCS paths for source and destination URIs
                    # gcs_source_uri = f"gs://ocrtheprime/{uploaded_file.filename}"

                    # # Get the list of blobs in the output folder
                    # client = storage.Client()
                    # bucket = client.bucket("ocrtheprime")
                    # blob_name = uploaded_file.filename
                    # blobs = list(bucket.list_blobs(prefix="output/"))

                    # # Determine the last uploaded file based on the order in blobs
                    # if blobs := list(bucket.list_blobs(prefix="output/")):
                    #     last_uploaded_blob = get_last_uploaded_blob(bucket, "output/")
                    #     if last_uploaded_blob:
                    #         last_uploaded_filename = last_uploaded_blob.name
                    #         # Use a consistent output filename in the "output" folder
                    #         gcs_destination_uri = f"gs://ocrtheprime/output/{uploaded_file.filename}.json"
                            
                    #         while bucket.blob(blob_name).exists():
                    #             base_name, extension = os.path.splitext(blob_name)
                    #             base_name += "_1"
                    #             blob_name = f"{base_name}{extension}"
                    #         # Upload the PDF to Google Cloud Storage
                    #         blob = bucket.blob(blob_name)
                    #         blob.upload_from_filename(file_path)


                            # Process the PDF asynchronously and get the extracted text
                            #text_extracted = async_detect_document(file_path)
                            
                           
                    # else:
                    #     # Handle the case when no blobs are found in the "output/" folder
                    #     print("No blobs found in the 'output/' folder.")
                else:
                    text_extracted = detect_text(file_path)
                
                
                result = initFatura(text_extracted, company_name)
                # passenger_info = result[3]

                # if flight_ticket:
                #     if flight_ticket_extension == "pdf":
                #         text_extracted = async_detect_document(flight_ticket_path)
                #     else:
                #         text_extracted = detect_text(flight_ticket_path)
                
                # flight_result = initFlight(passenger_info, text_extracted, company_name)
                # print("flight_result ....", flight_result)
                
                if result is None:
                  result = []
                
                end_time=time.time()
                print(f"Application took {end_time - start_time} seconds")
                
                if all(value is None for value in result):
                    error_message = "The document is not recognized as an invoice. Please upload a valide document.\n If you think it an error please reload the page and try again."
                    return render_template("result.html", result=result, error_message=error_message, selected_checkbox=selected_checkbox)
                else:
                    return render_template("result.html", result=result, selected_checkbox=selected_checkbox)

              

    flash("You need to log in first.")
    
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
