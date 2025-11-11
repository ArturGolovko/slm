import sys
import time
import numpy as np

sys.path.append(r"C:\Path\To\HEDS")
import HEDS
from hedslib.heds_types import *

HEDS.SDK.PrintVersion()
err = HEDS.SDK.Init(4, 1)
assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)

slm = HEDS.SLM.Init()
assert slm.errorCode() == HEDSERR_NoError, HEDS.SDK.ErrorString(slm.errorCode())

def create_checkerboard(squares_x, squares_y, slm_width=1024, slm_height=768):
    square_w = slm_width // squares_x
    square_h = slm_height // squares_y

    img = np.zeros((slm_height, slm_width), dtype=np.uint8)

    for y in range(squares_y):
        for x in range(squares_x):
            if (x + y) % 2 == 0:
                img[y*square_h:(y+1)*square_h, x*square_w:(x+1)*square_w] = 255

    err, dataHandle = slm.loadImageData(img)
    assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)
    err = dataHandle.show()
    assert err == HEDSERR_NoError, HEDS.SDK.ErrorString(err)
    time.sleep(0.5)

    return img

if __name__ == "__main__":
    create_checkerboard(8, 8)

slm.close()
HEDS.SDK.Close()
print("Done.")
