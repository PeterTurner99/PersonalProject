from django.db import models
from .utils import uploadToFunc
class modifiedImageField(models.ImageField):
    def __init__(
        self,
        verbose_name=None,
        uploadToFilePathStart = "",
        name=None,
        **kwargs,
    ):
        kwargs['upload_to'] = uploadToFunc(uploadToFilePathStart)
        super().__init__(verbose_name, name, **kwargs)