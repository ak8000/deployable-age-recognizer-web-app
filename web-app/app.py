"""
Flask App for uploading and processing images.
"""

# import base64
import os
import queue
import tempfile
import threading
import time
import cv2

# import traceback
from datetime import datetime
from dotenv import load_dotenv
from flask import flash, Flask, jsonify, render_template, request, redirect, url_for
import bson
import gridfs

# from requests.exceptions import RequestException

# import werkzeug
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import requests

from openai import OpenAI


load_dotenv()

app = Flask(__name__)
task_queue = queue.Queue()
results = {}

openai_api_key = os.getenv("OPENAI_API_KEY")
openai = OpenAI(api_key=openai_api_key)

# MongoDB connection
serverOptions = {
    "socketTimeoutMS": 600000,  # 10 minutes
    "connectTimeoutMS": 30000,  # 30 seconds
    "serverSelectionTimeoutMS": 30000,  # 30 seconds
}

client = MongoClient("mongodb://mongodb:27017/", **serverOptions)
db = client["faces"]
fs = gridfs.GridFS(db)

images_collection = db["images_pending_processing"]
results_collection = db["image_processing_results"]

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


@app.route("/processing/<image_id>")
def processing(image_id):
    """
    Instead of threading, calling the process_image directly.
    """
    try:
        grid_out = fs.get(bson.ObjectId(image_id))
        _, temp_filepath = tempfile.mkstemp()
        with open(temp_filepath, "wb") as f:
            f.write(grid_out.read())
        with open(temp_filepath, "rb") as file:
            requests.post("http://machine-learning-client:5001/analyze", files={"file": file}, data={"image_id": str(image_id)}, timeout=1000)
        wait_interval = 5
        while True:
            current_image_doc = images_collection.find_one({"image_id": bson.ObjectId(image_id)})
            if current_image_doc and current_image_doc.get("status") == "success":
                return redirect(url_for("show_results", image_id=image_id))
            if current_image_doc and current_image_doc.get("status") == "failed":
                flash("Processing failed", "error")
                app.logger.error("Processing failed for image ID %s", image_id)
            time.sleep(wait_interval)
    except bson.errors.InvalidId:
        flash("Invalid image ID provided.", "error")
        app.logger.error("Invalid image_id provided.")
        return jsonify({"error": "Invalid image ID"}), 400
    
# capturing the photo
@app.route('/capture_photo', methods=['GET'])
def capture_photo():
    """
    Function to capture a user photo
    """
    camera = cv2.VideoCapture(0)  # initialize camera
    try:
        success, frame = camera.read()
        if success:
            save_directory = './shots/'
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)
            filename = f'captured_photo_{int(time.time())}.jpg'
            filepath = os.path.join(save_directory, filename)
            cv2.imwrite(filepath, frame)
            camera.release()
            return jsonify({'message': 'Photo captured and saved successfully', 'filename': filename}), 200
        else:
            return jsonify({'error': 'Failed to capture photo'}), 500
    except Exception as e:
        camera.release()  # Ensure camera is released on error
        return jsonify({'error': f'Error capturing photo: {str(e)}'}), 500

def allowed_file(filename):
    """
    Function that makes sure the uploaded picture file is in the allowed extensions

    Returns:
        A boolean
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def home():
    """
    Creates the template for the homepage
    """
    return render_template("index.html")


def process_task():
    """
    Function to process the tasks
    """
    while True:
        task_id = task_queue.get()  # Wait until a task is available
        print(f"Processing task {task_id}")
        time.sleep(10)  # Simulate a long-running task
        results[task_id] = "Task Completed"
        task_queue.task_done()


# Start a background thread to process tasks
threading.Thread(target=process_task, daemon=True).start()


@app.route("/start_task", methods=["POST"])
def start_task():
    """
    Function to start the tasks
    """
    task_id = request.json.get("task_id")
    task_queue.put(task_id)
    return jsonify({"message": "Task started", "task_id": task_id}), 202


@app.route("/get_result/<task_id>", methods=["GET"])
def get_result(task_id):
    """
    Gets the result
    """
    result = results.get(task_id)
    if result:
        return jsonify({"task_id": task_id, "status": result})
    return jsonify({"task_id": task_id, "status": "Processing"}), 202


app.secret_key = os.getenv("SECRET_KEY")


@app.route("/upload", methods=["GET", "POST"])
def upload_image():
    """
    Function to upload the image to be processed and ensure its availability in GridFS
    before starting processing. It handles file uploads and redirects to processing or
    reloads the upload form with error messages based on upload success.

    Returns:
        Redirect to the image processing page if upload is successful,
        or re-render the upload page with appropriate error messages if not.
    """
    if request.method == "POST":
        image = request.files.get("image")
        actual_age = request.form.get("age")
        if not image or not actual_age:
            flash("Missing data", "error")
            return jsonify({"error": "Missing data"}), 400
        if image.filename == "":
            flash("No selected file", "error")
            return jsonify({"error": "No selected file"}), 400
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            try:
                image_id = fs.put(image, filename=filename)
                images_collection.insert_one({
                    "image_id": image_id,
                    "filename": filename,
                    "status": "pending",
                    "upload_date": datetime.now(),
                    "actual_age": actual_age,
                })
                return jsonify({"message": "File uploaded successfully", "task_id": str(image_id)}), 200
            except Exception as e:
                flash("File upload failed", "error")
                app.logger.error("File upload failed: %s", str(e))
                return jsonify({"error": "File upload failed"}), 500
        else:
            flash("Invalid file type", "error")
            return jsonify({"error": "Invalid file type"}), 400
    return render_template("upload.html")


@app.route("/results/<image_id>")
def show_results(image_id):
    """
    Function that brings you to the results.html after the image is done processing

    Returns:
        result.html
    """
    try:
        obj_id = bson.ObjectId(image_id)
        specific_result = results_collection.find_one({"image_id": obj_id})
        if not specific_result:
            flash("Result not found.", "error")
            return redirect(url_for("home"))

        fun_prompt = f"Generate a fun message for someone who is {specific_result['predicted_age']} years old and seems {specific_result['dominant_emotion']}."
        fun_message = generate_fun_message(fun_prompt)

        # Fetch all results for the graph
        all_results = results_collection.find({})
        predicted_ages = []
        actual_ages = []
        labels = []
        index = 0
        for result in all_results:
            if "actual_age" in result and "predicted_age" in result:
                actual_ages.append(result["actual_age"])
                predicted_ages.append(result["predicted_age"])
                labels.append(str(index))  # Use the index or any specific identifier
                index += 1

        return render_template(
            "results.html",
            specific_result=specific_result,
            predicted_ages=predicted_ages,
            actual_ages=actual_ages,
            labels=labels,
            fun_message=fun_message
        )
    except bson.errors.InvalidId:
        flash("Invalid image ID.", "error")
        return redirect(url_for("home"))

def generate_fun_message(prompt):
    """
    Generates a fun message based on a prompt using OpenAI API.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        if response.choices:
            message = response.choices[0].message.content
            return message
        else:
            return "No completion found."
    except Exception as e:
        app.logger.error(f"Failed to generate message: {str(e)}")
        return "Error generating message."



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
