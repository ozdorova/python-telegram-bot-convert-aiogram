import os
import time

import convertio

from .config import convertio_token as token


def convert(filename: str, name: str, callback: str,):
    client = convertio.Client(token=token)
    conversion_id = client.convert_by_filename(
        fp=f'packages/temp_files/{filename}',
        output_format=callback
    )
    while client.check_conversion(conversion_id).step != 'finish':
        time.sleep(1)

    client.download(
        conversion_id,
        f'packages/temp_files/{name}.{callback}'
    )
    client.delete(conversion_id)


def delete_items_in_folder(folder_path='packages/temp_files'):
    for items in os.listdir(folder_path):
        if os.path.isdir(os.path.join(folder_path, items)):
            delete_items_in_folder(
                os.path.isdir(os.path.join(folder_path, items)))
        else:
            os.remove(os.path.join(folder_path, items))
