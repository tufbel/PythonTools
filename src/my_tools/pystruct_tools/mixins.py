# -*- coding: utf-8 -*-
# @Time    : 2022/7/20 16:09
# @Author  : Tuffy
# @Description : 
from collections import namedtuple
from copy import deepcopy
from typing import Any, Dict, List, Union

from construct import Construct

__all__ = (
    "FormatTuple",
    "InnerDictMixin",
    "SubStructMixin",
)

# 用于标明字段是否为inner字段（需要根据上级字段生成）的元组
# is_inner: bool，标记字段是否为inner字段
# _inner_format: Union[None, List, Dict]
#    None:表示什么都不处理，若List与Dict判断为空一样也不处理
#    List:描述inner字段包含哪些上级字段，并且停止往更深处进行inner_format
#    Dict:其key描述inner字段包含哪些上级字段，并且根据value继续进行inner_format， 所以value必须也为format_tuple
FormatTuple = namedtuple("FormatTuple", ["is_inner", "inner_format"], defaults=(False, None))


class InnerDictMixin:
    _inner_format: Dict[Any, FormatTuple] = None  # Ditc 每一层的key在inner_to_dict时使用，value用于把指定的key转到inner中，在dict_to_inner时使用

    @classmethod
    def dict_to_inner(cls, origin: Union[Dict], inner_format: Dict[Any, FormatTuple] = None, is_copy: bool = True) -> Dict:
        if not isinstance(inner_format, dict):
            return origin
        if is_copy:
            origin = deepcopy(origin)
        for key_, value_ in inner_format.items():
            if not isinstance(value_, FormatTuple) or not value_.inner_format:
                continue

            if key_ == "__all__":
                [cls.dict_to_inner(list_item_, value_.inner_format, False) for list_item_ in origin]
                return origin

            if value_.is_inner:
                if isinstance(value_.inner_format, dict):
                    [cls.dict_to_inner(origin, {k_: v_}, is_copy=False) for k_, v_ in value_.inner_format.items() if
                     isinstance(v_, FormatTuple) and v_.inner_format]
                    inner_dict_ = {inner_key_: origin.pop(inner_key_) for inner_key_ in value_.inner_format.keys() if inner_key_ in origin}
                else:
                    inner_dict_ = {inner_key_: origin.pop(inner_key_) for inner_key_ in value_.inner_format if inner_key_ in origin}

                if inner_dict_:
                    origin[key_] = inner_dict_

            elif isinstance(value_.inner_format, dict):
                cls.dict_to_inner(origin[key_], value_.inner_format, is_copy=False)

        return origin

    @classmethod
    def inner_to_dict(cls, inner: Union[Dict, List], inner_format: Dict[Any, FormatTuple] = None, is_copy: bool = True) -> Dict:
        if not isinstance(inner_format, dict):
            return inner
        if is_copy:
            inner = deepcopy(inner)

        for key_, value_ in inner_format.items():
            if not isinstance(value_, FormatTuple) or not value_.inner_format:
                continue

            if key_ == "__all__":
                [cls.inner_to_dict(list_item_, value_.inner_format, False) for list_item_ in inner]
                return inner
            elif key_ in inner:
                if isinstance(value_.inner_format, dict):
                    cls.inner_to_dict(inner[key_], value_.inner_format, False)
                if value_.is_inner:
                    inner.update(inner.pop(key_, {}))

        return inner


class SubStructMixin:
    _sub_structs: List[Dict] = None

    @classmethod
    def sub_struct_build(cls, origin: Dict, sub_struct: Dict):
        for key_, value_ in sub_struct.items():
            if key_ == "__all__":
                [cls.sub_struct_build(list_item_, value_) for list_item_ in origin]
                return
            if isinstance(value_, Construct):
                origin[key_] = value_.build(origin[key_])
            elif isinstance(value_, Dict) and value_:
                cls.sub_struct_build(origin[key_], value_)

    @classmethod
    def sub_struct_parse(cls, origin: Dict, sub_struct: Dict):
        for key_, value_ in sub_struct.items():
            if key_ == "__all__":
                [cls.sub_struct_parse(list_item_, value_) for list_item_ in origin]
                return
            if isinstance(value_, Construct):
                origin[key_] = value_.parse(origin[key_])
            elif isinstance(value_, Dict) and value_:
                cls.sub_struct_parse(origin[key_], value_)
