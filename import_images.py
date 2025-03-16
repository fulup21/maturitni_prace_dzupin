import os
import json
import base64
import hashlib

from abstracts import Card


def process_images_to_json(input_picture_directory: str, output_json_file: str) -> None:
    """input: directory of images to be processed;
        output: json file with images' metadata (key, path, MD5 checksum, base64 encoding of image)
        :param input_picture_directory:
        :param output_json_file:
        :return: None
    """

    def get_key_from_name(file: str) -> int:
        """files are named x.png, therefore the 0 index is the x portion of string"""
        return int(os.path.splitext(file)[0])

    def encode_to_b64(file: str) -> str:
        with open(file, "rb") as _f:  #"rb" means read in binary mode
            b64_image: str = base64.b64encode(_f.read()).decode("utf-8")
        return b64_image

    def calculate_md5(encoded_pic: str) -> str:
        return hashlib.md5(encoded_pic.encode("utf-8")).hexdigest()

    pictures: list[Card] = []
    files: list[str] = os.listdir(input_picture_directory)
    sorted_files: list[str] = sorted(files, key=get_key_from_name)

    for picture in sorted_files:
        key: int = get_key_from_name(picture)
        path: str = os.path.join(input_picture_directory, picture)
        base64_data: str = encode_to_b64(path)
        checksum: str = calculate_md5(base64_data)
        pictures.append(Card(key=key, path=path, checksum=checksum, encoded_picture=base64_data))

    json_data: str = json.dumps([picture.model_dump() for picture in pictures], ensure_ascii=False, indent=4)
    with open(output_json_file, "w", encoding="utf-8") as f:
        f.write(json_data)

if __name__ == "__main__":
    process_images_to_json("card_images","images.json")