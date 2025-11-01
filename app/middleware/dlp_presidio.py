from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()


def presidio_scan(text: str):
    results = analyzer.analyze(text=text, entities=[], language="en")
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text, [r.entity_type for r in results]
