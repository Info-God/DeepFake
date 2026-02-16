import hashlib
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from report_generator import  generate_simple_report
import os
from detect import load_model, predict_video
from utils import compute_file_sha256
from web3 import Web3
import json
from datetime import datetime


ADMIN_PASSWORD = "admin123"
# Flask setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this!
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'webm'}

# Load detection model once
model = load_model()

# Initialize blockchain variables
GANACHE_URL = os.getenv("GANACHE_URL")
w3 = None
contract = None
contract_address = None
blockchain_connected = False

# Try to connect to blockchain
try:
    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    
    # Check connection
    if w3.is_connected():
        blockchain_connected = True
        print("✅ Connected to Ganache")
        
        # Try to load contract
        try:
            with open("contract/MediaRegistry.json", "r") as f:
                contract_data = json.load(f)
            
            contract_address = contract_data["address"]
            contract_abi = contract_data["abi"]
            
            contract = w3.eth.contract(
                address=contract_address,
                abi=contract_abi
            )
            print(f"✅ Contract loaded: {contract_address}")
            
        except FileNotFoundError:
            print("⚠️ Contract file not found. Run deploy_and_register.py first")
        except Exception as e:
            print(f"⚠️ Error loading contract: {e}")
            
    else:
        print("❌ Cannot connect to Ganache. Make sure it's running on http://127.0.0.1:7545")
        
