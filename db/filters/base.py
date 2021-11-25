from dataclasses import dataclass, field#, replace
from enum import Enum
from typing import Any, List, Union, Type

class PredicateSuperType(Enum):
    LEAF = "leaf"
    BRANCH = "branch"

class BranchPredicateType(Enum):
    NOT = "not"
    OR = "or"
    AND = "and"

class LeafPredicateType(Enum):
    """Note that negation is achieved via BranchPredicateType.NOT"""
    EQUAL = "equal"
    GREATER = "greater"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESSER = "lesser"
    LESSER_OR_EQUAL = "lesser_or_equal"
    EMPTY = "empty"
    IN = "in"

class ParameterCount(Enum):
    SINGLE = "single"
    MULTI = "multi"
    NONE = "none"

predicateTypesToSAIds = {
    BranchPredicateType.NOT: 'not',
    BranchPredicateType.AND: 'and',
    BranchPredicateType.OR: 'or',
    LeafPredicateType.EQUAL: 'eq',
    LeafPredicateType.GREATER: 'gt',
    LeafPredicateType.GREATER_OR_EQUAL: 'ge',
    LeafPredicateType.LESSER: 'lt',
    LeafPredicateType.LESSER_OR_EQUAL: 'le',
    LeafPredicateType.EMPTY: 'is_null',
    LeafPredicateType.IN: 'in',
}

def getSAIdFromPredicateType(type: Union[LeafPredicateType, BranchPredicateType]) -> str:
    if type in predicateTypesToSAIds:
        return predicateTypesToSAIds[type]
    else:
        raise Exception("This should never happen.")

# frozen=True provides immutability
# TODO add kw_only=True on upgrade to Python 3.10, improves readability and prevents argument order errors
def frozen_dataclass(f):
    return dataclass(frozen=True)(f)

def static(value):
    """
    Declares a static field on a dataclass.
    """
    return field(init=False, default=value)

@frozen_dataclass
class Predicate:
    superType: PredicateSuperType
    type: Union[LeafPredicateType, BranchPredicateType]
    parameterCount: ParameterCount

    def saId(self) -> str:
        return getSAIdFromPredicateType(self.type)

def takesParameterThatsAMathesarType(predicateSubClass: Type[Predicate]) -> bool:
    return (
        issubclass(predicateSubClass, Leaf)
        and not issubclass(predicateSubClass, NoParameter)
    )

@frozen_dataclass
class Leaf(Predicate):
    superType: PredicateSuperType = static(PredicateSuperType.LEAF)
    type: LeafPredicateType
    field: str 

@frozen_dataclass
class SingleParameter:
    parameterCount: ParameterCount = static(ParameterCount.SINGLE)
    parameter: Any

@frozen_dataclass
class MultiParameter:
    parameterCount: ParameterCount = static(ParameterCount.MULTI)
    parameters: List[Any]

@frozen_dataclass
class NoParameter:
    parameterCount: ParameterCount = static(ParameterCount.NONE)

@frozen_dataclass
class Branch(Predicate):
    superType: PredicateSuperType = static(PredicateSuperType.BRANCH)
    type: BranchPredicateType

@frozen_dataclass
class Equal(SingleParameter, Leaf, Predicate):
    type: LeafPredicateType = static(LeafPredicateType.EQUAL)

@frozen_dataclass
class Greater(SingleParameter, Leaf, Predicate):
    type: LeafPredicateType = static(LeafPredicateType.GREATER)

@frozen_dataclass
class GreaterOrEqual(SingleParameter, Leaf, Predicate):
    type: LeafPredicateType = static(LeafPredicateType.GREATER_OR_EQUAL)

@frozen_dataclass
class Lesser(SingleParameter, Leaf, Predicate):
    type: LeafPredicateType = static(LeafPredicateType.LESSER)

@frozen_dataclass
class LesserOrEqual(SingleParameter, Leaf, Predicate):
    type: LeafPredicateType = static(LeafPredicateType.LESSER_OR_EQUAL)

@frozen_dataclass
class Empty(NoParameter, Leaf, Predicate):
    type: LeafPredicateType = static(LeafPredicateType.EMPTY)

@frozen_dataclass
class In(MultiParameter, Leaf, Predicate):
    type: LeafPredicateType = static(LeafPredicateType.IN)

@frozen_dataclass
class Not(SingleParameter, Branch, Predicate):
    type: BranchPredicateType = static(BranchPredicateType.NOT)

@frozen_dataclass
class And(MultiParameter, Branch, Predicate):
    type: BranchPredicateType = static(BranchPredicateType.AND)

@frozen_dataclass
class Or(MultiParameter, Branch, Predicate):
    type: BranchPredicateType = static(BranchPredicateType.OR)

def getSAFilterSpecFromPredicate(pred: Predicate) -> dict:
    if isinstance(pred, Leaf):
        if isinstance(pred, SingleParameter):
            return {'field': pred.field, 'op': pred.saId(), 'value': pred.parameter}
        elif isinstance(pred, MultiParameter):
            return {'field': pred.field, 'op': pred.saId(), 'value': pred.parameters}
        elif isinstance(pred, NoParameter):
            return {'field': pred.field, 'op': pred.saId()}
        else:
            raise Exception("This should never happen.")
    elif isinstance(pred, Branch):
        if isinstance(pred, SingleParameter):
            subject = getSAFilterSpecFromPredicate(pred.parameter)
            return {pred.saId(): [subject]}
        elif isinstance(pred, MultiParameter):
            subjects = [ getSAFilterSpecFromPredicate(subject) for subject in pred.parameters ]
            return {pred.saId(): subjects}
        else:
            raise Exception("This should never happen.")
    else:
        raise Exception("This should never happen.")

allPredicateSubClasses = [
    Equal,
    Greater,
    GreaterOrEqual,
    Lesser,
    LesserOrEqual,
    Empty,
    In,
    Not,
    And,
    Or,
    ]
