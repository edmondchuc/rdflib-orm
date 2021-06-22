import inspect
import logging
import traceback
from typing import List

from rdflib import Graph, URIRef, BNode

from rdflib_orm.db import Database

logger = logging.getLogger(__name__)


class InstanceNotFoundError(Exception):
    """Exception called when retrieve queries return no matching values."""
    pass


class QuerySet(set):
    def __str__(self):
        instance = ''
        for i, item in enumerate(self):
            if i != len(self) - 1:
                instance += str(item) + ', '
            else:
                instance += str(item)
        return f'<{self.__class__.__name__} [{instance}]>'

    def order_by(self, value: str):
        """Model.objects.all().order_by('label')"""
        queryset = list(self)
        queryset.sort(key=lambda x: getattr(x, value))
        return queryset


class Query:
    def __init__(self, model_class: 'Model'):
        self.model_class = model_class
        super(Query, self).__init__()

    @staticmethod
    def _get_instance_uri_by_predicate_and_value(predicate, value, db: Database) -> List[URIRef]:
        instance_uris = list()
        if isinstance(value, list):
            for val in value:
                for s, p, o in db.read((None, predicate, val)):
                    instance_uris.append(s)
        else:
            for s, p, o in db.read((None, predicate, value)):
                instance_uris.append(s)
        return instance_uris

    @staticmethod
    def _get_sparql_query_uri_lists(uri_list):
        """String used as part of the get and filter SPARQL query construction."""
        if isinstance(uri_list, list):
            class_type_str = ''
            for i, type_ in enumerate(uri_list):
                class_type_str += f'<{type_}>'
                if i != len(uri_list) - 1:
                    class_type_str += ', '
            return class_type_str
        else:
            return f'<{uri_list}>'

    def create(self, uri: str, db_key: str = 'default', **kwargs):
        """Create and save an object in a single step.

        Otherwise, this is equivalent to instantiating
        a new `model` and calling `model.save()`.
        """
        # TODO: Raise error if URI already exists? Or maybe a warning?
        instance = self.model_class(uri, **kwargs)
        instance.save(db_key=db_key)
        return instance

    def get(self, uri: str, db_key: str = 'default', **kwargs) -> 'Model':
        # TODO: Basically this was a copy paste from the filter function. See if there's a better way to structure
        #  the duplicate code to keep it simple, readable and DRY.

        # TODO: Look at raising the same exceptions as Django.
        #  See https://docs.djangoproject.com/en/3.1/topics/db/queries/#retrieving-a-single-object-with-get
        db = Database.get_db(db_key)
        if not isinstance(uri, BNode):
            uri = URIRef(uri)
        if db.is_sparql_store:
        # if isinstance(Database.g.store, SPARQLUpdateStore) or isinstance(Database.g.store, SPARQLStore):
        #     uri = kwargs.get('uri', None)
            # uri = f'<{uri}>' if uri else '?uri'
            uri_sparql_str = f'<{uri}>'
            # kwargs.pop('uri')

            class_type = self.model_class.class_type.value
            class_type_str = self._get_sparql_query_uri_lists(class_type)
            where_clause = ''
            for key, val in kwargs.items():
                field = getattr(self.model_class, key)
                predicate = f'<{field.predicate}>'
                o = field.convert(val, create_mode=False)
                literal_o = f'"{o}"'
                datatype = f'<{o.datatype}>' if type(o) == Literal else None
                uri_o = f'<{o}>'
                if datatype:
                    literal_o = f'{literal_o}^^{datatype}'

                where_clause += f'\n\t\t\t{predicate} {literal_o if not isinstance(o, URIRef) else uri_o};'
            po = '\n\t\t\t?p ?o .'
            where_clause += po
            query = f"""
# SPARQL filter query
SELECT *
WHERE {{ 
    GRAPH <{db.g.identifier}> {{
        {uri_sparql_str} a {class_type_str} ;
{where_clause}
    }}
}}
            """
            logger.info(query)
            query_result = db.sparql(query)

            g = Graph()
            for row in query_result:
                if uri:
                    g.add((uri, row['p'], row['o']))
                else:
                    # TODO: This won't happen anymore now that uri is a mandatory arg in this get function.
                    g.add((row['uri'], row['p'], row['o']))

            model_attributes = self.model_class.get_model_attributes(self.model_class)
            # Attribute and values to use to create an instance of self.model.
            to_be_instance_values = dict()

            for s, p, o in g.triples((None, None, None)):
                for model_attr in model_attributes:
                    if model_attr[1].predicate == p:
                        if model_attr[0] not in to_be_instance_values:
                            to_be_instance_values[model_attr[0]] = model_attr[1].convert_to_python(o)
                        else:
                            # There's more than one value for this predicate.
                            # Convert the current value into a list and append the new value or
                            # simply append to the existing list.
                            if isinstance(to_be_instance_values[model_attr[0]], list):
                                to_be_instance_values[model_attr[0]].append(model_attr[1].convert_to_python(o))
                            else:
                                to_be_instance_values[model_attr[0]] = [to_be_instance_values[model_attr[0]],
                                                                        model_attr[1].convert_to_python(o)]
                        continue
            if to_be_instance_values:
                return self.model_class(uri, **to_be_instance_values)
            else:
                raise InstanceNotFoundError(f'No instance found with URI {uri}')
        else:
            # for key, val in kwargs.items():
            #     filtered_attr: Field = getattr(self.model_class, key)
            #     converted_value = filtered_attr.convert(val)
            #     instance_uris = self._get_instance_uri_by_predicate_and_value(filtered_attr.predicate, converted_value, db)

            model_attributes = self.model_class.get_model_attributes(self.model_class)
            # Attribute and values to use to create an instance of self.model.
            to_be_instance_values = dict()

            for s, p, o in db.read((uri, None, None)):
                for model_attr in model_attributes:
                    if model_attr[1].predicate == p:
                        if model_attr[0] not in to_be_instance_values:
                            to_be_instance_values[model_attr[0]] = model_attr[1].convert_to_python(o)
                        else:
                            # There's more than one value for this predicate.
                            # Convert the current value into a list and append the new value or
                            # simply append to the existing list.
                            if isinstance(to_be_instance_values[model_attr[0]], list):
                                to_be_instance_values[model_attr[0]].append(
                                    model_attr[1].convert_to_python(o))
                            else:
                                to_be_instance_values[model_attr[0]] = [
                                    to_be_instance_values[model_attr[0]],
                                    model_attr[1].convert_to_python(o)]
                        continue

            # Check and see if the to_be_instance_values dict
            # matches the values supplied in the filter kwargs.
            is_match = False

            # Not required anymore since we fetch via URI of instance.
            # for k in kwargs:
            #     # Sometimes it's convenient to pass an RDFLib namespace URIRef, cast it to str.
            #     if isinstance(kwargs[k], URIRef):
            #         kwargs[k] = str(kwargs[k])
            #
            #     if k in to_be_instance_values:
            #         if kwargs[k] == to_be_instance_values[k]:
            #             is_match = True
            #         else:
            #             # One of the filters didn't match, break loop.
            #             is_match = False
            #             break

            if to_be_instance_values:
                return self.model_class(uri, **to_be_instance_values)
            else:
                raise InstanceNotFoundError(f'No instance found with URI {uri}')

    def filter(self, db_key: str = 'default', **kwargs) -> QuerySet:
        """Get a queryset of objects based on the filter parameters."""
        assert 'uri' not in kwargs, 'Found key uri in kwargs. If you want to retrieve a single instance by URI, use Model.objects.get() instead.'

        queryset = QuerySet()
        db = Database.get_db(db_key)

        if db.is_sparql_store:
        # if isinstance(Database.g.store, SPARQLUpdateStore) or isinstance(Database.g.store, SPARQLStore):
            class_type = self.model_class.class_type.value
            class_type_str = self._get_sparql_query_uri_lists(class_type)
            where_clause = ''
            for key, val in kwargs.items():
                field = getattr(self.model_class, key)
                predicate = f'<{field.predicate}>'
                o = field.convert(val, create_mode=False)
                if isinstance(o, URIRef) or isinstance(o, list) and isinstance(o[0], URIRef):
                    is_uri = True
                else:
                    is_uri = False
                literal_o = f'"{o}"'
                datatype = f'<{o.datatype}>' if type(o) == Literal else None
                uri_o = self._get_sparql_query_uri_lists(o)
                if datatype:
                    literal_o = f'{literal_o}^^{datatype}'

                where_clause += f'\n\t\t\t{predicate} {literal_o if not is_uri else uri_o};'
            po = '\n\t\t\t?p ?o .'
            where_clause += po
            query = f"""
# SPARQL filter query
SELECT *
WHERE {{ 
    GRAPH <{db.g.identifier}> {{
        ?uri a {class_type_str} ;
{where_clause}
    }}
}}
            """
            logger.info(query)
            query_result = db.sparql(query)

            g = Graph()
            for row in query_result:
                g.add((row['uri'], row['p'], row['o']))

            query_instance_uris = f"""
# SPARQL filter query
SELECT DISTINCT ?uri
WHERE {{ 
    GRAPH <{db.g.identifier}> {{
        ?uri a {class_type_str} ;
{where_clause}
    }}
}}
"""
            logger.info(query_instance_uris)
            instances = db.sparql(query_instance_uris)

            for instance_row in instances:
                instance_uri = instance_row['uri']

                model_attributes = self.model_class.get_model_attributes(self.model_class)
                # Attribute and values to use to create an instance of self.model.
                to_be_instance_values = dict()

                for s, p, o in g.triples((instance_uri, None, None)):
                    for model_attr in model_attributes:
                        if model_attr[1].predicate == p:
                            if model_attr[0] not in to_be_instance_values:
                                to_be_instance_values[model_attr[0]] = model_attr[1].convert_to_python(o)
                            else:
                                # There's more than one value for this predicate.
                                # Convert the current value into a list and append the new value or
                                # simply append to the existing list.
                                if isinstance(to_be_instance_values[model_attr[0]], list):
                                    to_be_instance_values[model_attr[0]].append(model_attr[1].convert_to_python(o))
                                else:
                                    to_be_instance_values[model_attr[0]] = [to_be_instance_values[model_attr[0]],
                                                                            model_attr[1].convert_to_python(o)]
                            continue
                queryset.add(self.model_class(instance_uri, **to_be_instance_values))
        else:
            for key, val in kwargs.items():
                filtered_attr: 'Field' = getattr(self.model_class, key)
                converted_value = filtered_attr.convert(val)
                instance_uris = self._get_instance_uri_by_predicate_and_value(filtered_attr.predicate, converted_value, db)

                if instance_uris:
                    for instance_uri in instance_uris:
                        model_attributes = self.model_class.get_model_attributes(self.model_class)
                        # Attribute and values to use to create an instance of self.model.
                        to_be_instance_values = dict()

                        for s, p, o in db.read((instance_uri, None, None)):
                            for model_attr in model_attributes:
                                if model_attr[1].predicate == p:
                                    if model_attr[0] not in to_be_instance_values:
                                        to_be_instance_values[model_attr[0]] = model_attr[1].convert_to_python(o)
                                    else:
                                        # There's more than one value for this predicate.
                                        # Convert the current value into a list and append the new value or
                                        # simply append to the existing list.
                                        if isinstance(to_be_instance_values[model_attr[0]], list):
                                            to_be_instance_values[model_attr[0]].append(model_attr[1].convert_to_python(o))
                                        else:
                                            to_be_instance_values[model_attr[0]] = [to_be_instance_values[model_attr[0]], model_attr[1].convert_to_python(o)]
                                    continue

                        # Check and see if the to_be_instance_values dict
                        # matches the values supplied in the filter kwargs.
                        is_match = False
                        for k in kwargs:
                            # Sometimes it's convenient to pass an RDFLib namespace URIRef, cast it to str.
                            if isinstance(kwargs[k], URIRef):
                                kwargs[k] = str(kwargs[k])

                            if k in to_be_instance_values:
                                if isinstance(kwargs[k], list) and isinstance(kwargs[k][0], URIRef):
                                    # Process the list to compare that they are the same by casting to string,
                                    # since the to_be_instance_values always contains Python types.
                                    # kwargs[k] = [str(uri) for uri in kwargs[k]]
                                    if k == 'class_type' and all(str(x) in to_be_instance_values[k] for x in kwargs[k]):
                                        is_match = True
                                        continue
                                if sorted(kwargs[k]) == sorted(to_be_instance_values[k]):
                                    is_match = True
                                else:
                                    # One of the filters didn't match, break loop.
                                    is_match = False
                                    break

                        if is_match:
                            # Create the instance and add it to the queryset.
                            queryset.add(self.model_class(instance_uri, **to_be_instance_values))

        return queryset

    def exclude(self, db_key: str = 'default', **kwargs) -> QuerySet:
        raise NotImplementedError()

    def all(self, db_key: str = 'default',):
        """Get all instances of the class."""
        return self.filter(class_type=self.model_class.class_type.value, db_key=db_key)


