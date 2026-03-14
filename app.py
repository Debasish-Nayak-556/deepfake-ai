"""
DeepFake AI — Flask Application Server
=======================================
REST API + static file serving for the DeepFake AI web application.
Run:  python app.py
"""

import os
import uuid
import logging
from pathlib import Path

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from deepfake_engine import DeepFakeProcessor, VideoDeepFakeProcessor

# ──────────────────────────────────────────────
# App Configuration
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_DIR      = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
OUTPUT_FOLDER = BASE_DIR / "static" / "outputs"

ALLOWED_IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "bmp"}
ALLOWED_VIDEO_EXTS = {"mp4", "avi", "mov", "mkv"}
MAX_CONTENT_MB     = 50

# Ensure directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_MB * 1024 * 1024
app.config["UPLOAD_FOLDER"]      = str(UPLOAD_FOLDER)
app.config["SECRET_KEY"]         = os.environ.get("SECRET_KEY", "deepfake-dev-key-2024")

CORS(app, resources={r"/api/*": {"origins": "*"}})

# ──────────────────────────────────────────────
# AI Processor Singletons
# ──────────────────────────────────────────────

image_processor = DeepFakeProcessor()
video_processor = VideoDeepFakeProcessor()

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def allowed_file(filename: str, allowed: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def unique_filename(original: str) -> str:
    ext = Path(original).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


def save_upload(file, allowed: set) -> tuple[bool, str]:
    """Save an uploaded FileStorage object. Returns (ok, path_or_error)."""
    if not file or file.filename == "":
        return False, "No file provided."
    if not allowed_file(file.filename, allowed):
        return False, f"File type not allowed. Accepted: {allowed}"
    fname = unique_filename(secure_filename(file.filename))
    fpath = UPLOAD_FOLDER / fname
    file.save(str(fpath))
    return True, str(fpath)


# ──────────────────────────────────────────────
# Routes — UI
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/static/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(str(OUTPUT_FOLDER), filename)


# ──────────────────────────────────────────────
# Routes — API
# ──────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    """Health-check endpoint."""
    return jsonify({"status": "ok", "message": "DeepFake AI Server running 🚀"})


@app.route("/api/swap/image", methods=["POST"])
def swap_image():
    """
    POST /api/swap/image
    Form-data fields:
        source  — image file (face donor)
        target  — image file (face recipient)
        enhance — 'true' | 'false'  (optional, default true)
        blend   — float 0.0–1.0     (optional, default 0.85)
    """
    logger.info("Image swap request received.")

    # ── Validate uploads ──
    ok, source_path = save_upload(request.files.get("source"), ALLOWED_IMAGE_EXTS)
    if not ok:
        return jsonify({"success": False, "error": f"Source: {source_path}"}), 400

    ok, target_path = save_upload(request.files.get("target"), ALLOWED_IMAGE_EXTS)
    if not ok:
        return jsonify({"success": False, "error": f"Target: {target_path}"}), 400

    # ── Parse options ──
    enhance = request.form.get("enhance", "true").lower() == "true"
    blend   = float(request.form.get("blend", 0.85))
    blend   = max(0.0, min(1.0, blend))

    # ── Run processor ──
    output_fname = f"result_{uuid.uuid4().hex}.jpg"
    output_path  = str(OUTPUT_FOLDER / output_fname)

    result = image_processor.process(
        source_path=source_path,
        target_path=target_path,
        output_path=output_path,
        enhance=enhance,
        blend_strength=blend,
    )

    if not result.get("success"):
        return jsonify(result), 422

    result["output_url"] = f"/static/outputs/{output_fname}"
    return jsonify(result)


@app.route("/api/swap/video", methods=["POST"])
def swap_video():
    """
    POST /api/swap/video
    Form-data fields:
        source       — image file (face donor)
        target_video — video file (face recipient)
        frame_skip   — int  (optional, default 0)
        max_frames   — int  (optional, default 200)
    """
    logger.info("Video swap request received.")

    ok, source_path = save_upload(request.files.get("source"), ALLOWED_IMAGE_EXTS)
    if not ok:
        return jsonify({"success": False, "error": f"Source image: {source_path}"}), 400

    ok, video_path = save_upload(request.files.get("target_video"), ALLOWED_VIDEO_EXTS)
    if not ok:
        return jsonify({"success": False, "error": f"Target video: {video_path}"}), 400

    frame_skip = int(request.form.get("frame_skip", 0))
    max_frames = int(request.form.get("max_frames", 200))

    output_fname = f"video_result_{uuid.uuid4().hex}.mp4"
    output_path  = str(OUTPUT_FOLDER / output_fname)

    result = video_processor.process_video(
        source_image_path=source_path,
        target_video_path=video_path,
        output_video_path=output_path,
        frame_skip=frame_skip,
        max_frames=max_frames,
    )

    if not result.get("success"):
        return jsonify(result), 422

    result["output_url"] = f"/static/outputs/{output_fname}"
    return jsonify(result)


@app.route("/api/detect", methods=["POST"])
def detect_faces():
    """
    POST /api/detect
    Form-data: image — image file
    Returns face count and bounding boxes.
    """
    ok, img_path = save_upload(request.files.get("image"), ALLOWED_IMAGE_EXTS)
    if not ok:
        return jsonify({"success": False, "error": img_path}), 400

    from deepfake_engine import load_image, resize_keep_aspect
    img   = resize_keep_aspect(load_image(img_path))
    faces = image_processor.detector.detect(img)

    return jsonify({
        "success": True,
        "face_count": len(faces),
        "faces": faces,
    })


# ──────────────────────────────────────────────
# Error Handlers
# ──────────────────────────────────────────────

@app.errorhandler(413)
def too_large(_):
    return jsonify({"success": False, "error": f"File too large. Max {MAX_CONTENT_MB}MB."}), 413

@app.errorhandler(404)
def not_found(_):
    return jsonify({"success": False, "error": "Endpoint not found."}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"success": False, "error": "Internal server error."}), 500


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "═" * 55)
    print("  🤖  DeepFake AI Server")
    print("  📡  http://localhost:5000")
    print("═" * 55 + "\n")
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        threaded=True,
    )
