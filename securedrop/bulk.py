from flask import render_template, send_file, url_for, redirect
import crypto_util
import store
import db


class Bulk:
    def __init__(self, request, sid, docs_selected):
        self.request = request
        self.sid = sid
        self.docs_selected = docs_selected

    def bulk_delete(self):
        confirm_delete = bool(self.request.form.get('confirm_delete', False))
        if confirm_delete:
            for doc in self.docs_selected:
                fn = store.path(self.sid, doc['name'])
                crypto_util.secureunlink(fn)
        return render_template(
            'delete.html', sid=self.sid, codename=db.display_id(self.sid, db.sqlalchemy_handle()),
            docs_selected=self.docs_selected, confirm_delete=confirm_delete)

    def bulk_download(self):
        filenames = [store.path(self.sid, doc['name']) for doc in self.docs_selected]
        zip = store.get_bulk_archive(filenames)
        return send_file(zip, mimetype="application/zip",
                         attachment_filename=crypto_util.displayid(self.sid) + ".zip",
                         as_attachment=True)

    def bulk_tag(self):
        filenames = [doc['name'] for doc in self.docs_selected]
        tag = self.request.form['tag']
        if tag == '__new__':
            return render_template(
                'new_tag.html', sid=self.sid, codename=db.display_id(self.sid, db.sqlalchemy_handle()),
                docs_selected=self.docs_selected)
        else:
            db.add_tag_to_file(filenames, tag)
            return redirect(url_for('col',sid=self.sid))

    def bulk_tag_remove(self):
        filenames = [doc['name'] for doc in self.docs_selected]
        tags_for_files = db.get_tags_for_file(filenames)
        tags_for_files = [tag for tags in tags_for_files.values() for tag in tags]
        db.delete_tags_from_file(filenames, tags_for_files)
        return redirect(url_for('col', sid=self.sid))
