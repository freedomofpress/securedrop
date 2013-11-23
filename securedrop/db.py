from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
import config
import crypto_util

metadata = MetaData()

tags = Table('tags',metadata,
             Column('id', Integer, primary_key=True),
             Column('name',String(255), nullable=False))

files_to_tags = Table("files_tags", metadata,
                      Column("id", Integer, primary_key=True),
                      Column("tags_id", Integer, ForeignKey("tags.id")),
                      Column("files_id", Integer, ForeignKey("files.id")))

files = Table('files', metadata,
              Column('id', Integer, primary_key=True),
              Column('name', String(255), nullable=False))

sources = Table('sources', metadata,
                Column('filesystem_id', String(96), primary_key=True),
                Column('journalist_designation', String(255), nullable=False))

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

def add_tag(filenames, *tags_to_add):
    session = sqlalchemy_handle()
    [session.execute(tags.insert().values(name=tag)) for tag in tags_to_add]
    [session.execute(files.insert().values(name=fileName)) for fileName in filenames]
    session.commit()
    session.close()