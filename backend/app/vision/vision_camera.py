import requests
class visionCamera:

    def request_capture(self):

        response = requests.post(
            "http://192.168.100.200/capture",
            timeout=10
        )

        response.raise_for_status()

        print(response.status_code)
        print(response.text)


camera = visionCamera()
camera.request_capture()