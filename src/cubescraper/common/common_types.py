from typing import Mapping, Sequence, Union

JSON = Union[
    None,
    bool,
    int,
    float,
    str,
    Sequence["JSON"],
    Mapping[str, "JSON"],
]
