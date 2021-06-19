from rdflib import Graph
from rdflib.namespace import DCTERMS, SKOS, OWL, DCAT, RDFS, RDF

from rdflib_orm.db import models, Database


class Common(models.Model):
    provenance = models.CharField(predicate=DCTERMS.provenance, lang='en', required=True)

    class Meta:
        mixin = True


class ConceptScheme(Common):
    class_type = models.IRIField(predicate=RDF.type, value=SKOS.ConceptScheme)
    title = models.CharField(predicate=DCTERMS.title, lang='en', required=True)
    description = models.CharField(predicate=SKOS.definition, lang='en', required=True)
    created = models.DateTimeField(DCTERMS.created, auto_now_add=True)
    modified = models.DateTimeField(DCTERMS.modified, auto_now=True)
    creator = models.IRIField(predicate=DCTERMS.creator, required=True)
    publisher = models.IRIField(predicate=DCTERMS.publisher, required=True)
    version = models.CharField(predicate=OWL.versionInfo, required=True)
    custodian = models.CharField(predicate=DCAT.contactPoint)
    see_also = models.IRIField(predicate=RDFS.seeAlso, many=True)

    def __repr__(self):
        return f'<{self.__uri__}>'


class Concept(Common):
    class_type = models.IRIField(predicate=RDF.type, value=SKOS.Concept)
    pref_label = models.CharField(predicate=SKOS.prefLabel, lang='en', required=True)
    alt_labels = models.CharField(predicate=SKOS.altLabel, lang='en', many=True)
    definition = models.CharField(predicate=SKOS.definition, lang='en', required=True)
    children = models.IRIField(predicate=SKOS.narrower, many=True, inverse=SKOS.broader)
    other_ids = models.CharField(predicate=SKOS.notation, many=True)
    home_vocab_uri = models.IRIField(predicate=RDFS.isDefinedBy)

    def __repr__(self):
        return f'<{self.__uri__}>'


if __name__ == '__main__':
    g = Graph()
    g.bind('dcterms', DCTERMS)
    g.bind('skos', SKOS)
    g.bind('dcat', DCAT)
    g.bind('owl', OWL)
    Database.set_db(g, base_uri='http://example.com/')

    concept_scheme = ConceptScheme(
        'https://linked.data.gov.au/def/concept_scheme',
        title='A concept scheme',
        description='A description of this concept scheme.',
        creator='https://linked.data.gov.au/org/cgi',  # Accepts a URIRef or a string since the field is an IRIField.
        publisher='https://linked.data.gov.au/org/ga',
        version='0.1.0',
        provenance='Generated using Python',
        custodian='A custodian name',
        see_also=['http://example.com', 'http://another.example.com']  # Accepts a Python list since Field's many=True
    )

    concept_scheme.save()  # Save to store - currently memory store, but works also for remote triplestore.

    concept_scheme.title = 'Modified concept scheme title'
    concept_scheme.save()  # Save changes - we changed the title field.

    concept_a = Concept(
        uri='https://linked.data.gov.au/def/concept_a',
        pref_label='A concept',
        alt_labels=['An alt label', 'another alt label'],
        definition='Definition of this concept.',
        # children=  # Optional field, no children on this concept.
        other_ids=['123', '456'],  # No language tag here :)
        home_vocab_uri=concept_scheme,  # Reference the Concept Scheme Python object directly.
        provenance = 'Generated using RDFLib',
    )

    concept_a.save()

    concept_b = Concept(
        uri='https://linked.data.gov.au/def/concept_b',
        pref_label='Another concept',
        # alt_labels=  # Alt labels are optional.
        definition='Definition is not optional.',
        children=[concept_a],  # Reference the previous concept Python object directly. Notice it will also add the inverse property :)
        # other_ids=  # Optional field again.
        home_vocab_uri=concept_scheme,
        provenance='Generated using rdflib-orm',
    )

    concept_b.save()

    # Let's do some queries.
    queryset = Concept.objects.all()
    print(queryset)
    # <QuerySet [<https://linked.data.gov.au/def/concept_b>, <https://linked.data.gov.au/def/concept_a>]>

    # Get object by URI.
    concept_result = Concept.objects.get('https://linked.data.gov.au/def/concept_a')
    print(concept_result)
    # <https://linked.data.gov.au/def/concept_a>
    print(concept_result.pref_label)
    # A concept
    print(concept_result.definition)
    # Definition of this concept.

    # Not implemented yet. Something planned for the future.
    # Get object by any property, e.g. notation.
    # concept_result = Concept.objects.get(other_ids=123)

    print(len(g))  # 28 triples

    g.serialize('output.ttl', format='turtle')
    """ # Output of Graph.serialize()
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://linked.data.gov.au/def/concept_a> a skos:Concept ;
    dcterms:provenance "Generated using RDFLib"@en ;
    rdfs:isDefinedBy <https://linked.data.gov.au/def/concept_scheme> ;
    skos:altLabel "An alt label",
        "another alt label" ;
    skos:broader <https://linked.data.gov.au/def/concept_b> ;
    skos:definition "Definition of this concept."@en ;
    skos:notation "123",
        "456" ;
    skos:prefLabel "A concept"@en .

<https://linked.data.gov.au/def/concept_b> a skos:Concept ;
    dcterms:provenance "Generated using rdflib-orm"@en ;
    rdfs:isDefinedBy <https://linked.data.gov.au/def/concept_scheme> ;
    skos:definition "Definition is not optional."@en ;
    skos:narrower <https://linked.data.gov.au/def/concept_a> ;
    skos:prefLabel "Another concept"@en .

<https://linked.data.gov.au/def/concept_scheme> a skos:ConceptScheme ;
    dcterms:created "2021-05-26T22:13:50.720468"^^xsd:dateTime ;
    dcterms:creator <https://linked.data.gov.au/org/cgi> ;
    dcterms:modified "2021-05-26T22:13:50.723468"^^xsd:dateTime ;
    dcterms:provenance "Generated using Python"@en ;
    dcterms:publisher <https://linked.data.gov.au/org/ga> ;
    dcterms:title "Modified concept scheme title"@en ;
    rdfs:seeAlso <http://another.example.com>,
        <http://example.com> ;
    owl:versionInfo "0.1.0" ;
    skos:definition "A description of this concept scheme."@en ;
    dcat:contactPoint "A custodian name" .
    """
