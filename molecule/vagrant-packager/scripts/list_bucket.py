#!/usr/bin/env python
#
#
#
#
# Generate index.html of vagrant box files in our s3 bucket
# and upload said file.

import boto3
import os


class S3_Bucket_IndexCreator(object):
    """ Class to initialize s3 bucket connection, grab contents, publish index """

    def __init__(self, bucket, path):
        self.s3 = boto3.resource('s3')
        self.vagrant_bucket = self.s3.Bucket(name=bucket)
        self.bucket = bucket
        self.path = path

    def bucket_get_list(self):
        """ Get bucket file listings and return python list """

        return [obj.key.split('/')[-1] for obj in
                self.vagrant_bucket.objects.filter(Prefix=self.path) if
                "index.html" not in obj.key]

    def generate_html_index(self):
        """Build a simple HTML index string from bucket listings"""

        str_files = ["""<a href="{file}">{file}</a>""".format(file=f) for f in
                     self.bucket_get_list()]

        index_string = """
            <html><head><title>Index of /{path}/</title></head><body bgcolor="white">
            <h1>Index of /{path}/</h1><hr><pre>{files}</pre><hr></body></html>""".format(
                path=self.path,
                files="<br>".join(str_files)
            )

        return index_string

    def upload_string_as_file(self,
                              contents,
                              filename="index.html",
                              content_type="text/html"):

        """ Take contents of a file as input and dump that to a file """
        object = self.s3.Object(self.bucket, '{}/{}'.format(self.path, filename))
        object.put(Body=contents,
                   ContentType=content_type)


if __name__ == "__main__":
    BUCKET = os.environ.get('BUCKET', 'dev-bin.ops.securedrop.org')
    BUCKET_PATH = os.environ.get('BUCKET_PATH', 'vagrant/')

    bucket_index_creation = S3_Bucket_IndexCreator(BUCKET, BUCKET_PATH)
    index = bucket_index_creation.generate_html_index()
    bucket_index_creation.upload_string_as_file(index)
