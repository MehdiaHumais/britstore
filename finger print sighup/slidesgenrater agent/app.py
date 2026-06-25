from flask import Flask, render_template, request, send_file, jsonify, session, redirect
from flask_cors import CORS
import os
import re
import fitz # PyMuPDF
import docx
import threading
import uuid
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from slides_agent import generate_slide_content, create_presentation, validate_slide_content, THEMES

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'slidewiz-super-secret-key-change-me')
CORS(app, resources={r"/*": {"origins": "*"}})

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    if hasattr(e, 'code'):
        return jsonify({"error": str(e)}), e.code
    # Handle non-HTTP exceptions
    print(f"[CRITICAL ERROR] {str(e)}")
    return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

# Ensure an output directory exists so we don't clutter the main dir
OUTPUT_DIR = "generated_presentations"
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"[*] Artifacts will be saved to: {os.path.abspath(OUTPUT_DIR)}")

# --- DATABASE SETUP ---
DB_PATH = "slides_db.sqlite"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()
# ----------------------

# Central memory for polling tasks to prevent browser timeouts
tasks = {}

@app.before_request
def log_request_info():
    print(f"[*] Request: {request.method} {request.path} from {request.remote_addr}")

def background_generate(task_id, topic, num_slides, detail_level, subtopics, subtopics_behavior, document_text, include_images, selected_theme, pdf_images=None):
    try:
        tasks[task_id]["status"] = "generating_ai"
        
        # Define a callback to update the task status in real-time
        def update_progress(msg):
            tasks[task_id]["status"] = "generating_ai" # keep status consistent
            tasks[task_id]["progress_text"] = msg
            print(f"[*] Task {task_id} Progress: {msg}")

        slides_data = generate_slide_content(topic, num_slides, detail_level, subtopics, subtopics_behavior, document_text, task_updater=update_progress)

        if isinstance(slides_data, str):
            tasks[task_id] = {"status": "error", "error": f"AI Parsing/Sync Issue: {slides_data}"}
            print(f"[!] Critical Generation Error for {task_id}: {slides_data}")
            return
        elif not slides_data:
            tasks[task_id] = {"status": "error", "error": "Failed to generate AI content (Empty Response)."}
            return

        # Content is already validated inside generate_slide_content

        tasks[task_id]["status"] = "building_ppt"
        
        # Failsafe Naming Logic
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = re.sub(r'[^a-zA-Z0-9\s]', '', topic).strip().replace(' ', '_')
        if not safe_topic: safe_topic = "Presentation"
        base_filename = f"{safe_topic[:30]}_{timestamp}"
        
        output_file = os.path.join(OUTPUT_DIR, f"{base_filename}.pptx")
        counter = 1
        while os.path.exists(output_file):
            output_file = os.path.join(OUTPUT_DIR, f"{base_filename}_{counter}.pptx")
            counter += 1
            
        # Add intermediate update
        tasks[task_id]["progress_text"] = "Rendering premium layouts and fetching high-res visuals..."
        print(f"[*] Rendering Task {task_id}")

        success = create_presentation(slides_data, topic, selected_theme, detail_level, include_images, output_file, pdf_images, task_updater=update_progress)
        
        if success:
            # Redundancy: Also save/copy as a fixed name in root for easy finding
            import shutil
            try:
                shutil.copy2(output_file, "latest_presentation.pptx")
                print(f"[+] Redundant copy saved to: latest_presentation.pptx")
            except Exception as copy_err:
                print(f"[!] Could not create redundant copy: {copy_err}")

            tasks[task_id] = {
                "status": "done", 
                "download_url": f"/download/{os.path.basename(output_file)}",
                "file_path": output_file
            }
            print(f"[+] Task {task_id} COMPLETED: {output_file}")
        else:
            tasks[task_id] = {"status": "error", "error": "Failed to build the PowerPoint file. Check if any file is open in another app."}
            
    except Exception as e:
        tasks[task_id] = {"status": "error", "error": f"Critical Error: {str(e)}"}

