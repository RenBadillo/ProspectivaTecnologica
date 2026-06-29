import requests
from pathlib import Path
import time


BASE_DIR = Path(__file__).resolve().parents[2]
IMAGE_PATH = BASE_DIR / "images" / "latest.jpg"


class visionCamera:

    def capture(self):

        self.request_capture()
        return self.wait_for_image()

    def wait_for_image(self,timeout=10):

        start = time.time()

        while time.time() - start < timeout:

            if IMAGE_PATH.exists() and IMAGE_PATH.stat().st_size > 0:
                return IMAGE_PATH

            time.sleep(0.1)

        raise TimeoutError("No llegó la imagen.")



    def request_capture(self):

        response = requests.post(
            "http://192.168.100.78/capture",
            timeout=10
        )

        response.raise_for_status()

        print(response.status_code)
        print(response.text)

if __name__ == "__main__":
    vision = visionCamera()
    vision.capture()