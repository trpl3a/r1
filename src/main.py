from flask import Flask, render_template, request, jsonify, send_file, session
import xml.etree.ElementTree as ET
import tempfile
import csv
import io
import zipfile
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Create uploads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def parse_xml_file(file_path):
    """Parse XML file and find buttons missing e-sign feature"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Get filename without path
        filename = os.path.basename(file_path)
        
        # Find all buttons
        buttons_missing_esign = []
        
        # Find all button elements
        for button in root.findall('.//button'):
            button_name = button.get('name', 'Unknown')
            
            # Check if button has eSignature element with requireElectronicSignature="true"
            esign_element = button.find('./eSignature')
            
            if esign_element is None:
                buttons_missing_esign.append({
                    'filename': filename,
                    'button_name': button_name,
                    'reason': 'Missing eSignature element'
                })
            elif esign_element.get('requireElectronicSignature', '').lower() != 'true':
                buttons_missing_esign.append({
                    'filename': filename,
                    'button_name': button_name,
                    'reason': f'requireElectronicSignature is "{esign_element.get("requireElectronicSignature", "")}" instead of "true"'
                })
                
        return buttons_missing_esign
    except Exception as e:
        return [{
            'filename': os.path.basename(file_path),
            'button_name': 'ERROR',
            'reason': f'Failed to parse file: {str(e)}'
        }]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files part'}), 400
    
    files = request.files.getlist('files[]')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    # Create a unique session ID for this batch of uploads
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    
    # Create a directory for this session
    session_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    # Save files and process them
    all_results = []
    file_count = 0
    
    for file in files:
        if file and file.filename.endswith('.xml'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(session_dir, filename)
            file.save(file_path)
            file_count += 1
            
            # Parse the XML file
            results = parse_xml_file(file_path)
            all_results.extend(results)
    
    # Save results to session
    result_file = os.path.join(session_dir, 'results.json')
    with open(result_file, 'w') as f:
        json.dump(all_results, f)
    
    return jsonify({
        'success': True,
        'message': f'Successfully processed {file_count} files',
        'session_id': session_id,
        'count': len(all_results)
    })

@app.route('/results')
def get_results():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'No active session'}), 400
    
    result_file = os.path.join(app.config['UPLOAD_FOLDER'], session_id, 'results.json')
    if not os.path.exists(result_file):
        return jsonify({'error': 'No results found'}), 404
    
    with open(result_file, 'r') as f:
        results = json.load(f)
    
    return jsonify(results)

@app.route('/download/<format>')
def download_results(format):
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'No active session'}), 400
    
    result_file = os.path.join(app.config['UPLOAD_FOLDER'], session_id, 'results.json')
    if not os.path.exists(result_file):
        return jsonify({'error': 'No results found'}), 404
    
    with open(result_file, 'r') as f:
        results = json.load(f)
    
    if format == 'csv':
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Filename', 'Button Name', 'Reason'])
        
        for item in results:
            writer.writerow([
                item.get('filename', ''),
                item.get('button_name', ''),
                item.get('reason', '')
            ])
        
        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'missing_esign_buttons_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    elif format == 'text':
        # Create text file in memory
        output = io.StringIO()
        output.write("Buttons Missing E-Sign Feature\n")
        output.write("============================\n\n")
        
        for item in results:
            output.write(f"File: {item.get('filename', '')}\n")
            output.write(f"Button: {item.get('button_name', '')}\n")
            output.write(f"Reason: {item.get('reason', '')}\n")
            output.write("-" * 50 + "\n")
        
        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name=f'missing_esign_buttons_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        )
    
    else:
        return jsonify({'error': 'Invalid format'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
