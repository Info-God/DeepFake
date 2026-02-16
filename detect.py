# detect.py
import cv2
import torch
import torchvision.transforms as T
from torchvision import models
import numpy as np
from tqdm import tqdm
import sys
from hashlib import sha256
from utils import compute_file_sha256

# ---------- CONFIG ----------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_WEIGHTS_PATH = None   # optional path if you fine-tune and save a model
FRAME_SAMPLE_RATE = 8       # sample 1 frame every N frames
IMAGE_SIZE = 224
THRESHOLD = 0.5             # >0.5 => fake (adjust after validation)
# ----------------------------

def load_model(device=DEVICE):
    # EfficientNet_b0 backbone as demo
    model = models.efficientnet_b0(pretrained=True)
    # replace classifier with binary head
    num_ftrs = model.classifier[1].in_features
    model.classifier = torch.nn.Sequential(
        torch.nn.Dropout(p=0.2),
        torch.nn.Linear(num_ftrs, 1)  # single logit for binary
    )
    if MODEL_WEIGHTS_PATH:
        model.load_state_dict(torch.load(MODEL_WEIGHTS_PATH, map_location=device))
    model.to(device).eval()
    return model

preprocess = T.Compose([
    T.ToPILImage(),
    T.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    T.ToTensor(),
    T.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
])

def predict_video(video_path, model, device=DEVICE, sample_rate=FRAME_SAMPLE_RATE):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Cannot open video: " + video_path)

    frame_preds = []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    for i in tqdm(range(total), desc="Frames", unit="frame"):
        ret, frame = cap.read()
        if not ret:
            break
        if i % sample_rate != 0:
            continue
        # optional: detect/align face here using face detector (improves accuracy)
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        x = preprocess(img).unsqueeze(0).to(device)
        with torch.no_grad():
            logits = model(x)           # shape [1,1]
            prob = torch.sigmoid(logits).item()  # probability of "fake"
            frame_preds.append(prob)
    cap.release()

    if len(frame_preds) == 0:
        raise RuntimeError("No frames processed. Lower sample_rate or check video.")

    avg_prob = float(np.mean(frame_preds))
    is_fake = avg_prob > THRESHOLD
    return {
        "avg_fake_probability": avg_prob,
        "is_fake": bool(is_fake),
        "frame_count": len(frame_preds)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detect.py input_video.mp4")
        sys.exit(1)
    video_file = sys.argv[1]
    print("Video SHA256:", compute_file_sha256(video_file))
    model = load_model()
    res = predict_video(video_file, model)
    print("Result:", res)
