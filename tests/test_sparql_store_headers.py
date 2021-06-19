from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLStore, SPARQLUpdateStore

from rdflib_orm.db import set_store_header_read, set_store_header_update


def test_set_store_header_read():
    """SPARQL headers are set correctly for a SPARQLStore."""
    store = SPARQLStore()
    g = Graph(store=store)
    set_store_header_read(g.store)
    assert g.store.kwargs['headers'].get('content-type') is None


def test_set_store_head_update():
    """SPARQL headers are set correctly for a SPARQLUpdateStore."""
    store = SPARQLUpdateStore()
    g = Graph(store=store)
    set_store_header_update(g.store)
    assert g.store.kwargs['headers'].get('content-type') == 'application/sparql-update'
