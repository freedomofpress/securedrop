from flask import wrappers
from tempfile import NamedTemporaryFile
from io import BytesIO

class RequestThatSecuresFileUploads(wrappers.Request):

    def _secure_file_stream(self, total_content_length, content_type, filename=None,
                        content_length=None):
        if total_content_length > 1024 * 512:
            tf = NamedTemporaryFile(delete=False)
            # Save the name of the temporary file on the request object so we can `shred` it later
            self._temporary_file_name = tf.name
            return tf
        return BytesIO()

    def make_form_data_parser(self):
        return self.form_data_parser_class(self._secure_file_stream,
                                           self.charset,
                                           self.encoding_errors,
                                           self.max_form_memory_size,
                                           self.max_content_length,
                                           self.parameter_storage_class)