except Exception as e:
    print(f"⚠️ Blockchain setup failed: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['video']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('Invalid file type. Allowed: mp4, avi, mov, mkv, flv, webm', 'error')
        return redirect(url_for('index'))
    
    # Save uploaded file
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(filepath)
    
    # Detect fake/real
    try:
        result = predict_video(filepath, model)
        fake_prob = round(result["avg_fake_probability"] * 100, 2)
        is_fake = result["is_fake"]
        frame_count = result.get("frame_count", 0)
    except Exception as e:
        flash(f'Detection error: {str(e)}', 'error')
        return redirect(url_for('index'))
    
    # Compute hash and check blockchain
    video_hash = compute_file_sha256(filepath)
    registered = False
    blockchain_data = {}
    
    if blockchain_connected and contract:
        try:
            # Use verifyMedia function from your contract
            exists, description, uploader, timestamp = contract.functions.verifyMedia(video_hash).call()
            
            if exists:
                registered = True
                blockchain_data = {
                    'verified': True,
                    'hash': video_hash,
                    'description': description,
                    'uploader': uploader,
                    'timestamp': timestamp,
                    'registered_date': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp > 0 else "Unknown"
                }
            else:
                blockchain_data = {
                    'verified': False,
                    'hash': video_hash,
                    'message': 'Video not registered on blockchain'
                }
        except Exception as e:
            blockchain_data = {
                'verified': False,
                'hash': video_hash,
                'error': str(e)
            }
    else:
        blockchain_data = {
            'verified': False,
            'hash': video_hash,
            'error': 'Blockchain not connected'
        }
    
    # Store file info in session for potential registration
    session['last_video'] = {
        'path': filepath,
        'hash': video_hash,
        'filename': filename,
        'is_fake': is_fake
    }
    
    # Store analysis data for report generation
    session['last_analysis'] = {
        'filename': filename,
        'hash': video_hash,
        'is_fake': is_fake,
        'fake_prob': fake_prob,
        'frame_count': frame_count,
        'registered': registered,
        'desc': blockchain_data.get('description', ''),
        'uploader': blockchain_data.get('uploader', ''),
        'timestamp': blockchain_data.get('registered_date', '')
    }
    
    return render_template(
        'result.html',
        filename=filename,
        fake_prob=fake_prob,
        is_fake=is_fake,
        frame_count=frame_count,
        registered=registered,
        blockchain_data=blockchain_data,
        blockchain_connected=blockchain_connected,
        show_report_button=True  # New flag for report generation
    )

@app.route('/verify_only', methods=['POST'])
def verify_only():
    """Only verify on blockchain without AI detection"""
    if 'video' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['video']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('Invalid file type', 'error')
        return redirect(url_for('index'))
    
    # Save file temporarily
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_' + filename)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(filepath)
    
    # Generate hash
    video_hash = compute_file_sha256(filepath)
    
    # Verify on blockchain
    blockchain_data = {}
    if blockchain_connected and contract:
        try:
            exists, description, uploader, timestamp = contract.functions.verifyMedia(video_hash).call()
            
            if exists:
                blockchain_data = {
                    'verified': True,
                    'hash': video_hash,
                    'description': description,
                    'uploader': uploader,
                    'timestamp': timestamp,
                    'registered_date': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp > 0 else "Unknown"
                }
            else:
                blockchain_data = {
                    'verified': False,
                    'hash': video_hash,
                    'message': 'Video not registered on blockchain'
                }
        except Exception as e:
            blockchain_data = {
                'verified': False,
                'hash': video_hash,
                'error': str(e)
            }
    else:
        blockchain_data = {
            'verified': False,
            'hash': video_hash,
            'error': 'Blockchain not connected'
        }
    
    # Clean up temp file
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return render_template('verify_only.html',
                         filename=filename,
                         blockchain_data=blockchain_data,
                         blockchain_connected=blockchain_connected)

@app.route('/register_video', methods=['POST'])
def register_video():
    """Register a video on blockchain"""
    if not blockchain_connected or not contract:
        flash('Blockchain not connected', 'error')
        return redirect(url_for('index'))
    
    if 'last_video' not in session:
        flash('No video to register', 'error')
        return redirect(url_for('index'))
    
    video_info = session['last_video']
    
    # Don't register if AI detected as fake
    if video_info['is_fake']:
        flash('Cannot register: Video detected as fake by AI', 'error')
        return redirect(url_for('index'))
    
    # Get description from form
    description = request.form.get('description', 'Verified Authentic Video')
    
    # You'll need to import your PRIVATE_KEY and ACCOUNT_ADDRESS
    # For testing, you can hardcode them or get from environment
    PRIVATE_KEY = "0x292b950ec019daf475f79055aea7e00dd3cefbb039f40e35f86601f464154ff9"  # From your deploy script
    ACCOUNT_ADDRESS = "0x5cC49064eEA0C9f4d16f0f1Ca1b79C736048690d"  # From your deploy script
    
    try:
        # Build transaction
        nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)
        
        tx = contract.functions.registerMedia(video_info['hash'], description).build_transaction({
            "chainId": 1337,
            "from": ACCOUNT_ADDRESS,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": w3.to_wei("20", "gwei")
        })
        
        # Sign and send transaction
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        flash(f'✅ Video registered on blockchain! Transaction: {tx_hash.hex()[:20]}...', 'success')
        
    except Exception as e:
        flash(f'Registration failed: {str(e)}', 'error')
    
    return redirect(url_for('index'))


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash('Incorrect password', 'error')
    
    # Pass required variables to template
    return render_template('admin_login.html',
                         contract_address=contract_address,
                         blockchain_connected=blockchain_connected)

@app.route('/admin_register', methods=['POST'])
def admin_register():
    """Admin registers a video on blockchain"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if 'video' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('admin_panel'))
    
    file = request.files['video']
    description = request.form.get('description', 'Admin Registered Video')
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin_panel'))
    
    if not allowed_file(file.filename):
        flash('Invalid file type', 'error')
        return redirect(url_for('admin_panel'))
    
    # Save the file
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'admin_' + filename)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(filepath)
    
    # Generate hash
    video_hash = compute_file_sha256(filepath)
    
    # Register on blockchain
    PRIVATE_KEY = "0x292b950ec019daf475f79055aea7e00dd3cefbb039f40e35f86601f464154ff9"
    ACCOUNT_ADDRESS = "0x5cC49064eEA0C9f4d16f0f1Ca1b79C736048690d"
    
    try:
        # Check if already registered
        exists, _, _, _ = contract.functions.verifyMedia(video_hash).call()
        if exists:
            flash('Video already registered on blockchain', 'info')
            return redirect(url_for('admin_panel'))
        
        # Register on blockchain
        nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)
        
        tx = contract.functions.registerMedia(video_hash, description).build_transaction({
            "chainId": 1337,
            "from": ACCOUNT_ADDRESS,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": w3.to_wei("20", "gwei")
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        flash(f'✅ Video registered successfully! Transaction: {tx_hash.hex()[:20]}...', 'success')
        
    except Exception as e:
        flash(f'Registration failed: {str(e)}', 'error')
    
    # Clean up
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return redirect(url_for('admin_panel'))


@app.route('/admin_panel')
def admin_panel():
    """Admin panel to register videos"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Get list of registered videos (you need to track these)
    registered_videos = []
    
    # Get stats
    stats = {
        'blockchain_connected': blockchain_connected,
        'registered_count': 0
    }
    
    if blockchain_connected and contract:
        try:
            count = contract.functions.getRegisteredCount().call()
            stats['registered_count'] = count
        except:
            stats['registered_count'] = "N/A"
    
    return render_template('admin.html',
                         registered_videos=registered_videos,
                         stats=stats,
                         contract_address=contract_address,
                         blockchain_connected=blockchain_connected)
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

