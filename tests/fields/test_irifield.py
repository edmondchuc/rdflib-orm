import pytest
from rdflib import Graph, URIRef

from rdflib_orm import models
from rdflib.namespace import RDF, OWL

from rdflib_orm.db import Database
from tests import BASE_URI


def test_required_field_raises():
    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        irifield = models.IRIField(RDF.value, required=True)

    with pytest.raises(models.FieldError):
        TestModel(uri='test')


def test_irifield_create():
    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        irifield = models.IRIField(RDF.value)

    model = TestModel(uri='test', irifield='123')
    assert model.irifield == '123'


def test_irifield_convert_to_rdf():
    g = Graph()
    Database.set_db(g, base_uri=BASE_URI)

    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        irifield = models.IRIField(RDF.value)

    model = TestModel(uri='test', irifield='123')
    model.save()

    value = g.value(BASE_URI.test, RDF.value, None)
    assert value == URIRef('123')


def test_irifield_convert_to_rdf_none():
    g = Graph()
    Database.set_db(g, base_uri=BASE_URI)

    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        irifield = models.IRIField(RDF.value)

    model = TestModel(uri='test', irifield=None)
    model.save()

    value = g.value(BASE_URI.test, RDF.value, None)
    assert value is None


def test_irifield_convert_to_rdf_list_value():
    g = Graph()
    Database.set_db(g, base_uri=BASE_URI)

    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        irifield = models.IRIField(RDF.value, many=True)

    model = TestModel(uri='test', irifield=['123', '456'])
    model.save()

    values = g.objects(BASE_URI.test, RDF.value)
    assert set(list(values)) == {URIRef('123'), URIRef('456')}


def test_irifield_convert_to_rdf_list_value_raises():
    g = Graph()
    Database.set_db(g, base_uri=BASE_URI)

    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        irifield = models.IRIField(RDF.value, many=True)

    model = TestModel(uri='test', irifield='123')
    with pytest.raises(models.FieldError):
        model.save()
