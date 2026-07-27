from dataclasses import dataclass
from typing import Literal, Optional

NodeType = Literal["atomic_comparable", "atomic_conceptual", "branch"]

RelationType = Literal[
    "prerequisite_of", "alternative_to", "contrasts_with", "composes_with", "applied_in"
]


@dataclass
class EdgeContext:
    """Uma aresta real do no, usada como insumo fechado anti-alucinacao."""
    neighbor_label: str
    relation_type: RelationType
    confidence: float


@dataclass
class NodeClassificationInput:
    node_id: str
    label: str
    description_md: Optional[str]
    neighbor_labels: list[str]
    structural_guess: NodeType


@dataclass
class EdgeClassificationInput:
    pair_id: str
    node_a_label: str
    node_a_description_md: Optional[str]
    node_b_label: str
    node_b_description_md: Optional[str]


@dataclass
class EdgeClassificationResult:
    relation_type: RelationType
    confidence: float


@dataclass
class ContentGenerationInput:
    label: str
    node_type: NodeType
    description_md: Optional[str]
    edges: list[EdgeContext]
    retry_reason: Optional[str] = None


@dataclass
class AuditResult:
    approved: bool
    reason: Optional[str] = None


@dataclass
class MentoriaTurn:
    role: Literal["mentora", "usuario"]
    text: str
