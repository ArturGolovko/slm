import sys
import os
import time
import numpy as np
import cv2

# -------------------------
# Setup
# -------------------------
# Add HEDS SDK to path (adjust this to your actual install)
sys.path.append(r"C:\Path\To\HEDS")

# Try importing PySpin
try:
    import PySpin
except ImportError:
    print("PySpin (Spinnaker SDK) not found. Please install it first.")
    sys.exit(1)

# Import HEDS SDK
import HEDS
from hedslib.heds_types import *

# -------------------------
# Configuration
# -------------------------
OUTPUT_DIR = r"C:\Users\chmo\Desktop\qsa\captures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SLM_WIDTH = 1024
SLM_HEIGHT = 768
NUM_GRAY_LEVELS = 256  # 0–255 inclusive

# -------------------------
# Initialize HEDS SLM
# -------------------------
HEDS.SDK.PrintVersion()
err = HEDS.SDK.Init(4, 1)
assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)

slm = HEDS.SLM.Init()
assert slm.errorCode() == HEDSERR_NoError, HEDS.SDK.ErrorString(slm.errorCode())

# -------------------------
# Initialize PySpin Camera
# -------------------------
system = PySpin.System.GetInstance()
cams = system.GetCameras()
if cams.GetSize() == 0:
    print("No PySpin-compatible camera detected.")
    system.ReleaseInstance()
    sys.exit(1)

camera = cams.GetByIndex(0)
camera.Init()

nodemap = camera.GetNodeMap()

# Continuous acquisition mode
acq = PySpin.CEnumerationPtr(nodemap.GetNode("AcquisitionMode"))
ac_cont = acq.GetEntryByName("Continuous")
acq.SetIntValue(ac_cont.GetValue())

# Pixel format: Mono8 (grayscale)
pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))
mono8 = pixel_format.GetEntryByName("Mono8")
pixel_format.SetIntValue(mono8.GetValue())

camera.BeginAcquisition()
print("PySpin camera initialized successfully.\n")

# -------------------------
# Main Loop: Display + Capture
# -------------------------
for gray_val in range(NUM_GRAY_LEVELS):
    img_array = np.zeros((SLM_HEIGHT, SLM_WIDTH), dtype=np.uint8)
    img_array[:, :SLM_WIDTH // 2] = 255
    img_array[:, SLM_WIDTH // 2:] = gray_val

    err, dataHandle = slm.loadImageData(img_array)
    assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)
    err = dataHandle.show()
    assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)

    # Save pattern image
    slm_filename = f"SLM_halfgray_{gray_val:03d}.bmp"
    cv2.imwrite(os.path.join(OUTPUT_DIR, slm_filename), img_array)

    # Allow SLM to update
    time.sleep(0.1)

    # Capture from camera
    try:
        img = camera.GetNextImage()
        if not img.IsIncomplete():
            frame = img.GetNDArray()
            capture_filename = f"Capture_gray_{gray_val:03d}.bmp"
            cv2.imwrite(os.path.join(OUTPUT_DIR, capture_filename), frame)
            print(f"[{gray_val:03d}/255] Captured → {capture_filename}")
        img.Release()
    except Exception as e:
        print(f"Capture failed at gray={gray_val}: {e}")

# -------------------------
# Cleanup
# -------------------------
camera.EndAcquisition()
camera.DeInit()
cams.Clear()
system.ReleaseInstance()

slm.close()
HEDS.SDK.Close()

print("\nDone.")
