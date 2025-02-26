from django.db import models
from .utils import upload_to_func


class ModifiedImageField(models.ImageField):
    def __init__(
        self,
        verbose_name=None,
            upload_to_file_path_start="",
        name=None,
        **kwargs,
    ):
        kwargs['upload_to'] = upload_to_func(upload_to_file_path_start)
        super().__init__(verbose_name, name, **kwargs)