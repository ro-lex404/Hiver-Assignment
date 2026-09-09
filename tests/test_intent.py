from src.intent.classifier import IntentClassifier
from src.intent.taxonomy import ALL_INTENTS

def test_intent_classifier_delivery():
    clf = IntentClassifier()
    res = clf.predict("Where is my package? It is late and tracking TBA1234 has no updates.")
    assert res["intent"] == "ORDER_STATUS_DELIVERY"
    assert res["confidence"] > 0.60

def test_intent_classifier_refund():
    clf = IntentClassifier()
    res = clf.predict("I dropped off my return at Kohl's 5 days ago, when is my refund coming?")
    assert res["intent"] == "REFUND_AND_RETURNS"

def test_intent_classifier_security():
    clf = IntentClassifier()
    res = clf.predict("My account was hacked and someone changed my password and email!")
    assert res["intent"] == "ACCOUNT_ACCESS_SECURITY"

def test_intent_classifier_empty():
    clf = IntentClassifier()
    res = clf.predict("")
    assert res["intent"] in ALL_INTENTS
