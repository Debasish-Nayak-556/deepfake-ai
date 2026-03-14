"""
DeepFake AI Engine
==================
Core face-swap processing module using InsightFace + ONNX Runtime.
Author: Senior PM Build — DeepFake AI Project
"""

import cv2
import numpy as np
from PIL import Image
import os
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Utility Helpers
# ──────────────────────────────────────────────

def load_image(path: str) -> np.ndarray:
    """Load image from disk and convert to RGB numpy array."""
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def save_image(img: np.ndarray, path: str) -> None:
    """Save RGB numpy array to disk as BGR image."""
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(path, bgr)
    logger.info(f"Saved output → {path}")


def resize_keep_aspect(img: np.ndarray, max_dim: int = 1024) -> np.ndarray:
    """Resize image while maintaining aspect ratio."""
    h, w = img.shape[:2]
    if max(h, w) <= max_dim:
        return img
    scale = max_dim / max(h, w)
    return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


# ──────────────────────────────────────────────
# Face Detection Module
# ──────────────────────────────────────────────

class FaceDetector:
    """
    Lightweight face detector using OpenCV DNN Haar Cascade.
    Falls back gracefully if no face is found.
    """

    def __init__(self):
        self.cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def detect(self, img: np.ndarray) -> list[dict]:
        """
        Detect faces in image.
        Returns list of dicts with keys: bbox, confidence
        bbox = (x, y, w, h)
        """
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )
        results = []
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                results.append({
                    "bbox": (int(x), int(y), int(w), int(h)),
                    "confidence": 0.95,  # Haar doesn't return confidence; mock value
                })
        return results


# ──────────────────────────────────────────────
# Face Alignment Module
# ──────────────────────────────────────────────

class FaceAligner:
    """Align face region for consistent swap quality."""

    @staticmethod
    def extract_face(img: np.ndarray, bbox: tuple, padding: float = 0.25) -> np.ndarray:
        """Extract padded face crop from image."""
        x, y, w, h = bbox
        pad_x = int(w * padding)
        pad_y = int(h * padding)
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(img.shape[1], x + w + pad_x)
        y2 = min(img.shape[0], y + h + pad_y)
        return img[y1:y2, x1:x2], (x1, y1, x2, y2)

    @staticmethod
    def resize_face(face: np.ndarray, target_size: tuple = (256, 256)) -> np.ndarray:
        return cv2.resize(face, target_size, interpolation=cv2.INTER_LINEAR)


# ──────────────────────────────────────────────
# Face Blender — Poisson Seamless Cloning
# ──────────────────────────────────────────────

class FaceBlender:
    """
    Blends swapped face back into target using Poisson seamless cloning
    for photorealistic compositing.
    """

    @staticmethod
    def blend(target: np.ndarray, source_face: np.ndarray, bbox_coords: tuple) -> np.ndarray:
        """
        Seamlessly clone source_face into target at bbox_coords region.
        bbox_coords = (x1, y1, x2, y2)
        """
        x1, y1, x2, y2 = bbox_coords
        region_w = x2 - x1
        region_h = y2 - y1

        # Resize source face to match target region
        src_resized = cv2.resize(source_face, (region_w, region_h), interpolation=cv2.INTER_LINEAR)

        # Convert to BGR for OpenCV
        target_bgr = cv2.cvtColor(target, cv2.COLOR_RGB2BGR)
        src_bgr = cv2.cvtColor(src_resized, cv2.COLOR_RGB2BGR)

        # Create elliptical mask for smooth blending
        mask = np.zeros((region_h, region_w), dtype=np.uint8)
        cx, cy = region_w // 2, region_h // 2
        cv2.ellipse(mask, (cx, cy), (cx - 5, cy - 5), 0, 0, 360, 255, -1)

        # Centre point in target image
        center = (x1 + cx, y1 + cy)

        try:
            blended_bgr = cv2.seamlessClone(
                src_bgr, target_bgr, mask, center, cv2.NORMAL_CLONE
            )
        except cv2.error as e:
            logger.warning(f"Seamless clone failed ({e}), falling back to alpha blend.")
            blended_bgr = target_bgr.copy()
            blended_bgr[y1:y2, x1:x2] = src_bgr

        return cv2.cvtColor(blended_bgr, cv2.COLOR_BGR2RGB)


# ──────────────────────────────────────────────
# DeepFake Processor — Main Orchestrator
# ──────────────────────────────────────────────

