import base64


class Utils:

    def string_to_base_64_string(self, string: str) -> str:
        return base64.b64encode(string.encode('ascii')).decode('ascii')
