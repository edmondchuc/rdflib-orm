import pytest

from rdflib import Graph, URIRef
from rdflib.plugins.stores.sparqlstore import SPARQLStore, SPARQLUpdateStore

from rdflib_orm.db import Database, InvalidDBKeyTypeError
from tests import BASE_URI


def test_database_init_sets_sparql_store_bool_false():
    """SPARQL headers are not set on normal graph."""
    g = Graph()
    db = Database(g, BASE_URI)
    assert db.is_sparql_store is False


def test_database_init_sets_sparql_store_bool_true_1():
    """SPARQL headers are set on SPARQLStore"""
    store = SPARQLStore()
    g = Graph(store=store)
    db = Database(g, BASE_URI)
    assert db.is_sparql_store is True


def test_database_init_sets_sparql_store_bool_true_2():
    """SPARQL headers are set on SPARQLUpdateStore"""
    store = SPARQLUpdateStore()
    g = Graph(store=store)
    db = Database(g, BASE_URI)
    assert db.is_sparql_store is True


def test_database_init_assign_attributes():
    """Ensure attributes are assigned correctly."""
    g = Graph()
    db = Database(g, BASE_URI)
    assert isinstance(db.g, Graph)
    assert str(db.base_uri) == BASE_URI
    assert isinstance(db.base_uri, URIRef)


def test_database_set_db_default_key():
    """Database.set_db() sets the Graph to the Database.databases default key."""
    g = Graph()
    Database.set_db(g, BASE_URI)
    db = Database.databases['default']
    assert isinstance(db, Database)
    assert isinstance(db.g, Graph)
    assert str(db.base_uri) == BASE_URI
    assert isinstance(db.base_uri, URIRef)


def test_database_set_db_key_not_str():
    """Database.set_db() throws InvalidDBKeyTypeError if db_key is None."""
    g = Graph()
    with pytest.raises(InvalidDBKeyTypeError):
        Database.set_db(g, BASE_URI, None)


def test_database_set_db_key_custom():
    """Database.set_db() can set db_key to something."""
    g = Graph()
    custom_key = 'metadata'
    Database.set_db(g, BASE_URI, custom_key)
    db = Database.databases[custom_key]
    assert isinstance(db, Database)
    assert isinstance(db.g, Graph)
    assert str(db.base_uri) == BASE_URI
    assert isinstance(db.base_uri, URIRef)


def test_database_get_db_default():
    """Database.get_db() gets the db with the 'default' key."""
    g = Graph()
    Database.set_db(g, BASE_URI)
    db = Database.get_db()
    assert isinstance(db, Database)
    assert isinstance(db.g, Graph)
    assert str(db.base_uri) == BASE_URI
    assert isinstance(db.base_uri, URIRef)


def test_database_get_db_key_custom():
    """Database.get_db() gets the db with a custom key."""
    g = Graph()
    custom_key = 'metadata'
    Database.set_db(g, BASE_URI, custom_key)
    db = Database.get_db(custom_key)
    assert isinstance(db, Database)
    assert isinstance(db.g, Graph)
    assert str(db.base_uri) == BASE_URI
    assert isinstance(db.base_uri, URIRef)


def test_database_write():
    """Ensure data is written to Graph."""
    g = Graph()
    Database.set_db(g, BASE_URI)
    db = Database.get_db()
    triple = (URIRef('s'), URIRef('p'), URIRef('o'))
    db.write(triple)
    assert triple in g.triples((None, None, None))


def test_database_write_set_store_header_update(mocker):
    """Ensure SPARQL update header is set for write."""
    store = SPARQLUpdateStore()
    g = Graph(store=store)
    db = Database(g, BASE_URI)
    assert db.is_sparql_store is True
    mocker.patch('rdflib.Graph.add')
    db.write((URIRef('s'), URIRef('p'), URIRef('o')))


def test_database_delete():
    """Ensure data is deleted."""
    g = Graph()
    Database.set_db(g, BASE_URI)
    db = Database.get_db()
    triple = (URIRef('s'), URIRef('p'), URIRef('o'))
    db.write(triple)
    assert triple in g.triples((None, None, None))
    db.delete(triple)
    assert triple not in g.triples((None, None, None))


def test_database_delete_set_store_header_update(mocker):
    """Ensure SPARQL update header is set for delete."""
    store = SPARQLUpdateStore()
    g = Graph(store=store)
    db = Database(g, BASE_URI)
    assert db.is_sparql_store is True
    mocker.patch(
        'rdflib.Graph.remove'
    )
    db.delete((URIRef('s'), URIRef('p'), URIRef('o')))


def test_database_read():
    g = Graph()
    Database.set_db(g, BASE_URI)
    db = Database.get_db()
    triple = (URIRef('s'), URIRef('p'), URIRef('o'))
    db.write(triple)
    for result in db.read(triple):
        assert result == triple


def test_database_read_set_store_read_header(mocker):
    store = SPARQLUpdateStore()
    g = Graph(store=store)
    db = Database(g, BASE_URI)
    triple = (URIRef('s'), URIRef('p'), URIRef('o'))
    assert db.is_sparql_store is True
    mocker.patch('rdflib.Graph.add')
    db.write(triple)
    mocker.patch('rdflib.Graph.triples')
    for _ in db.read(triple):
        pass


def test_database_sparql_update_positive(mocker):
    store = SPARQLUpdateStore()
    g = Graph(store=store)
    db = Database(g, BASE_URI)
    mocker.patch('rdflib.plugins.stores.sparqlstore.SPARQLUpdateStore.update')
    db.sparql_update('')


def test_database_sparql_positive(mocker):
    store = SPARQLUpdateStore()
    g = Graph(store=store)
    db = Database(g, BASE_URI)
    mocker.patch('rdflib.plugins.stores.sparqlstore.SPARQLUpdateStore.query')
    db.sparql('')
