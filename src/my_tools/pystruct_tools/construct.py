# -*- coding: utf-8 -*-
# @Time    : 2022/7/20 16:28
# @Author  : Tuffy
# @Description :

from io import BytesIO

from construct import Construct, Container, MappingError, SizeofError, UnionError, stream_seek, stream_tell

__all__ = (
    "PreSwitch",
    "PreSwitchFactory",
)


class PreSwitch(Construct):

    def __init__(self, tag_field: str, tag_struct, *subcons, **subconskw):
        super().__init__()
        self.tag_field = tag_field
        self.tag_struct = tag_struct
        self.subcons = list(subcons) + list(k / v for k, v in subconskw.items())
        self._subcons = Container((sc.name, sc) for sc in self.subcons if sc.name)

    def __getattr__(self, name):
        if name in self._subcons:
            return self._subcons[name]
        raise AttributeError

    def _parse(self, stream: BytesIO, context: Container, path: str):
        obj = Container()
        context = Container(
            _=context,
            _params=context._params,
            _root=None,
            _parsing=context._parsing,
            _building=context._building,
            _sizing=context._sizing,
            _subcons=self._subcons,
            _io=stream,
            _index=context.get("_index", None)
        )
        context._root = context._.get("_root", context)
        fallback = stream_tell(stream, path)
        tag_ = self.tag_struct._parse(stream, context, path)
        stream_seek(stream, fallback, 0, path)  # raises KeyError
        if isinstance(tag_, dict):
            tag_ = tag_[self.tag_field]

        if subcon_ := self._subcons.get(tag_):
            return subcon_._parse(stream, context, path)

        raise MappingError("Unknown tag in PreSwitch", path=f"{path} -> {self.tag_field}")

    def _build(self, obj, stream: BytesIO, context: Container, path: str):
        if self.tag_field not in obj:
            raise UnionError(f"Union cannot build, missing key: {self.tag_field}", path=f"{path} -> {self.tag_field}")

        context = Container(
            _=context,
            _params=context._params,
            _root=None,
            _parsing=context._parsing,
            _building=context._building,
            _sizing=context._sizing,
            _subcons=self._subcons,
            _io=stream,
            _index=context.get("_index", None)
        )
        context._root = context._.get("_root", context)
        context.update(obj)

        if subcon_ := self._subcons.get(obj[self.tag_field]):
            return subcon_._build(obj, stream, context, path)
        else:
            raise UnionError("cannot build, none of subcons were found in the dictionary %r" % (obj,), path=f"{path} -> {self.tag_field}")

    def _sizeof(self, context, path):
        raise SizeofError("Union builds depending on actual object dict, size is unknown", path=path)


def PreSwitchFactory(tag_field: str, tag_struct):
    def decorator_(*subcons, **subconskw):
        return PreSwitch(tag_field, tag_struct, *subcons, **subconskw)

    return decorator_