@app.route('/')
def index():
    # Pass themes to frontend
    themes_data = [{"id": k, "name": v["name"]} for k,v in THEMES.items()]
    return render_template('index.html', themes=themes_data)

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not name or not email or not password:
        return jsonify({"success": False, "error": "Name, email, and password are all required."}), 400
    if len(password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters."}), 400
        
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return jsonify({"success": False, "error": "An account with this email already exists. Please login."}), 409
            
            hashed = generate_password_hash(password)
            cursor.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", (name, email, hashed))
            conn.commit()
            user_id = cursor.lastrowid
            
            session['user_id'] = user_id
            session['user_name'] = name
            session['user_email'] = email
            session['is_fingerprint'] = False
            
            return jsonify({"success": True, "message": "Account created!", "user": {"name": name, "email": email, "is_fingerprint": False}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400
        
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({"success": False, "error": "No account found with this email. Please sign up."}), 404
            
            if not check_password_hash(user[3], password):
                return jsonify({"success": False, "error": "Incorrect password."}), 401
            
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_email'] = user[2]
            session['is_fingerprint'] = False
            
            return jsonify({"success": True, "message": "Login successful!", "user": {"name": user[1], "email": user[2], "is_fingerprint": False}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/me')
def get_me():
    if 'user_id' in session:
        return jsonify({"logged_in": True, "user": {"name": session['user_name'], "email": session['user_email'], "is_fingerprint": session.get('is_fingerprint', False)}})
    return jsonify({"logged_in": False})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/api/fingerprint', methods=['POST'])
def auth_fingerprint():
    data = request.json
    device_id = data.get('device_id', '').strip()
    name = data.get('name', '').strip()
    action = data.get('action', 'login') # 'login' or 'signup'
    
    if not device_id:
        return jsonify({"success": False, "error": "Device ID missing."}), 400
        
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            if action == 'signup':
                if not name:
                    return jsonify({"success": False, "error": "Name is required for signup."}), 400
                # Use device_id as the email, and a random secure string as the password hash
                dummy_email = f"{device_id}@fingerprint.local"
                dummy_hash = generate_password_hash(device_id + "secret_salt_123")
                
                try:
                    cursor.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", 
                                  (name, dummy_email, dummy_hash))
                    conn.commit()
                    user_id = cursor.lastrowid
                    session['user_id'] = user_id
                    session['user_name'] = name
                    session['user_email'] = dummy_email
                    session['is_fingerprint'] = True
                    return jsonify({"success": True, "message": "Fingerprint account created!", "user": {"name": name, "email": dummy_email, "is_fingerprint": True}})
                except sqlite3.IntegrityError:
                    return jsonify({"success": False, "error": "You already have a fingerprint account on this device. Please log in."}), 400
            
            else: # login
                dummy_email = f"{device_id}@fingerprint.local"
                cursor.execute("SELECT id, name, email FROM users WHERE email = ?", (dummy_email,))
                user = cursor.fetchone()
                
                if not user:
                    return jsonify({"success": False, "error": "No fingerprint account found. Please sign up with fingerprint first."}), 404
                
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['user_email'] = user[2]
                session['is_fingerprint'] = True
                
                return jsonify({"success": True, "message": "Fingerprint login successful!", "user": {"name": user[1], "email": user[2], "is_fingerprint": True}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not logged in."}), 401
    
    data = request.json
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        return jsonify({"success": False, "error": "Both current and new password are required."}), 400
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "New password must be at least 6 characters."}), 400
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (session['user_id'],))
            user = cursor.fetchone()
            
            if not user or not check_password_hash(user[0], current_password):
                return jsonify({"success": False, "error": "Current password is incorrect."}), 401
            
            new_hash = generate_password_hash(new_password)
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, session['user_id']))
            conn.commit()
            return jsonify({"success": True, "message": "Password changed successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/fingerprint-set-password', methods=['POST'])
def fingerprint_set_password():
    """Allows a fingerprint-only user to add a real email + password for backup/recovery."""
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not logged in."}), 401
    if not session.get('is_fingerprint', False):
        return jsonify({"success": False, "error": "This account already has a password."}), 400

    data = request.json
    new_email    = data.get('email', '').strip()
    new_password = data.get('new_password', '')

    if not new_email or not new_password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters."}), 400

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if the email is already taken by another account
            cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (new_email, session['user_id']))
            existing = cursor.fetchone()
            if existing:
                return jsonify({"success": False, "error": "This email is already used by another account."}), 400

            new_hash = generate_password_hash(new_password)
            cursor.execute("UPDATE users SET email = ?, password_hash = ? WHERE id = ?",
                          (new_email, new_hash, session['user_id']))
            conn.commit()

            # Update the session too
            session['user_email'] = new_email
            session['is_fingerprint'] = False

            return jsonify({"success": True, "message": "Backup password created! You can now login with email."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    # Because of File Uploads, we are now using FormData (form and files)
    topic = request.form.get("topic", "").strip()
    num_slides = int(request.form.get("num_slides", 5))
    detail_level = request.form.get("detail_level", "detailed")
    subtopics = request.form.get("subtopics", "").strip()
    subtopics_behavior = request.form.get("subtopics_behavior", "only")
    include_images = str(request.form.get("include_images")).lower() == "true"
    extract_pdf_images = str(request.form.get("extract_pdf_images")).lower() == "true"
    theme_id = str(request.form.get("theme", "2"))
    
    document_text = ""
    pdf_images = []
    
    if 'document' in request.files:
        file = request.files['document']
        if file.filename != '':
            filename_lower = file.filename.lower()
            if filename_lower.endswith('.txt'):
                document_text = file.read().decode('utf-8', errors='ignore')
            elif filename_lower.endswith('.pdf'):
                try:
                    pdf_bytes = file.read()
                    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                        # Extract Text (Efficiently stop early as we only need a bit)
                        for page in doc:
                            extracted = page.get_text()
                            if extracted:
                                document_text += extracted + "\n"
                            if len(document_text) > 8000: break # Stop once we have enough context
                        
                        # Extract Images if requested
                        if extract_pdf_images:
                            task_img_dir = os.path.join(OUTPUT_DIR, f"img_{uuid.uuid4().hex[:8]}")
                            os.makedirs(task_img_dir, exist_ok=True)
                            
                            img_count = 0
                            for page_index in range(len(doc)):
                                image_list = doc.get_page_images(page_index)
                                for img_index, img in enumerate(image_list):
                                    xref = img[0]
                                    try:
                                        base_image = doc.extract_image(xref)
                                        image_bytes = base_image["image"]
                                        img_ext = base_image["ext"]
                                    except:
                                        continue 
                                    img_path = os.path.join(task_img_dir, f"p{page_index}_i{img_index}.{img_ext}")
                                    with open(img_path, "wb") as f:
                                        f.write(image_bytes)
                                    pdf_images.append(img_path)
                                    img_count += 1
                                    if img_count >= 15: break # Don't over-extract
                                if img_count >= 15: break
                except Exception as e:
                    return jsonify({"error": f"Failed to read PDF: {e}"}), 400
            elif filename_lower.endswith('.docx'):
                try:
                    from io import BytesIO
                    doc = docx.Document(BytesIO(file.read()))
                    fullText = []
                    for para in doc.paragraphs:
                        fullText.append(para.text)
                    document_text = '\n'.join(fullText)
                except Exception as e:
                    return jsonify({"error": f"Failed to read Word document: {e}"}), 400
            
            # Use the PDF filename for the Presentation Title & PPTX name
            if not topic:
                topic = os.path.splitext(file.filename)[0].replace("_", " ").title()
            
            # Allow more context for the AI
            document_text = document_text[:10000].strip()
            
            if not document_text:
                return jsonify({"error": "Failed: Could not extract any readable text from this PDF document. It may be an image-based scan."}), 400

    smart_count = str(request.form.get("smart_count")).lower() == "true"
    
    # Extract topic from document filename if missing
    if not topic and 'document' in request.files:
        filename = request.files['document'].filename
        topic = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
    elif not topic:
        topic = "Strategic Business Analysis"
        
    if smart_count and document_text:
        # 1 slide per 1200 characters of text (approx 200 words), min 5 max 25
        num_slides = max(5, min(25, len(document_text) // 1200))
    
    if not topic and not document_text:
        return jsonify({"error": "Topic or Document is required."}), 400
    
    selected_theme = THEMES.get(theme_id, THEMES["2"])
    
    # Threading Task Creation
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "started"}
    
    print(f"[*] Task {task_id} initiated for: {topic}")
    worker = threading.Thread(target=background_generate, args=(task_id, topic, num_slides, detail_level, subtopics, subtopics_behavior, document_text, include_images, selected_theme, pdf_images))
    worker.daemon = True
    worker.start()
    
    return jsonify({"success": True, "task_id": task_id})

@app.route('/status/<task_id>')
def status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"status": "error", "error": "Unknown Task ID."}), 404
    return jsonify(task)

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    print("[START] Starting SlideWiz Frontend...")
    # disabled use_reloader to prevent file creation from wiping the tasks dictionary
    # Bind to 0.0.0.0 to allow connections from mobile devices/emulators
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
