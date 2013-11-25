from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, ForeignKey, distinct, delete, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
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


def get_engine():
    if config.DATABASE_ENGINE == "sqlite":
        engine = create_engine(
            config.DATABASE_ENGINE + ":///" +
            config.DATABASE_FILE
        )
    else:
        engine = create_engine(
            config.DATABASE_ENGINE + '://' +
            config.DATABASE_USERNAME + ':' +
            config.DATABASE_PASSWORD + '@' +
            config.DATABASE_HOST + '/' +
            config.DATABASE_NAME, echo=False
        )
    return engine


engine = get_engine()


def create_tables():
    metadata.drop_all(engine)
    metadata.create_all(engine)


def sqlalchemy_handle():
    Session = sessionmaker(bind=engine)
    return Session()


def display_id(filesystem_id, session):
    journalist_designation = session.query(sources.c.journalist_designation).filter(
        sources.c.filesystem_id == filesystem_id).all()
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


def insert_files(file_names, session):
    file_results = []
    for fileName in file_names:
        query = session.query(files.c.id).filter(files.c.name == fileName)
        results = session.execute(query)
        if results.rowcount > 0:
            file_results.append(results.fetchone()[0])
        else:
            result_proxy = session.execute(files.insert().values(name=fileName))
            file_results.append(result_proxy.inserted_primary_key[0])
    return file_results


def add_tag_to_file(file_names, *tags_to_add):
    session = sqlalchemy_handle()
    tag_results = []
    for tag in tags_to_add:
        query = session.query(tags.c.id).filter(tags.c.name == tag)
        results = session.execute(query)
        if results.rowcount > 0:
            tag_results.append(results.fetchone()[0])
        else:
            result_proxy = session.execute(tags.insert().values(name=tag))
            tag_results.append(result_proxy.inserted_primary_key[0])

    file_results = insert_files(file_names, session)

    for tag_id in tag_results:
        for file_id in file_results:
            query = session.query(files_to_tags)
            query = query.filter(files_to_tags.c.files_id == file_id).filter(files_to_tags.c.tags_id == tag_id)
            results = session.execute(query)
            if results.rowcount == 0:
                session.execute(files_to_tags.insert().values(tags_id=tag_id,files_id=file_id))

    session.commit()
    session.close()


def get_files_ids(file_names):
    session = sqlalchemy_handle()
    file_ids = []
    for file_name in file_names:
        query = session.query(files.c.id)
        query = query.filter(files.c.name == file_name)
        results = session.execute(query)
        if results.rowcount > 0:
            file_ids.append(results.fetchone()[0])
    session.close()
    return file_ids


def get_tags_id_from(file_ids):
    session = sqlalchemy_handle()
    tag_ids = {}
    for file_id in file_ids:
        query = session.query(distinct(files_to_tags.c.tags_id))
        query = query.filter(files_to_tags.c.files_id == file_id)
        results = session.execute(query)
        if results.rowcount > 0:
            all = results.fetchall()
            tag_ids[file_id]= [id[0] for id in all]
        else:
            tag_ids[file_id] = []
    session.close()
    return tag_ids


def get_tags_for_file(file_names):
    session = sqlalchemy_handle()
    file_id = insert_files(file_names, session)
    tags_id = get_tags_id_from(file_id)
    results = {}

    for index, id in enumerate(file_id):
        tag_name_list = []
        for tag in tags_id[id]:
            query = session.query(distinct(tags.c.name))
            query = query.filter(tags.c.id == tag).filter(tags.c.name != '')
            query_result = session.execute(query)
            if query_result.rowcount > 0:
                tag_name_list.append(query_result.fetchone()[0])
        results[file_names[index]] = tag_name_list

    session.close()
    return results


def delete_tags_from_file(file_names, tags_to_remove):
    session = sqlalchemy_handle()
    for file_name in file_names:
        tags_ids = []
        query = session.query(files.c.id).filter(files.c.name == file_name)
        result = session.execute(query)
        if result.rowcount > 0:
            file_id = result.fetchone()[0]
            for tag in tags_to_remove[file_name]:
                query = session.query(tags.c.id)
                query = query.filter(tags.c.name == tag)
                result = session.execute(query)
                if result.rowcount > 0:
                    tags_ids.extend(result.fetchall()[0])
            for tag_id in tags_ids:
                where_clause = and_(files_to_tags.c.tags_id == tag_id, files_to_tags.c.files_id == file_id)
                query = delete(files_to_tags,whereclause=where_clause)
                session.execute(query)

    session.commit()
    session.close()