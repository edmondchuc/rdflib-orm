import pytest
from rdflib import RDFS, OWL, RDF

from rdflib_orm import models


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
