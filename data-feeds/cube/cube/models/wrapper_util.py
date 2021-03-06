from typing import Any, List, TypeVar, Callable, Type, cast
from datetime import datetime
import dateutil.parser

T = TypeVar("T")


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_none_of_int(x: Any) -> Any:
    assert x is None
    return 0


def from_none_of_float(x: Any) -> Any:
    assert x is None
    return 0.0


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_datetime(x: Any) -> datetime:
    return dateutil.parser.parse(x)


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def from_float_string(x: Any) -> float:
    assert isinstance(x, (str, float))
    try:
        return float(x)
    except:
        pass
    assert False


def from_int_string(x: Any) -> float:
    assert isinstance(x, (str, int))
    try:
        if '' == x:
            return 0
        return int(x)
    except:
        pass
    assert False


def to_float(x: Any) -> float:
    assert isinstance(x, float)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()