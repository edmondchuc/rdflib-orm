import abc
import datetime
from typing import Union, List

from rdflib import URIRef, Literal
from rdflib.namespace import XSD

from rdflib_orm.db.models import Model


class FieldError(Exception):
    pass


class Field(abc.ABC):
    predicate: URIRef
    value: any
    required: bool

    def validate(self, value, cls, field):
        if self.required and value is None:
            raise FieldError(f'{cls} required field "{field}" is not set.')

    @abc.abstractmethod
    def convert(self, value, **kwargs):
        pass

    @abc.abstractmethod
    def convert_to_python(self, value):
        pass


class CharField(Field):
    # TODO: Add many field.
    def __init__(self, predicate: URIRef, value: str = None, max_length: int = None, required: bool = False, lang: str = '', many=False):
        self.predicate = predicate
        self.max_length = max_length
        self.value = value
        self.required = required
        self.lang = lang
        self.many = many

    def validate(self, value: str, cls: str, field: str):
        super(CharField, self).validate(value, cls, field)
        if self.max_length is not None and value is not None:
            length = len(value)
            if length >= self.max_length:
                raise FieldError(f'{cls} exceeds max_length ({self.max_length}) on field {field} ({length}).')

    def convert(self, value, **kwargs):
        if value is None:
            return None
        if not isinstance(value, list):
            return Literal(value, lang=self.lang)
        else:
            # TODO: Improve error message.
            assert isinstance(value, list), f'Expected a list.'
            return [Literal(item) for item in value]

    def convert_to_python(self, value):
        return str(value) if value is not None else None


class IRIField(Field):
    def __init__(self, predicate: URIRef, value: Union[URIRef, str, Model, List[Union[URIRef, str, Model]]] = None, inverse: URIRef = None, required: bool = False, many: bool = False):
        self.predicate = predicate
        self.value = value
        self.inverse = inverse
        self.required = required
        self.many = many

    def convert(self, value: Union[URIRef, Model, List[Union[URIRef, Model]]], **kwargs):
        if value is None:
            return None
        if not isinstance(value, list):
            if isinstance(value, Model):
                return value.__uri__
            try:
                return URIRef(value)
            except Exception as e:
                # TODO: This failed because value is a list of class URIs while self.many is False.
                raise Exception(str(e) + ' ' + str(value))
        else:
            # TODO: Improve error message.
            assert isinstance(value, list), f'Expected a list.'
            result = list()
            for item in value:
                if isinstance(item, Model):
                    result.append(item.__uri__)
                else:
                    result.append(URIRef(item))
            return result

    def convert_to_python(self, value):
        if isinstance(value, Model):
            return str(value.__uri__)
        return str(value) if value is not None else None


class DateTimeField(Field):
    # TODO: Add many field.
    def __init__(self, predicate: URIRef, auto_now: bool = False, auto_now_add: bool = False, value: datetime = None, required: bool = False):
        self.predicate = predicate
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        self.required = required

        if self.auto_now_add:
            self.value = datetime.datetime.now()
        else:
            self.value = value

    def convert(self, value, create_mode=True):
        # The create_mode arg means this convert function was called during model creation, not at retrieval time.
        # Therefore, in Query functions for creation, set create_mode to True while retrieval functions
        # such as filter or get, set create_mode to False.
        if create_mode and self.auto_now:
            value = datetime.datetime.now()
        return Literal(value, datatype=XSD.dateTime) if value is not None else None

    def convert_to_python(self, value):
        return datetime.datetime.fromisoformat(value)


class BooleanField(Field):
    def __init__(self, predicate: URIRef, value: bool = None, required: bool = False):
        self.predicate = predicate
        self.value = value
        self.required = required

    def convert(self, value, **kwargs):
        return Literal(value) if value is not None else None

    def convert_to_python(self, value):
        if str(value) == 'false':
            return False
        elif str(value) == 'true':
            return True
        else:
            raise Exception(f'Could not parse value "{value}" to Python bool.')
