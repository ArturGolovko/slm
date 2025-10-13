import os
import sys
import time
import numpy as np
import cv2

try:
    import PySpin
    USE_CAMERA = True
except ImportError:
    print("PySpin not found; running without camera.")
    USE_CAMERA = False


sys.path.append(r"C:\Path\To\HEDS")

import HEDS
from hedslib.heds_types import *

OUTPUT_DIR = r"C:\Users\chmo\Desktop\qsa\captures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SLM_WIDTH = 1024
SLM_HEIGHT = 768
NUM_IMAGES = 1000

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
        acq = PySpin.CEnumerationPtr(nodemap.GetNode("AcquisitionMode"))
        ac_cont = acq.GetEntryByName("Continuous")
        acq.SetIntValue(ac_cont.GetValue())
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

    img_array = np.zeros((SLM_HEIGHT, SLM_WIDTH), dtype=np.uint8)
    img_array[:, :SLM_WIDTH // 2] = 255
    img_array[:, SLM_WIDTH // 2:] = gray_val

    err, dataHandle = slm.loadImageData(img_array)
    assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)

    err = dataHandle.show()
    assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    pattern_filename = f"{timestamp}_halfgray_{i:04d}.bmp"
    pattern_path = os.path.join(OUTPUT_DIR, pattern_filename)
    cv2.imwrite(pattern_path, img_array)

    # Small delay to ensure SLM update
    time.sleep(0.05)

    if USE_CAMERA and camera is not None:
        try:
            img = camera.GetNextImage()
            if not img.IsIncomplete():
                converted = img.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
                frame = converted.GetNDArray()

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
