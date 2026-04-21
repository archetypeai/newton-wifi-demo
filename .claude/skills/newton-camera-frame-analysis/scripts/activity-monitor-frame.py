#!/usr/bin/env python3
"""
Simplified webcam capture and analysis using ArchetypeAI Newton model
"""
import cv2
import base64
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from archetypeai.api_client import ArchetypeAI
from archetypeai.utils import base64_encode

# Model configuration - defined once and reused
MODEL_CONFIG = {
    "model_version": "Newton::c2_4_7b_251215a172f6d7",
    "template_name": "image_qa_template_task",
    "instruction": "Answer the following question about the image:",
    "max_new_tokens": 512
}

def capture_webcam_image(camera_index=0, output_dir="captures"):
    """Capture image from webcam and save it"""
    Path(output_dir).mkdir(exist_ok=True)

    cap = cv2.VideoCapture(camera_index)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise Exception("Failed to capture image from webcam")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/webcam_{timestamp}.jpg"
    cv2.imwrite(filename, frame)
    print(f"📸 Captured: {filename}")
    return filename

def analyze_webcam_image(api_key, image_path, question="Describe what you see"):
    """Analyze captured image using Newton model"""

    client = ArchetypeAI(api_key)

    # Lens configuration with model parameters
    lens_config = {
        "lens_name": f"webcam-analysis-{int(time.time())}",
        "lens_config": {
            "model_pipeline": [{
                "processor_name": "lens_camera_processor",
                "processor_config": {}
            }],
            "model_parameters": {
                **MODEL_CONFIG,
                "focus": question,
                "camera_buffer_size": 1,
                "min_replicas": 1,
                "max_replicas": 1
            }
        }
    }

    lens_id = None
    session_id = None

    try:
        # 1. Register lens
        print("🔧 Setting up analysis...")
        lens = client.lens.register(lens_config)
        lens_id = lens['lens_id']

        # 2. Create session
        session = client.lens.sessions.create(lens_id)
        session_id = session['session_id']

        # 3. Wait for session ready
        print("⏳ Initializing...")
        for _ in range(30):
            try:
                status = client.lens.sessions.process_event(
                    session_id, {"type": "session.status"}
                )
                if status.get('session_status') in ['3', 'LensSessionStatus.SESSION_STATUS_RUNNING']:
                    break
            except:
                pass
            time.sleep(0.5)

        # 4. Initialize processor
        client.lens.sessions.process_event(session_id, {
            "type": "session.modify",
            "event_data": {"camera_buffer_size": 1}
        })

        # 5. Prepare image
        base64_img = base64_encode(image_path).replace("data:image/jpeg;base64,", "")

        # 6. Query with image
        print("🔍 Analyzing image...")
        event = {
            "type": "model.query",
            "event_data": {
                **MODEL_CONFIG,
                "focus": question,
                "data": [{
                    "type": "base64_img",
                    "base64_img": base64_img
                }]
            }
        }

        response = client.lens.sessions.process_event(session_id, event)

        # 7. Extract result
        if response.get('type') == 'model.query.response':
            result = response.get('event_data', {}).get('response', '')
            if isinstance(result, list):
                result = result[0] if result else "No response"
            print(f"\n💭 Answer: {result}")
            return result
        else:
            print(f"Unexpected response: {json.dumps(response, indent=2)}")
            return None

    finally:
        # Cleanup
        if session_id:
            try:
                client.lens.sessions.destroy(session_id)
            except:
                pass
        if lens_id:
            try:
                client.lens.delete(lens_id)
            except:
                pass

def main():
    # Get API key
    api_key = os.environ.get("ARCHETYPE_API_KEY") or os.environ.get("ATAI_API_KEY")

    if not api_key:
        print("Error: Please set ARCHETYPE_API_KEY or ATAI_API_KEY environment variable")
        sys.exit(1)

    # Parse arguments
    question = sys.argv[1] if len(sys.argv) > 1 else "Describe what you see"
    camera_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    print(f"📷 Camera: {camera_index}")
    print(f"❓ Question: {question}")
    print("-" * 40)

    try:
        # Capture and analyze
        image_path = capture_webcam_image(camera_index)
        analyze_webcam_image(api_key, image_path, question)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()