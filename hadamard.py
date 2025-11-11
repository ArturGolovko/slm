import sys
import os
import time
import numpy as np
import cv2

# -------------------------
# Setup
# -------------------------
sys.path.append(r"C:\Path\To\HEDS")

try:
    import PySpin
except ImportError:
    print("PySpin not found.")
    sys.exit(1)

import HEDS
from hedslib.heds_types import *

# -------------------------
# Configuration
# -------------------------
OUTPUT_DIR = r"C:\Users\chmo\Desktop\qsa\captures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SLM_WIDTH = 1024
SLM_HEIGHT = 768

# -------------------------
# Input: Hadamard size
# -------------------------
n = int(input("Enter Hadamard matrix size"))
if not (n & (n - 1) == 0 and n != 0):
    print("Error: Hadamard matrix size must be a power of 2.")
    sys.exit(1)

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

acq = PySpin.CEnumerationPtr(nodemap.GetNode("AcquisitionMode"))
ac_cont = acq.GetEntryByName("Continuous")
acq.SetIntValue(ac_cont.GetValue())

pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))
mono8 = pixel_format.GetEntryByName("Mono8")
pixel_format.SetIntValue(mono8.GetValue())

camera.BeginAcquisition()
print("PySpin camera initialized successfully.\n")

# -------------------------
# generate hadamard matrix
# -------------------------
H = np.array([[1]])
while H.shape[0] < n:
    H = np.block([
        [H,  H],
        [H, -H]
    ])
H_gray = ((H + 1) / 2 * 255).astype(np.uint8)

# -------------------------
# mail loop display capture
# -------------------------
print(f"Displaying {n}x{n} Hadamard patterns...\n")

for i in range(n):
    for j in range(n):
        base_pattern = np.full((n, n), 0, dtype=np.uint8)
        base_pattern[i, j] = H_gray[i, j]

        pattern_resized = cv2.resize(base_pattern, (SLM_WIDTH, SLM_HEIGHT), interpolation=cv2.INTER_NEAREST)

        err, dataHandle = slm.loadImageData(pattern_resized)
        assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)
        err = dataHandle.show()
        assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)

        slm_filename = f"Hadamard_{n}x{n}_i{i:02d}_j{j:02d}.bmp"
        cv2.imwrite(os.path.join(OUTPUT_DIR, slm_filename), pattern_resized)

        time.sleep(0.1)

        try:
            img = camera.GetNextImage()
            if not img.IsIncomplete():
                frame = img.GetNDArray()
                capture_filename = f"Capture_{n}x{n}_i{i:02d}_j{j:02d}.bmp"
                cv2.imwrite(os.path.join(OUTPUT_DIR, capture_filename), frame)
                print(f"[{i:02d},{j:02d}] Captured → {capture_filename}")
            img.Release()
        except Exception as e:
            print(f"Capture failed at pattern ({i},{j}): {e}")

# -------------------------
# cleanup
# -------------------------
camera.EndAcquisition()
camera.DeInit()
cams.Clear()
system.ReleaseInstance()

slm.close()
HEDS.SDK.Close()

print("\nDone.")
