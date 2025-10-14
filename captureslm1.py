import sys
import os
import time
import numpy as np
import cv2

# Add HEDS folder to path (adjust the path)
sys.path.append(r"C:\Path\To\HEDS")

try:
    import PySpin
    USE_CAMERA = True
except ImportError:
    print("PySpin not found; running without camera.")
    USE_CAMERA = False

import HEDS
from hedslib.heds_types import *

# -------------------------
# Configuration
# -------------------------
OUTPUT_DIR = r"C:\Users\chmo\Desktop\qsa\captures"  # change as needed
os.makedirs(OUTPUT_DIR, exist_ok=True)

SLM_WIDTH = 1024
SLM_HEIGHT = 768   # set according to your SLM
NUM_IMAGES = 10    # number of patterns to generate

# -------------------------
# Initialize SDK and SLM
# -------------------------
HEDS.SDK.PrintVersion()
err = HEDS.SDK.Init(4, 1)
assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)

slm = HEDS.SLM.Init()
assert slm.errorCode() == HEDSERR_NoError, HEDS.SDK.ErrorString(slm.errorCode())

# -------------------------
# Initialize Camera
# -------------------------
system = cams = camera = None
if USE_CAMERA:
    system = PySpin.System.GetInstance()
    cams = system.GetCameras()
    if cams.GetSize() > 0:
        camera = cams.GetByIndex(0)
        camera.Init()

        nodemap = camera.GetNodeMap()
        # Set acquisition mode to Continuous
        acq = PySpin.CEnumerationPtr(nodemap.GetNode("AcquisitionMode"))
        ac_cont = acq.GetEntryByName("Continuous")
        acq.SetIntValue(ac_cont.GetValue())

        # Optional: set pixel format to Mono8 (grayscale)
        pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))
        mono8 = pixel_format.GetEntryByName("Mono8")
        pixel_format.SetIntValue(mono8.GetValue())

        camera.BeginAcquisition()
        print("Camera initialized.")
    else:
        print("No camera found.")
        USE_CAMERA = False

# -------------------------
# Display patterns + Capture
# -------------------------
for i in range(NUM_IMAGES):
    gray_val = int((i / (NUM_IMAGES - 1)) * 255)

    # Generate half-white, half-gray pattern
    img_array = np.zeros((SLM_HEIGHT, SLM_WIDTH), dtype=np.uint8)
    img_array[:, :SLM_WIDTH // 2] = 255
    img_array[:, SLM_WIDTH // 2:] = gray_val

    # Load the generated pattern into SLM memory
    err, dataHandle = slm.loadImageData(img_array)
    assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)

    # Display the pattern on the SLM
    err = dataHandle.show()
    assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)

    # Save pattern locally
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    pattern_filename = f"{timestamp}_halfgray_{i:04d}.bmp"
    pattern_path = os.path.join(OUTPUT_DIR, pattern_filename)
    cv2.imwrite(pattern_path, img_array)

    # Small delay to ensure SLM update
    time.sleep(0.05)

    # Capture image from camera
    if USE_CAMERA and camera is not None:
        try:
            img = camera.GetNextImage()
            if not img.IsIncomplete():
                # Directly get NumPy array
                frame = img.GetNDArray()

                capture_filename = f"{timestamp}_capture_{i:04d}.bmp"
                capture_path = os.path.join(OUTPUT_DIR, capture_filename)
                cv2.imwrite(capture_path, frame)

                print(f"[{i+1}/{NUM_IMAGES}] Gray={gray_val} → Captured {capture_filename}")
            img.Release()
        except Exception as e:
            print(f"Camera capture failed at index {i}: {e}")

# -------------------------
# Cleanup
# -------------------------
if USE_CAMERA and camera:
    try:
        camera.EndAcquisition()
        camera.DeInit()
    except:
        pass
    del camera

if USE_CAMERA and cams:
    cams.Clear()
    del cams

if USE_CAMERA and system:
    system.ReleaseInstance()

slm.close()
HEDS.SDK.Close()

print("Done.")
