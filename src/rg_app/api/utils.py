import msgspec

class BaseStruct(msgspec.Struct, rename="camel"):
    pass