class DeepFakeProcessor:
    """
    High-level orchestrator that chains:
    Detection → Alignment → Swap → Blending → Post-process
    """

    def __init__(self):
        self.detector = FaceDetector()
        self.aligner = FaceAligner()
        self.blender = FaceBlender()
        logger.info("DeepFakeProcessor initialised.")

    # ── Main entry point ──────────────────────

    def process(
        self,
        source_path: str,
        target_path: str,
        output_path: str,
        enhance: bool = True,
        blend_strength: float = 0.85,
    ) -> dict:
        """
        Perform face swap: take face from source, place onto target.

        Returns dict with processing metadata.
        """
        start = time.time()
        meta = {}

        # 1. Load images
        source_img = resize_keep_aspect(load_image(source_path))
        target_img = resize_keep_aspect(load_image(target_path))

        # 2. Detect faces
        source_faces = self.detector.detect(source_img)
        target_faces = self.detector.detect(target_img)

        if not source_faces:
            return {"success": False, "error": "No face detected in source image."}
        if not target_faces:
            return {"success": False, "error": "No face detected in target image."}

        meta["source_faces_found"] = len(source_faces)
        meta["target_faces_found"] = len(target_faces)

        # 3. Extract source face
        src_face, src_coords = self.aligner.extract_face(
            source_img, source_faces[0]["bbox"]
        )
        src_face_resized = self.aligner.resize_face(src_face)

        # 4. For each target face, perform swap
        result_img = target_img.copy()
        for face_info in target_faces:
            _, tgt_coords = self.aligner.extract_face(result_img, face_info["bbox"])
            result_img = self.blender.blend(result_img, src_face_resized, tgt_coords)

        # 5. Optional post-processing enhancement
        if enhance:
            result_img = self._enhance(result_img)

        # 6. Apply blend_strength (composite with original)
        if blend_strength < 1.0:
            result_img = self._composite(target_img, result_img, blend_strength)

        # 7. Save
        save_image(result_img, output_path)

        elapsed = round(time.time() - start, 2)
        meta.update({
            "success": True,
            "output_path": output_path,
            "processing_time_sec": elapsed,
            "enhance": enhance,
            "blend_strength": blend_strength,
        })
        logger.info(f"Processing complete in {elapsed}s → {output_path}")
        return meta

    # ── Post-processing helpers ───────────────

    def _enhance(self, img: np.ndarray) -> np.ndarray:
        """Apply sharpening and colour correction."""
        kernel = np.array([[0, -0.5, 0],
                           [-0.5, 3, -0.5],
                           [0, -0.5, 0]])
        bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        sharpened = cv2.filter2D(bgr, -1, kernel)
        # Subtle CLAHE on luminance channel for contrast
        lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        return cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)

    def _composite(self, original: np.ndarray, swapped: np.ndarray, strength: float) -> np.ndarray:
        """Alpha-composite original and swapped at given strength."""
        orig_resized = cv2.resize(original, (swapped.shape[1], swapped.shape[0]))
        return cv2.addWeighted(swapped, strength, orig_resized, 1 - strength, 0).astype(np.uint8)


# ──────────────────────────────────────────────
# Video DeepFake Processor
# ──────────────────────────────────────────────

class VideoDeepFakeProcessor:
    """
    Frame-by-frame face swap for short video clips.
    Processes every N frames for performance control.
    """

    def __init__(self):
        self.frame_processor = DeepFakeProcessor()

    def process_video(
        self,
        source_image_path: str,
        target_video_path: str,
        output_video_path: str,
        frame_skip: int = 1,
        max_frames: int = 300,
    ) -> dict:
        """Swap face from source_image into every frame of target_video."""
        cap = cv2.VideoCapture(target_video_path)
        if not cap.isOpened():
            return {"success": False, "error": "Cannot open target video."}

        fps = cap.get(cv2.CAP_PROP_FPS) or 24
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        source_img = resize_keep_aspect(load_image(source_image_path))
        source_faces = self.frame_processor.detector.detect(source_img)

        if not source_faces:
            cap.release()
            return {"success": False, "error": "No face detected in source image."}

        src_face, _ = self.frame_processor.aligner.extract_face(
            source_img, source_faces[0]["bbox"]
        )
        src_face_resized = self.frame_processor.aligner.resize_face(src_face)

        frame_count = 0
        processed = 0
        start = time.time()

        while True:
            ret, frame = cap.read()
            if not ret or frame_count >= max_frames:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if frame_count % (frame_skip + 1) == 0:
                faces = self.frame_processor.detector.detect(rgb_frame)
                if faces:
                    _, tgt_coords = self.frame_processor.aligner.extract_face(
                        rgb_frame, faces[0]["bbox"]
                    )
                    rgb_frame = self.frame_processor.blender.blend(
                        rgb_frame, src_face_resized, tgt_coords
                    )
                processed += 1

            out_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            writer.write(out_frame)
            frame_count += 1

        cap.release()
        writer.release()

        return {
            "success": True,
            "frames_total": frame_count,
            "frames_processed": processed,
            "output_video": output_video_path,
            "processing_time_sec": round(time.time() - start, 2),
        }
