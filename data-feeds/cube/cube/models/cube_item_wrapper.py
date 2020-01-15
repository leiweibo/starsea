# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = cube_item_wrapper_from_dict(json.loads(json_string))

from typing import Optional, Any, List
from cube.models.wrapper_util import *


class CubeItemWrapper:
    symbol: Optional[str]
    market: Optional[str]
    name: Optional[str]
    net_value: Optional[float]
    daily_gain: Optional[float]
    monthly_gain: Optional[float]
    total_gain: Optional[float]
    annualized_gain: Optional[float]
    closed_at: Optional[int]
    total_score: Optional[float]
    report_updated_time: Optional[int]

    def __init__(self, symbol: Optional[str], market: Optional[str], name: Optional[str], net_value: Optional[float],
                 daily_gain: Optional[float], monthly_gain: Optional[float], total_gain: Optional[float],
                 annualized_gain: Optional[float],
                 closed_at: Optional[int]
                 ) -> None:
        self.symbol = symbol
        self.market = market
        self.name = name
        self.net_value = net_value
        self.daily_gain = daily_gain
        self.monthly_gain = monthly_gain
        self.total_gain = total_gain
        self.annualized_gain = annualized_gain
        self.closed_at = closed_at
        self.total_score = 0
        self.report_updated_time = 0

    @staticmethod
    def from_dict(obj: Any) -> 'CubeItemWrapper':
        assert isinstance(obj, dict)
        symbol = from_union([from_str, from_none], obj.get("symbol"))
        market = from_union([from_str, from_none], obj.get("market"))
        name = from_union([from_str, from_none], obj.get("name"))
        net_value = from_union([from_float_string, from_none], obj.get("net_value"))
        daily_gain = from_union([from_float_string, from_none], obj.get("daily_gain"))
        monthly_gain = from_union([from_float_string, from_none], obj.get("monthly_gain"))
        total_gain = from_union([from_float_string, from_none], obj.get("total_gain"))
        annualized_gain = from_union([from_float_string, from_none], obj.get("annualized_gain"))
        closed_at = from_union([from_int_string, from_none_of_int], obj.get("closed_at"))
        # total_score = from_union([from_int, from_none], obj.get("total_score"))
        # report_updated_time = from_union([from_int, from_none], obj.get("report_updated_time"))
        return CubeItemWrapper(symbol, market, name, net_value, daily_gain, monthly_gain, total_gain, annualized_gain,
                               closed_at)

    def to_dict(self) -> dict:
        result: dict = {}
        result["symbol"] = from_union([from_str, from_none], self.symbol)
        result["market"] = from_union([from_str, from_none], self.market)
        result["name"] = from_union([from_str, from_none], self.name)
        result["net_value"] = from_union([to_float, from_none], self.net_value)
        result["daily_gain"] = from_union([to_float, from_none], self.daily_gain)
        result["monthly_gain"] = from_union([to_float, from_none], self.monthly_gain)
        result["total_gain"] = from_union([to_float, from_none], self.total_gain)
        result["annualized_gain"] = from_union([to_float, from_none], self.annualized_gain)
        result["closed_at"] = from_union([from_int, from_none], self.closed_at)
        result['total_score'] = from_union([from_float, from_none], self.total_score)
        result['report_updated_time'] = from_union([from_int, from_none], self.report_updated_time)
        return result


def cube_item_wrapper_from_dict(s: Any) -> List[CubeItemWrapper]:
    return from_list(CubeItemWrapper.from_dict, s)


def cube_item_wrapper_to_dict(x: List[CubeItemWrapper]) -> Any:
    return from_list(lambda x: to_class(CubeItemWrapper, x), x)
