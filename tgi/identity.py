"""Static identity over Unicode scalar values; no normalization or segmentation.

This TGI registry is distinct from the VEYRA 10240-slot registry.
IDs 0..15 are reserved and cannot be decoded as characters.
"""
REGISTRY_ID = "TGI-NMU-UNICODE-SCALAR-OFFSET16-RAW-V1"
OFFSET = 16


def validate_identity(identity: int) -> None:
    if type(identity) is not int:
        raise TypeError("Identity must be an integer, not bool or float")
    cp = identity - OFFSET
    if not 0 <= cp <= 0x10FFFF or 0xD800 <= cp <= 0xDFFF:
        raise ValueError("Identity is reserved or outside the declared scalar domain")


def encode(text: str) -> tuple[int, ...]:
    if not isinstance(text, str):
        raise TypeError("Input must be text")
    result = tuple(ord(char) + OFFSET for char in text)
    for identity in result:
        validate_identity(identity)
    return result


def decode(identities) -> str:
    result = []
    for identity in identities:
        validate_identity(identity)
        result.append(chr(identity - OFFSET))
    return "".join(result)
