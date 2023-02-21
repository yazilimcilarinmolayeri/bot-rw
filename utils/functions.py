import mimetypes


def is_image(url: str):
    mimetype, encoding = mimetypes.guess_type(url)
    return mimetype and mimetype.startswith("image")


def convert_matrix(data: list, column: int = 10):
    return [data[i : i + column] for i in range(0, len(data), column)]
