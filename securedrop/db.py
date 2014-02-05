from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, ForeignKey, distinct, delete, and_, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import StaticPool
import config
import crypto_util

metadata = MetaData()

tags = Table('tags', metadata,
             Column('id', Integer, primary_key=True),
             Column('name', String(255), nullable=False, unique=True))

files_to_tags = Table("files_tags", metadata,
                      Column("id", Integer, primary_key=True),
                      Column("tags_id", Integer, ForeignKey('tags.id', onupdate="CASCADE", ondelete="CASCADE")),
                      Column("files_id", Integer, ForeignKey("files.id", onupdate="CASCADE", ondelete="CASCADE")))

files = Table('files', metadata,
              Column('id', Integer, primary_key=True),
              Column('name', String(255), nullable=False, unique=True))

sources = Table('sources', metadata,
                Column('filesystem_id', String(96), primary_key=True),
                Column('journalist_designation', String(255), nullable=False))


# I had to put this engine creation logic in a function so we can
# re-create the sqlite file in tests. Since we are keeping state
# maybe we should convert this db module into a proper class - jacksingleton
def initialize():
    global _engine
    if config.DATABASE_ENGINE == "sqlite":
        _engine = create_engine(
            config.DATABASE_ENGINE + ":///" +
            config.DATABASE_FILE,
            poolclass=StaticPool
        )
    else:
        _engine = create_engine(
            config.DATABASE_ENGINE + '://' +
            config.DATABASE_USERNAME + ':' +
            config.DATABASE_PASSWORD + '@' +
            config.DATABASE_HOST + '/' +
            config.DATABASE_NAME, echo=False
        )


initialize()


def create_tables():
    metadata.drop_all(_engine)
    metadata.create_all(_engine)


def sqlalchemy_handle():
    Session = sessionmaker(bind=_engine)
    return Session()


def display_id(filesystem_id, session):
    journalist_designation = session.query(sources.c.journalist_designation).filter(
        sources.c.filesystem_id == filesystem_id).all()
    session.close()
    if len(journalist_designation) > 0:
        return journalist_designation[0][0]
    else:
        return crypto_util.displayid(filesystem_id)



def regenerate_display_id(filesystem_id):
    session = sqlalchemy_handle()
    try:
        source_obj = session.query(sources.c.journalist_designation).filter(
            sources.c.filesystem_id == filesystem_id).one()
        add = sources.update().values(
            journalist_designation=crypto_util.displayid(
                display_id(filesystem_id, session))
        ).where(sources.c.filesystem_id == filesystem_id)
    except NoResultFound:
        add = sources.insert().values(
            filesystem_id=filesystem_id,
            journalist_designation=crypto_util.displayid(
                display_id(filesystem_id, session))
        )
    session.execute(add)
    session.commit()
    session.close()


def delete_source(source_id):
    session = sqlalchemy_handle()
    try:
        delete = sources.delete().where(
            sources.c.filesystem_id == source_id)
    except SQLAlchemyError as e:
        # TODO: proper logging
        print "Exception occurred attempting to delete source (source_id: %s): %s" % (source_id, e)
    session.execute(delete)
    session.commit()
    session.close()


def insert_files(file_names, session):
    file_results = []
    for file_name in file_names:
        query = session.query(files.c.id).filter(files.c.name == file_name)
        results = session.execute(query).fetchone()
        if results is not None:
            file_results.append(results[0])
        else:
            result_proxy = session.execute(files.insert().values(name=file_name))
            file_results.append(result_proxy.inserted_primary_key[0])
    return file_results


def add_tag_to_file(file_names, *tags_to_add):
    session = sqlalchemy_handle()
    tag_results = []
    for tag in tags_to_add:
        query = session.query(tags.c.id).filter(tags.c.name == tag)
        result = session.execute(query).fetchone()
        if result is not None:
            tag_results.append(result[0])
        else:
            result_proxy = session.execute(tags.insert().values(name=tag))
            tag_results.append(result_proxy.inserted_primary_key[0])

    file_results = _insert_files(session, file_names)

    for tag_id in tag_results:
        for file_id in file_results:
            query = session.query(files_to_tags)
            query = query.filter(files_to_tags.c.files_id == file_id).filter(files_to_tags.c.tags_id == tag_id)
            results = session.execute(query).fetchall()
            if len(results) == 0:
                session.execute(files_to_tags.insert().values(tags_id=tag_id,files_id=file_id))

    session.commit()
    session.close()


def get_tags_for_file(file_names):
    session = sqlalchemy_handle()
    results = {}
    for file_name in file_names:
        query = session.query(tags.c.name).filter(files.c.id == files_to_tags.c.files_id)
        query = query.filter(tags.c.id == files_to_tags.c.tags_id)
        query = query.filter(files.c.name == file_name)
        query = query.filter(tags.c.name != '')
        tag_names = [row[0] for row in session.execute(query).fetchall()]
        results[file_name] = tag_names
    session.close()
    return results


def delete_tags_from_file(file_names, tags_to_remove):
    session = sqlalchemy_handle()
    query = session.query(files_to_tags.c.id).join(tags, files_to_tags.c.tags_id == tags.c.id)
    query = query.join(files, files_to_tags.c.files_id == files.c.id)
    query = query.filter(tags.c.name.in_(tags_to_remove))
    query = query.filter(files.c.name.in_(file_names))
    results = session.execute(query).fetchall()
    if len(results) > 0:
        results = [row[0] for row in results]
        delete_query = delete(files_to_tags, files_to_tags.c.id.in_(results))
        session.execute(delete_query)
    session.commit()
    session.close()


def delete_tag_from_file(file_name, tag_name):
    session = sqlalchemy_handle()

    query = session.query(files_to_tags.c.id).join(tags, files_to_tags.c.tags_id == tags.c.id)
    query = query.join(files, files_to_tags.c.files_id == files.c.id)
    query = query.filter(tags.c.name == tag_name)
    query = query.filter(files.c.name == file_name)
    result = session.execute(query).fetchall()
    if len(result) > 0:
        delete_query = delete(files_to_tags, files_to_tags.c.id == result[0][0])
        session.execute(delete_query)

    session.commit()
    session.close()


def get_all_tags():
    session = sqlalchemy_handle()
    query = session.query(tags.c.name).order_by(tags.c.name)
    results = session.execute(query)
    results = [row[0] for row in results.fetchall()]
    session.close()
    return results


def delete_source(source_id):
    session = sqlalchemy_handle()
    try:
        delete = sources.delete().where(
            sources.c.filesystem_id == source_id)
    except SQLAlchemyError as e:
        # TODO: proper logging
        print "Exception occurred attempting to delete source (source_id: %s): %s" % (source_id, e)
    session.execute(delete)
    session.commit()
    session.close()
