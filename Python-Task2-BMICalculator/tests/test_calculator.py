import math
from dataclasses import FrozenInstanceError
import pytest
from app.core.calculator import calculate_bmi, create_result, format_bmi
from app.core.classification import BMICategory
from app.core.models import BMIResult
from app.core.validator import ValidationError
from app.core.conversions import (pounds_to_kilograms, inches_to_metres,
    centimetres_to_metres, feet_inches_to_metres)

def test_reference():
    assert calculate_bmi(70, 1.75) == pytest.approx(22.857142857142858)
    assert format_bmi(calculate_bmi(50, 1.60)) == "19.53"

def test_equivalent_units():
    metric = calculate_bmi(70, 1.75)
    imperial = calculate_bmi(pounds_to_kilograms(70 / 0.45359237), inches_to_metres(1.75 / 0.0254))
    assert imperial == pytest.approx(metric)
    assert centimetres_to_metres(175) == pytest.approx(1.75)
    assert feet_inches_to_metres(5, 9) == pytest.approx(1.7526)
    assert feet_inches_to_metres(0, 6) == pytest.approx(0.1524)
    assert feet_inches_to_metres(6) == pytest.approx(1.8288)

@pytest.mark.parametrize("bad", [0, -1, math.nan, math.inf, -math.inf, True, None, [], {}, "70", 10**1000])
@pytest.mark.parametrize("field", ["weight", "height"])
def test_invalid_measurements(bad, field):
    with pytest.raises(ValidationError):
        calculate_bmi(bad if field == "weight" else 70, bad if field == "height" else 1.75)

@pytest.mark.parametrize("weight,height", [(1e308, 1e-308), (1e-308, 1e308)])
def test_unrepresentable_results(weight, height):
    with pytest.raises(ValidationError):
        calculate_bmi(weight, height)

def test_result():
    result = create_result("70", "1.75")
    assert (result.weight_kg, result.height_m) == (70, 1.75)
    assert result.bmi_value == calculate_bmi(70, 1.75)
    assert result.bmi_value != float(result.formatted_bmi)
    assert result.formatted_bmi == "22.86"
    assert result.category is BMICategory.NORMAL
    with pytest.raises(FrozenInstanceError):
        result.weight_kg = 80

def test_original_value_classification():
    result = BMIResult(24.9999 * 4, 2)
    assert result.formatted_bmi == "25.00"
    assert result.category is BMICategory.NORMAL

@pytest.mark.parametrize("converter", [pounds_to_kilograms, inches_to_metres, centimetres_to_metres])
@pytest.mark.parametrize("bad", [0, -1, math.nan, math.inf, True, "12", None, 10**1000])
def test_invalid_conversions(converter, bad):
    with pytest.raises(ValidationError):
        converter(bad)

@pytest.mark.parametrize("feet,inches", [(-1, 0), (1.5, 0), (True, 0), (0, 0), (5, 12), (5, -1), (5, math.nan), (5, math.inf), (5, True), (5, "1"), (10**1000, 0)])
def test_invalid_feet_inches(feet, inches):
    with pytest.raises(ValidationError):
        feet_inches_to_metres(feet, inches)