# Add new route for report generation
@app.route('/generate_report/<filename>')
def generate_report(filename):
    """Generate and download verification report"""
    
    # Get the last analysis results from session
    if 'last_analysis' not in session:
        flash('No analysis data found', 'error')
        return redirect(url_for('index'))
    
    analysis_data = session['last_analysis']
    
    # Prepare data for report
    video_info = {
        'filename': filename,
        'hash': analysis_data.get('hash', 'N/A'),
        'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    ai_result = {
        'is_fake': analysis_data.get('is_fake', False),
        'fake_probability': analysis_data.get('fake_prob', 0),
        'frame_count': analysis_data.get('frame_count', 0),
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    blockchain_result = {
        'verified': analysis_data.get('registered', False),
        'description': analysis_data.get('desc', ''),
        'uploader': analysis_data.get('uploader', ''),
        'registered_date': analysis_data.get('timestamp', ''),
        'contract_address': contract_address,
        'blockchain': 'Ethereum (Ganache)'
    }
    
    try:
        # Generate report
        report_path = generate_simple_report(filename, ai_result, blockchain_result)
        
        # Store in session for download
        session['last_report'] = report_path
        
        return render_template('report_ready.html', 
                             filename=filename,
                             report_path=report_path)
        
    except Exception as e:
        flash(f'Report generation failed: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download_report/<path:filename>')
def download_report(filename):
    """Download the generated report"""
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        flash(f'Download failed: {str(e)}', 'error')
        return redirect(url_for('index'))



# Add these routes AFTER the index() route but BEFORE the upload_video() route

@app.route('/detect')
def upload_video_page():
    """Page for uploading videos for full analysis"""
    return render_template('upload_video.html',
                         stats={'blockchain_connected': blockchain_connected},
                         contract_address=contract_address,
                         blockchain_connected=blockchain_connected)

@app.route('/verify')
def verify_only_page():
    """Page for blockchain-only verification"""
    return render_template('verify_only.html',  # Create this template
                         stats={'blockchain_connected': blockchain_connected},
                         contract_address=contract_address,
                         blockchain_connected=blockchain_connected)

@app.route('/')
def index():
    # Get blockchain stats
    stats = {
        'blockchain_connected': blockchain_connected,
        'registered_count': 0
    }
    
    if blockchain_connected and contract:
        try:
            # Try to get count from contract
            # Note: Your contract might not have getRegisteredCount function
            # If it doesn't, just show N/A
            try:
                count = contract.functions.getRegisteredCount().call()
                stats['registered_count'] = count
            except:
                # Try alternative: check if any function exists
                stats['registered_count'] = "N/A"
        except:
            stats['registered_count'] = "N/A"
    
    return render_template('index.html', 
                         stats=stats,
                         contract_address=contract_address,
                         blockchain_connected=blockchain_connected)



if __name__ == '__main__':
    # Create uploads folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Create reports folder
    reports_folder = "static/reports"
    if not os.path.exists(reports_folder):
        os.makedirs(reports_folder)
    
    app.run(debug=True, port=5000)