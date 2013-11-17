from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from config import DATABASE_ENGINE, DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_NAME
import crypto_util

metadata = MetaData()

sources = Table('sources', metadata,
                Column('filesystem_id', String(96), primary_key=True),
                Column('journalist_designation', String(255), nullable=False)
                )

engine = create_engine(
    DATABASE_ENGINE + '://' +
    DATABASE_USERNAME + ':' +
    DATABASE_PASSWORD + '@' +
    DATABASE_HOST + '/' +
    DATABASE_NAME, echo=False
)


def create_tables():
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
