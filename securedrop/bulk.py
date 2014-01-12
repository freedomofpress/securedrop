from flask import render_template, send_file, url_for, redirect
import crypto_util
import store
import db


class Bulk:
    def __init__(self, request, sid, docs_selected):
        self.request = request
        self.sid = sid
        self.docs_selected = docs_selected

    def delete_selected(self):
        confirm_delete = bool(self.request.form.get('confirm_delete', False))
        if confirm_delete:
            for doc in self.docs_selected:
                fn = store.path(self.sid, doc['name'])
                store.secure_unlink(fn)
        return render_template(
            'delete.html', sid=self.sid, codename=db.display_id(self.sid, db.sqlalchemy_handle()),
            docs_selected=self.docs_selected, confirm_delete=confirm_delete)

    def download_selected(self):
        filenames = [store.path(self.sid, doc['name']) for doc in self.docs_selected]
        zip = store.get_bulk_archive(filenames)
        return send_file(zip.name, mimetype="application/zip",
                         attachment_filename=db.display_id(sid, db.sqlalchemy_handle()) + ".zip",
                         as_attachment=True)

    def tag_selected_with(self):
        filenames = [doc['name'] for doc in self.docs_selected]
        tag = self.request.form['tag']
        if tag == '__new__':
            return render_template(
                'new_tag.html', sid=self.sid, codename=db.display_id(self.sid, db.sqlalchemy_handle()),
                docs_selected=self.docs_selected)
        else:
            db.add_tag_to_file(filenames, tag)
            return redirect(url_for('col',sid=self.sid))

    def remove_tags(self):
        filenames = [doc['name'] for doc in self.docs_selected]
        tags_for_files = db.get_tags_for_file(filenames)
        tags_for_files = [tag for tags in tags_for_files.values() for tag in tags]
        db.delete_tags_from_file(filenames, tags_for_files)
        return redirect(url_for('col', sid=self.sid))
