from app.ai.parsing import parse_edge_classification, parse_node_type


def test_parse_node_type_accepts_valid_value():
    assert parse_node_type("branch", fallback="atomic_conceptual") == "branch"


def test_parse_node_type_falls_back_on_invalid_value():
    assert parse_node_type("nao sei", fallback="atomic_conceptual") == "atomic_conceptual"


def test_parse_node_type_falls_back_on_none():
    assert parse_node_type(None, fallback="branch") == "branch"


def test_parse_edge_classification_accepts_valid_relation():
    result = parse_edge_classification('{"relation_type": "prerequisite_of", "confidence": 0.8}')
    assert result is not None
    assert result.relation_type == "prerequisite_of"
    assert result.confidence == 0.8


def test_parse_edge_classification_none_relation_means_no_edge():
    assert parse_edge_classification('{"relation_type": "none"}') is None


def test_parse_edge_classification_rejects_hallucinated_relation_type():
    """Regressao: um modelo mais fraco (ex: Groq llama-3.1-8b) pode ignorar
    o vocabulario fechado e inventar um relation_type livre. Isso nao pode
    propagar pro banco (que tem CHECK constraint e quebraria a chamada
    inteira) — o par deve simplesmente virar 'sem relacao', nao um crash."""
    result = parse_edge_classification('{"relation_type": "relates_to", "confidence": 0.7}')
    assert result is None


def test_parse_edge_classification_handles_malformed_json():
    assert parse_edge_classification("isso nao e json") is None


def test_parse_edge_classification_handles_none_input():
    assert parse_edge_classification(None) is None


def test_parse_edge_classification_defaults_confidence_when_missing_or_invalid():
    result = parse_edge_classification('{"relation_type": "applied_in"}')
    assert result.confidence == 0.5

    result2 = parse_edge_classification('{"relation_type": "applied_in", "confidence": "alta"}')
    assert result2.confidence == 0.5
