import typing as ty

import msgspec

SubjectLike = str | list[str]
TextPayload = bytes | str
CommonJsonable = dict[str, ty.Any] | list[ty.Any] | msgspec.Struct

TStruct = ty.TypeVar("TStruct", bound=msgspec.Struct)

TStructOrList = ty.TypeVar("TStructOrList", bound=msgspec.Struct | list[msgspec.Struct])

