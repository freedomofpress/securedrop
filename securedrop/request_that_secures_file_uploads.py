from flask import wrappers
from io import BytesIO

class RequestThatSecuresFileUploads(wrappers.Request):

    def _secure_file_stream(self, total_content_length, content_type, filename=None,
                        content_length=None):
        return create_secure_file_stream()

    def make_form_data_parser(self):
        return self.form_data_parser_class(self._secure_file_stream,
                                           self.charset,
                                           self.encoding_errors,
                                           self.max_form_memory_size,
                                           self.max_content_length,
                                           self.parameter_storage_class)


def create_secure_file_stream():
    return BytesIO()
