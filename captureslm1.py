import os
import sys
import time
import numpy as np
import cv2
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK

sys.path.append(r"C:\Path\To\HEDS")
import HEDS
from hedslib.heds_types import *

OUTPUT_DIR = r"C:\Users\chmo\Desktop\qsa\captures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SLM_WIDTH = 1024
SLM_HEIGHT = 768
NUM_IMAGES = 1000

HEDS.SDK.PrintVersion()
err = HEDS.SDK.Init(4, 1)
assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)
slm = HEDS.SLM.Init()
assert slm.errorCode() == HEDSERR_NoError, HEDS.SDK.ErrorString(slm.errorCode())

sdk = TLCameraSDK()
camera_list = sdk.discover_available_cameras()
if not camera_list:
    print("No Thorlabs camera detected.")
    camera = None
else:
    camera = sdk.open_camera(camera_list[0])
    camera.exposure_time_us = 20000
    camera.frames_per_trigger_zero_for_unlimited = 0
    camera.image_poll_timeout_ms = 5000
    camera.arm(2)
    camera.issue_software_trigger()

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

    time.sleep(0.05)

    if camera:
        frame = camera.get_pending_frame_or_null()
        if frame is not None:
            frame_data = frame.image_buffer.copy()
            capture_filename = f"{timestamp}_capture_{i:04d}.bmp"
            capture_path = os.path.join(OUTPUT_DIR, capture_filename)
            cv2.imwrite(capture_path, frame_data)
            print(f"[{i+1}/{NUM_IMAGES}] Gray={gray_val} → Captured {capture_filename}")
        camera.issue_software_trigger()

if camera:
    camera.disarm()
    camera.dispose()
sdk.dispose()

slm.close()
HEDS.SDK.Close()
print("Done.")
