import math
import pytest
from app.core.validator import validate_weight, validate_height, ValidationError

@pytest.mark.parametrize("validator", [validate_weight, validate_height])
@pytest.mark.parametrize("bad", ["", "  ", "abc", -1, 0, "0", "-2", math.nan, math.inf, -math.inf, "NaN", "inf", "-Infinity", None, True, False, [], {}, complex(1,2), 10**1000])
def test_invalid_input(validator,bad):
    with pytest.raises(ValidationError):
        validator(bad)

@pytest.mark.parametrize("validator,value,expected", [(validate_weight,"70.5",70.5),(validate_weight," 70 ",70),(validate_height,"1.75",1.75),(validate_height,1.6,1.6),(validate_weight,1,1),(validate_weight,500,500),(validate_height,0.3,0.3),(validate_height,2.75,2.75)])
def test_valid(validator,value,expected):
    assert validator(value) == expected

@pytest.mark.parametrize("validator,value", [(validate_weight,0.99),(validate_weight,500.01),(validate_height,0.29),(validate_height,2.76)])
def test_support_limits(validator,value):
    with pytest.raises(ValidationError,match="application-supported range"):
        validator(value)

@pytest.mark.parametrize("validator,value,message", [(validate_weight,"","Please enter your weight."),(validate_weight,"abc","Weight must be a valid number."),(validate_height,0,"Height must be greater than zero."),(validate_height,"","Please enter your height.")])
def test_messages(validator,value,message):
    with pytest.raises(ValidationError) as error:
        validator(value)
    assert str(error.value) == message
