import re


NUMBER_REGEX = re.compile(
    r"(\d{1,3}(?:[ ,.\u00A0]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)",
    re.VERBOSE,
)
