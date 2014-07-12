from flask import wrappers
import io

class ZeroFillStream(io.BytesIO):

    def close(self):
        """Zero fill the underlying buffer before closing.

        Note that you cannot rely on the garbage collector to get rid of this
        in a timely manner. For best results, call .close() explicitly when you
        are done, or use a context manager."""
        #
        # XXX this might not be sufficient. As data is repeatedly .written to
        # BytesIO, it is a periodically re-allocated with an underlying call to
        # PyMem_Realloc. That means that fragments of plaintext will escape our
        # grasp and become impossible to zero-fill.
        # 
        # TODO test with the poc from the audit
        #
        # The only potential fix here is to create our own secure stream data
        # type in C, which is essentially a BytesIO, but zerofills the
        # underlying buffer on realloc and free.
        #
        self.seek(io.SEEK_END)
        data_len = self.tell()
        self.seek(io.SEEK_SET)
        self.write('\0' * data_len)
        super(ZeroFillStream, self).close()

def create_secure_file_stream():
    return BytesIO()

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

