import math
import pytest
from app.core.classification import BMICategory as C, classify_bmi, CATEGORY_METADATA
from app.core.validator import ValidationError

@pytest.mark.parametrize("value,expected", [(18.49,C.UNDERWEIGHT),(18.5,C.NORMAL),(24.99,C.NORMAL),(25,C.OVERWEIGHT),(29.99,C.OVERWEIGHT),(30,C.OBESE)])
def test_required_boundaries(value,expected):
    assert classify_bmi(value) is expected

@pytest.mark.parametrize("boundary,below,at", [(18.5,C.UNDERWEIGHT,C.NORMAL),(25,C.NORMAL,C.OVERWEIGHT),(30,C.OVERWEIGHT,C.OBESE)])
def test_adjacent_floats(boundary,below,at):
    assert classify_bmi(math.nextafter(boundary,-math.inf)) is below
    assert classify_bmi(boundary) is at
    assert classify_bmi(math.nextafter(boundary,math.inf)) is at

@pytest.mark.parametrize("bad", [0,-1,math.nan,math.inf,-math.inf,True,"25",None,[],10**1000])
def test_invalid_bmi(bad):
    with pytest.raises(ValidationError):
        classify_bmi(bad)

def test_metadata():
    assert set(CATEGORY_METADATA) == set(C)
    for category, metadata in CATEGORY_METADATA.items():
        assert metadata.name == category.value
        assert metadata.colour.startswith("#")
        assert metadata.explanation
    with pytest.raises(TypeError):
        CATEGORY_METADATA[C.NORMAL] = None
