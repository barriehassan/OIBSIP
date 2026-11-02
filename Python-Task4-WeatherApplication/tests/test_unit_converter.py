import pytest
from app.core.unit_converter import celsius_to_fahrenheit, fahrenheit_to_celsius
from app.core.exceptions import WeatherDataError

@pytest.mark.parametrize('c,f',[(0,32),(100,212),(-40,-40),(-12.345,9.779),(21.123456789,70.0222222202)])
def test_conversion(c,f):
    assert celsius_to_fahrenheit(c)==pytest.approx(f)
    assert fahrenheit_to_celsius(f)==pytest.approx(c)
    assert fahrenheit_to_celsius(celsius_to_fahrenheit(c))==pytest.approx(c,abs=1e-12)

@pytest.mark.parametrize('value',[None,True,'10',float('nan'),float('inf'),-float('inf'),10**1000])
@pytest.mark.parametrize('convert',[celsius_to_fahrenheit,fahrenheit_to_celsius])
def test_invalid(value,convert):
    with pytest.raises(WeatherDataError): convert(value)
