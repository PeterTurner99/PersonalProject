import os


def upload_to_func(file_path_start):
    def processed_upload_to(obj, filename):
        return os.path.join(
            '%s_%d' % (file_path_start, obj.pk), filename
        )

    return processed_upload_to