class ModelBase(type):
    def __new__(cls, name, bases, attrs, **kwargs):
        new_class: Union[Model, type] = super().__new__(cls, name, bases, attrs)

        # TODO: Improve error message here.
        # Ensure class models define the attribute class_type unless they are a mixin class.
        if new_class.Meta.mixin == False and new_class.__name__ not in ('ModelBase', 'Model'):
            assert hasattr(new_class, 'class_type'), f'{cls} must have the attribute class_type.'
            class_type = getattr(new_class, 'class_type')
            assert isinstance(class_type, IRIField), f'{cls} must be an instance of IRIField.'

        query = Query(new_class)
        new_class.objects = query
        return new_class


class Model(metaclass=ModelBase):
    class_type = None

    class Meta:
        mixin = False

    def __str__(self, instance_name: str = None):
        if instance_name is not None:
            return f"<{self.__class__.__name__}: {instance_name}>"
        else:
            return self.__repr__()

    def __hash__(self):
        return hash(self.__uri__)

    def __eq__(self, other):
        if isinstance(other, Model):
            return self.__uri__ == other.__uri__
        # TODO: Improve this.
        raise NotImplementedError()

    def get_model_attributes(self) -> List[tuple[str, any]]:
        return list(
            # Filter instance attributes.
            filter(
                lambda tuple_item:
                    # Filter out attributes that start with '__'.
                    not tuple_item[0].startswith('__')
                    # Filter out methods.
                    and not inspect.ismethod(tuple_item[1])
                    # Filter out ORM reserved attributes.
                    and tuple_item[0] not in ('objects', 'get_model_attributes', 'save', 'Meta', 'serialize'),
                inspect.getmembers(self)
            )
        )

    def __init__(self, uri: str, db_key: str = 'default', **kwargs):
        cls = self.__class__
        db = Database.get_db(db_key)
        # self.__objects__ = Query(cls)  # I don't think this is used anywhere?

        if not uri:
            raise Exception(f'{cls} instance uri is an empty string.')
        else:
            if not uri.startswith('http'):
                self.__uri__ = URIRef(db.base_uri + uri)
            else:
                self.__uri__ = URIRef(uri)

        self.__attributes__ = self.get_model_attributes()

        # try:
        for attribute_name, attribute_field in self.__attributes__:
            if kwargs.get(attribute_name):
                value = kwargs[attribute_name]
                attribute_field.validate(value, cls, attribute_name)
                # converted_value = attribute_field.convert(value)
                setattr(self, attribute_name, value)
            else:
                # Value was not passed in through the constructor, check if there's a default value
                # on the class field and set it.
                value = attribute_field.value
                attribute_field.validate(value, cls, attribute_name)
                # converted_value = attribute_field.convert(value)
                setattr(self, attribute_name, value)
        # except Exception as e:
        #     # TODO: Check why we need this in a try except block?
        #     logger.error(traceback.print_exc())
        #     logger.error(str(e))
        #     raise Exception(f'Failed creating {cls} instance with identifier {self.__uri__}')

    def serialize(self, format='turtle'):
        uri = self.__uri__
        cls = self.__class__

        g = Graph()

        for attribute_name, attribute_field in self.__attributes__:
            predicate = attribute_field.predicate
            inverse = getattr(attribute_field, 'inverse', None)
            value = getattr(self, attribute_name)

            attribute_field.validate(value, cls, attribute_name)
            converted_value = attribute_field.convert(value, create_mode=False)

            if converted_value is not None:
                if isinstance(converted_value, list):
                    for item in converted_value:
                        g.add((uri, predicate, item))
                        if inverse is not None:
                            g.add((item, inverse, uri))
                else:
                    g.add((uri, predicate, converted_value))
                    if inverse is not None:
                        g.add((converted_value, inverse, uri))
        return g.serialize(format=format).decode('utf-8')

    def save(self, db_key: str = 'default'):
        # g = Database.g
        uri = self.__uri__
        cls = self.__class__
        db = Database.get_db(db_key)

        # Store current state in a temp graph for naive   transactional rollback functionality.
        previous_state = Graph()
        for _, p, o in db.read((uri, None, None)):
            previous_state.add((uri, p, o))

        # for s, p, _ in Database.read((None, None, uri)):
        #     previous_state.add((s, p, uri))

        def delete_current_triples(uri: URIRef):
            g = Database.get_db(db_key)
            if g.is_sparql_store:
                # TODO: Use SPARQL query only if it's a SPARQL store, otherwise use Database.read.
                query = f"""
                    DELETE {{
                        GRAPH <{db.g.identifier}> {{
                            <{uri}> ?p ?o .
                        }}
                    }}
                    WHERE {{
                        GRAPH <{db.g.identifier}> {{
                            <{uri}> ?p ?o .
                        }}
                    }}
                """
                db.sparql_update(query)
            else:
                # Inefficient - the RDFLib SPARQLUpdateStore sends each triple as a HTTP request.
                for _, p, o in g.read((uri, None, None)):
                    g.delete((uri, p, o))
                for s, p, _ in g.read((None, None, uri)):
                    g.delete((s, p, uri))

        delete_current_triples(uri)

        try:
            for attribute_name, attribute_field in self.__attributes__:
                predicate = attribute_field.predicate
                inverse = getattr(attribute_field, 'inverse', None)
                value = getattr(self, attribute_name)

                attribute_field.validate(value, cls, attribute_name)
                converted_value = attribute_field.convert(value)

                if converted_value is not None:
                    if isinstance(converted_value, list):
                        for item in converted_value:
                            db.write((uri, predicate, item))
                            if inverse is not None:
                                db.write((item, inverse, uri))
                    else:
                        db.write((uri, predicate, converted_value))
                        if inverse is not None:
                            db.write((converted_value, inverse, uri))
        except Exception as e:
            # Something bad happened, rollback.
            logger.error(traceback.print_exc())
            logger.error(str(e))

            # Delete the current transaction.
            logger.info('Rolling back transaction')
            logger.info('Deleting current transaction')
            delete_current_triples(uri)

            # Rollback.
            logger.info('Restoring previous state')
            # SPARQLUpdateStore does not understand the overloaded += operator.
            # Database.g += previous_state
            # Manually restore by calling the Database.write() function.
            for s, p, o in previous_state.triples((None, None, None)):
                db.write((s, p, o))

            logger.info('Transaction rollback complete')


# Avoid circular imports by importing fields after the model-related classes have been initialised.
from rdflib_orm.fields import *
