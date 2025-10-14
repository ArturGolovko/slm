import sys
import os
import time
import numpy as np
import cv2

# Add HEDS folder to path (adjust the path)
sys.path.append(r"C:\Path\To\HEDS")

# Try importing PySpin (FLIR/Spinnaker SDK)
try:
    import PySpin
    USE_PYSPIN = True
except ImportError:
    print("PySpin not found; will attempt Thorlabs camera only.")
    USE_PYSPIN = False

# Import HEDS
import HEDS
from hedslib.heds_types import *

# Optional Thorlabs camera SDK
try:
    from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
    USE_TSI = True
except ImportError:
    print("Thorlabs TSI SDK not found.")
    USE_TSI = False

# -------------------------
# Configuration
# -------------------------
OUTPUT_DIR = r"C:\Users\chmo\Desktop\qsa\captures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SLM_WIDTH = 1024
SLM_HEIGHT = 768
NUM_IMAGES = 256  # 0 to 255 grayscale

# -------------------------
# Initialize HEDS SLM
# -------------------------
HEDS.SDK.PrintVersion()
err = HEDS.SDK.Init(4, 1)
assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)

slm = HEDS.SLM.Init()
assert slm.errorCode() == HEDSERR_NoError, HEDS.SDK.ErrorString(slm.errorCode())

# -------------------------
# Initialize Cameras
# -------------------------
pyspin_camera = None
tsi_camera = None
pyspin_system = None
pyspin_cams = None
tsi_sdk = None

if USE_PYSPIN:
    pyspin_system = PySpin.System.GetInstance()
    pyspin_cams = pyspin_system.GetCameras()
    if pyspin_cams.GetSize() > 0:
        pyspin_camera = pyspin_cams.GetByIndex(0)
        pyspin_camera.Init()
        nodemap = pyspin_camera.GetNodeMap()

        # Continuous acquisition
        acq = PySpin.CEnumerationPtr(nodemap.GetNode("AcquisitionMode"))
        ac_cont = acq.GetEntryByName("Continuous")
        acq.SetIntValue(ac_cont.GetValue())

        # Mono8 pixel format
        pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))
        mono8 = pixel_format.GetEntryByName("Mono8")
        pixel_format.SetIntValue(mono8.GetValue())

        pyspin_camera.BeginAcquisition()
        print("PySpin camera initialized.")
    else:
        print("No PySpin camera found.")
        USE_PYSPIN = False

if USE_TSI:
    tsi_sdk = TLCameraSDK()
    cameras = tsi_sdk.discover_available_cameras()
    if cameras:
        tsi_camera = tsi_sdk.open_camera(cameras[0])
        tsi_camera.exposure_time_us = 20000
        tsi_camera.frames_per_trigger_zero_for_unlimited = 0
        tsi_camera.image_poll_timeout_ms = 5000
        tsi_camera.arm(2)
        print("Thorlabs TSI camera initialized.")
    else:
        print("No Thorlabs camera detected.")
        USE_TSI = False

# -------------------------
# Display patterns + Capture
# -------------------------
for gray_val in range(256):  # 0–255
    # Generate half-white, half-gray pattern
    img_array = np.zeros((SLM_HEIGHT, SLM_WIDTH), dtype=np.uint8)
    img_array[:, :SLM_WIDTH // 2] = 255
    img_array[:, SLM_WIDTH // 2:] = gray_val

    # Load and show pattern on SLM
    err, dataHandle = slm.loadImageData(img_array)
    assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)
    err = dataHandle.show()
    assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)

    # Save SLM pattern locally
    pattern_filename = f"SLM_gray_{gray_val:03d}.bmp"
    cv2.imwrite(os.path.join(OUTPUT_DIR, pattern_filename), img_array)

    # Small delay to ensure SLM update
    time.sleep(0.05)

    # Capture PySpin camera image
    if USE_PYSPIN and pyspin_camera:
        try:
            img = pyspin_camera.GetNextImage()
            if not img.IsIncomplete():
                frame = img.GetNDArray()
                capture_filename = f"PySpin_gray_{gray_val:03d}.bmp"
                cv2.imwrite(os.path.join(OUTPUT_DIR, capture_filename), frame)
                print(f"Gray={gray_val} → PySpin captured {capture_filename}")
            img.Release()
        except Exception as e:
            print(f"PySpin capture failed at gray={gray_val}: {e}")

    # Capture Thorlabs TSI camera image
    if USE_TSI and tsi_camera:
        frame = tsi_camera.get_pending_frame_or_null()
        if frame is not None:
            frame_data = frame.image_buffer.copy()
            capture_filename = f"TSI_gray_{gray_val:03d}.bmp"
            cv2.imwrite(os.path.join(OUTPUT_DIR, capture_filename), frame_data)
            print(f"Gray={gray_val} → TSI captured {capture_filename}")
        tsi_camera.issue_software_trigger()

# -------------------------
# Cleanup
# -------------------------
if USE_PYSPIN and pyspin_camera:
    pyspin_camera.EndAcquisition()
    pyspin_camera.DeInit()
    del pyspin_camera

if USE_PYSPIN and pyspin_cams:
    pyspin_cams.Clear()
    del pyspin_cams

if USE_PYSPIN and pyspin_system:
    pyspin_system.ReleaseInstance()

if USE_TSI and tsi_camera:
    tsi_camera.disarm()
    tsi_camera.dispose()

if USE_TSI and tsi_sdk:
    tsi_sdk.dispose()

slm.close()
HEDS.SDK.Close()

print("Done.")
