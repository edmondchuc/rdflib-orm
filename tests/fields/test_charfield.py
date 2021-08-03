import pytest
from rdflib import RDFS, OWL, RDF, Graph, Literal

from rdflib_orm import models
from rdflib_orm.db import Database
from tests import BASE_URI


def test_required_field_raises_exception():
    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        char_field = models.CharField(RDFS.comment, required=True)

    with pytest.raises(models.FieldError):
        TestModel(uri='test')


def test_charfield_create():
    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        char_field = models.CharField(RDFS.comment)

    model = TestModel(uri='test', char_field='test')
    assert model.char_field == 'test'


def test_charfield_length_validation_raises():
    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        char_field = models.CharField(RDFS.comment, max_length=1)

    with pytest.raises(models.FieldError):
        TestModel(uri='test', char_field='test')


def test_charfield_convert_to_rdf():
    g = Graph()
    Database.set_db(g, base_uri=BASE_URI)

    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        comment = models.CharField(RDFS.comment)

    model = TestModel(uri='test', comment='comment')
    model.save()

    value = g.value(BASE_URI.test, RDFS.comment, None)
    assert str(value) == 'comment'


def test_charfield_convert_to_rdf_none_value():
    g = Graph()
    Database.set_db(g, base_uri=BASE_URI)

    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        comment = models.CharField(RDFS.comment)

    model = TestModel(uri='test', comment=None)
    model.save()

    value = g.value(BASE_URI.test, RDFS.comment, None)
    assert value is None


def test_charfield_convert_to_rdf_list_value():
    g = Graph()
    Database.set_db(g, base_uri=BASE_URI)

    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        comment = models.CharField(RDFS.comment, many=True)

    model = TestModel(uri='test', comment=None)
    model.comment = ['comment-1', 'comment-2']
    model.save()

    values = g.objects(BASE_URI.test, RDFS.comment)
    assert set(list(values)) == {Literal('comment-1'), Literal('comment-2')}


def test_charfield_convert_to_rdf_list_value_raises():
    g = Graph()
    Database.set_db(g, base_uri=BASE_URI)

    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        comment = models.CharField(RDFS.comment, many=True)

    model = TestModel(uri='test', comment=None)
    model.comment = 'comment'

    with pytest.raises(models.FieldError):
        model.save()


def test_charfield_convert_to_rdf_non_list_value_raises():
    g = Graph()
    Database.set_db(g, base_uri=BASE_URI)

    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        comment = models.CharField(RDFS.comment, many=True)

    model = TestModel(uri='test', comment=False)

    with pytest.raises(models.FieldError):
        model.save()


def test_charfield_query():
    g = Graph()
    Database.set_db(g, base_uri=BASE_URI)

    class TestModel(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        comment = models.CharField(RDFS.comment, many=True)

    model = TestModel(uri='test', comment=['123'])
    model.save()

    test_model = TestModel.objects.get(uri=BASE_URI.test)
    assert test_model.comment == ['123']

    model.comment.append('456')
    model.save()
    test_model = TestModel.objects.get(uri=BASE_URI.test)
    assert set(test_model.comment) == {'123', '456'}

    model2 = TestModel(uri='test2', comment=['567', '8910'])
    model2.save()
    test_model2 = TestModel.objects.get(uri=BASE_URI.test2)
    assert set(test_model2.comment) == {'567', '8910'}

    # TODO: If comment is many=True, then passing it a None should result in an empty list?
    model3 = TestModel(uri='test3', comment=None)
    model3.save()
    test_model3 = TestModel.objects.get(uri=BASE_URI.test3)
    assert test_model3.comment is None

    # Test with comment field, many=False
    class TestModelSingle(models.Model):
        class_type = models.IRIField(RDF.type, OWL.Thing)
        comment = models.CharField(RDFS.comment)

    model4 = TestModelSingle(uri='test4', comment='comment')
    model4.save()
    test_model4 = TestModelSingle.objects.get(BASE_URI.test4)
    assert test_model4.comment == 'comment'
