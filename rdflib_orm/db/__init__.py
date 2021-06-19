import logging
from typing import Tuple, Dict, Union

from rdflib import Graph, URIRef
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore, SPARQLStore
from rdflib.query import Result
from rdflib.store import Store
from rdflib.term import Node

logger = logging.getLogger(__name__)


class InvalidDBKeyTypeError(Exception):
    """Exception called when an invalid DB key is supplied."""
    @classmethod
    def message(cls, value):
        return f'db_key must be a str, instead it received {value} with type {type(value)}.'


def set_store_header_update(store: Store):
    """Call this function before any `Graph.add()` calls to set the appropriate request headers."""
    if 'headers' not in store.kwargs:
        store.kwargs.update({'headers': {}})
    store.kwargs['headers'].update({'content-type': 'application/sparql-update'})


def set_store_header_read(store: Store):
    """Call this function before any `Graph.triples()` calls to set the appropriate request headers."""
    if 'headers' not in store.kwargs:
        store.kwargs.update({'headers': {}})
    store.kwargs['headers'].pop('content-type', None)


class Database:
    g: Graph
    base_uri: URIRef
    databases: Dict[str, 'Database'] = {'default': None}

    def __init__(self, g: Graph, base_uri: Union[str, URIRef]):
        self.g = g
        self.base_uri = URIRef(base_uri)

        if isinstance(g.store, SPARQLUpdateStore) or isinstance(g.store, SPARQLStore):
            self.is_sparql_store = True
        else:
            self.is_sparql_store = False

    @classmethod
    def get_db(cls, db_key: str = 'default') -> 'Database':
        return cls.databases[db_key]

    @classmethod
    def set_db(cls, g: Graph, base_uri: Union[str, URIRef], db_key: str = 'default'):
        if not isinstance(db_key, str):
            raise InvalidDBKeyTypeError(InvalidDBKeyTypeError.message(db_key))
        cls.databases.update({db_key: Database(g, URIRef(base_uri))})

    def write(self, triple: Tuple[Union[Node, None], Union[Node, None], Union[Node, None]]):
        logger.info(f'Adding triple {triple}')
        if self.is_sparql_store:
            set_store_header_update(self.g.store)
        self.g.add(triple)

        # if isinstance(cls.g.store, SPARQLUpdateStore) or isinstance(cls.g.store, SPARQLStore):
        #     set_store_header_update(cls.g.store)
        # cls.g.add(triple)

    def delete(self, triple: Tuple[Union[Node, None], Union[Node, None], Union[Node, None]]):
        logger.info(f'Deleting triple {triple}')
        if self.is_sparql_store:
            set_store_header_update(self.g.store)
        self.g.remove(triple)
        # if isinstance(cls.g.store, SPARQLUpdateStore) or isinstance(cls.g.store, SPARQLStore):
        #     set_store_header_update(cls.g.store)
        # cls.g.remove(triple)

    def read(self, triple: Tuple[Union[Node, None], Union[Node, None], Union[Node, None]]):
        if self.is_sparql_store:
            set_store_header_read(self.g.store)
        for s, p, o in self.g.triples(triple):
            logger.info(f'reading triple {(s, p, o)}')
            yield s, p, o
        # if isinstance(cls.g.store, SPARQLUpdateStore) or isinstance(cls.g.store, SPARQLStore):
        #     set_store_header_read(cls.g.store)
        # for s, p, o in cls.g.triples(triple):
        #     logger.info(f'reading triple {(s, p, o)}')
        #     yield s, p, o

    def sparql_update(self, query: str):
        if self.is_sparql_store:
            set_store_header_update(self.g.store)
        try:
            self.g.store.update(query)
        except Exception as e:
            raise Exception(f'{e}\nFailed with SPARQL query:\n{query}')
        # if isinstance(cls.g.store, SPARQLUpdateStore):
        #     set_store_header_update(cls.g.store)
        # cls.g.store.update(query)

    def sparql(self, query: str) -> Result:
        if self.is_sparql_store:
            set_store_header_read(self.g.store)
        try:
            result = self.g.store.query(query)
        except Exception as e:
            raise Exception(f'{e}\nFailed with SPARQL query:\n{query}')
        return result
        # if isinstance(cls.g.store, SPARQLStore):
        #     set_store_header_read(cls.g.store)
        # return cls.g.store.query(query)