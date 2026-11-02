import pytest
from app.core.condition_mapper import interpret

@pytest.mark.parametrize('code',[0,1,2,3,45,48,51,53,55,56,57,61,63,65,66,67,71,73,75,77,80,81,82,85,86,95,96,99])
def test_known_codes(code):
    assert interpret(code,True).category!='unknown'
    assert interpret(code,True).icon_id.endswith('d')
    assert interpret(code,False).icon_id.endswith('n')
    assert interpret(code).icon_id=='unknown'

@pytest.mark.parametrize('code',[None,999,-1,True,'0'])
def test_unknown(code):
    assert interpret(code,True).category=='unknown'
    assert interpret(code,True).icon_id=='unknown'
