# -*- coding: utf-8 -*-
# @Time    : 2022/7/20 16:10
# @Author  : Tuffy
# @Description :
from typing import Dict, Tuple, Type

from construct import Computed, Construct, Rebuild, Struct
from pydantic.fields import FieldInfo
from pydantic.main import BaseModel, ModelMetaclass

__all__ = (
    "SignallingBaseModel",
)


class SignallingModelMetaclass(ModelMetaclass):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict, **kwargs):
        cls = super().__new__(mcs, name, bases, attrs, **kwargs)
        if name != "SignallingBaseModel":

            parent_subcons_ = {}
            for parent_ in bases:
                parent_subcons_ |= getattr(parent_, "_subcons_kwargs", {})

            subcons_kwargs_ = parent_subcons_ | mcs.query_construct_field(attrs)

            struct_type_ = attrs.get("_signalling_struct", getattr(cls, "_signalling_struct_type", Struct))
            setattr(cls, "_signalling_struct", struct_type_(**subcons_kwargs_))
            setattr(cls, "_signalling_struct_type", struct_type_)

            setattr(cls, "_subcons_kwargs", subcons_kwargs_)
        return cls

    @staticmethod
    def query_construct_field(attrs: Dict[str, FieldInfo]) -> Dict[str, Construct]:
        subcons_kwargs_ = {}
        for attr_name_, field_ in attrs.items():
            if isinstance(field_, FieldInfo) and "signalling_struct" in field_.extra:
                if "struct_padding" in field_.extra:
                    subcons_kwargs_[f"_{attr_name_}_padding"] = field_.extra["struct_padding"]
                if "compute_rebuild" in field_.extra:
                    subcons_kwargs_[f"_{attr_name_}"] = Rebuild(
                        field_.extra["signalling_struct"], field_.extra["compute_rebuild"].rebuild
                    )
                    subcons_kwargs_[attr_name_] = Computed(field_.extra["compute_rebuild"].computed)
                else:
                    subcons_kwargs_[attr_name_] = field_.extra["signalling_struct"]
        return subcons_kwargs_


class SignallingBaseModel(BaseModel, metaclass=SignallingModelMetaclass):
    _signalling_struct: Construct = Struct
    _signalling_struct_type: Construct = Struct

    @classmethod
    def signalling_parse(cls, data: bytes):
        dict_ = cls._signalling_struct.parse(data)
        return cls.parse_obj(dict_)

    @classmethod
    def signalling_build(cls, obj: Dict) -> bytes:
        return cls._signalling_struct.build(obj)

    def to_signalling(self) -> bytes:
        return self._signalling_struct.build(self)

    def get(self, name: str, default: object = None):
        if isinstance(name, str):
            return getattr(self, name, default)

    def __getitem__(self, key):
        return getattr(self, key)

    def __contains__(self, key):
        return hasattr(self, key)

    def __bytes__(self) -> bytes:
        return self._signalling_struct.build(self)
