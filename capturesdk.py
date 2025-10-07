import os
import sys
import time
import numpy as np
import cv2

# Holoeye SDK is now required — script will fail if not installed
import holoeye_slim as slm

# Camera is still optional
try:
    import PySpin
    USE_CAMERA = True
except ImportError:
    print("PySpin not found; running in display-only mode.")
    USE_CAMERA = False

OUTPUT_DIR = r"C:\Users\kiyotaka\Desktop\qsa\captures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SLM_WIDTH = 1024
SLM_HEIGHT = 768
NUM_IMAGES = 1000

# Initialize camera if needed
camera = None
system = cams = None
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
        print("Camera initialized")
    else:
        print("No camera found")
        USE_CAMERA = False

# Initialize SLM — mandatory
device = slm.SLM()  # Connect to first available SLM
print("SLM initialized.")

for i in range(NUM_IMAGES):
    gray_val = int((i / (NUM_IMAGES - 1)) * 255)

    # Generate half-white, half-gray pattern
    img_array = np.zeros((SLM_HEIGHT, SLM_WIDTH), dtype=np.uint8)
    img_array[:, :SLM_WIDTH // 2] = 255
    img_array[:, SLM_WIDTH // 2:] = gray_val

    # Send pattern to SLM directly
    device.show(img_array)

    # Optional: small delay to let SLM update
    time.sleep(0.05)

    # Camera capture
    bmp_arr = None
    if camera:
        for _ in range(5):
            img = camera.GetNextImage()
            img.Release()
            time.sleep(0.01)

        img = camera.GetNextImage()
        if not img.IsIncomplete():
            conv = img.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
            bmp_arr = conv.GetNDArray()
        img.Release()

    # Save the pattern and captured image
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename_pattern = f"{timestamp}_halfgray_{i:04d}.bmp"
    path_pattern = os.path.join(OUTPUT_DIR, filename_pattern)
    cv2.imwrite(path_pattern, img_array)

    if bmp_arr is not None:
        filename_capture = f"{timestamp}_capture_{i:04d}.bmp"
        path_capture = os.path.join(OUTPUT_DIR, filename_capture)
        cv2.imwrite(path_capture, bmp_arr)
        print(f"Saved {i+1}/{NUM_IMAGES} gray={gray_val}, captured image saved.")
    else:
        print(f"Pattern {i+1}/{NUM_IMAGES} displayed on SLM.")

# Cleanup
device.close()

if camera:
    try:
        camera.EndAcquisition()
        camera.DeInit()
        del camera
    except:
        pass
if cams:
    try:
        cams.Clear()
        del cams
    except:
        pass
if system:
    try:
        system.ReleaseInstance()
    except:
        pass

sys.exit()
