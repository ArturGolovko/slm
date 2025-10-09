import os
import sys
import time
import numpy as np
import cv2

# Add HEDS folder to path if not in current folder
sys.path.append(r"C:\Path\To\HEDS")  # <- adjust this

import HEDS
from hedslib.heds_types import *

OUTPUT_DIR = r"C:\Users\kiyotaka\Desktop\qsa\captures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SLM_WIDTH = 1024
SLM_HEIGHT = 768
NUM_IMAGES = 1000

# -------------------------
# Initialize SDK and SLM
# -------------------------
HEDS.SDK.PrintVersion()
err = HEDS.SDK.Init(4,1)
assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)

slm = HEDS.SLM.Init()
assert slm.errorCode() == HEDSERR_NoError, HEDS.SDK.ErrorString(slm.errorCode())

# -------------------------
# Display patterns
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
    filename = f"{timestamp}_halfgray_{i:04d}.bmp"
    path = os.path.join(OUTPUT_DIR, filename)
    cv2.imwrite(path, img_array)

    time.sleep(0.05)

# -------------------------
# Cleanup
# -------------------------
slm.close()
HEDS.SDK.Close()
