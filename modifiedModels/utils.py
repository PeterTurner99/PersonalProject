import os
def uploadToFunc(filePathStart):
    def processedUploadTo(obj, filename):
        return os.path.join(
            '%s_%d' % (filePathStart , obj.pk), filename
        )
    return processedUploadTo