'''Unit tests for gradeforge.utils'''

from datetime import date

import pytest

from gradeforge.utils import parse_semester, army_time, get_season, b_and_n_semester

def test_parse_semester():
    assert parse_semester('fall') == str(date.today().year) + '08'
    assert parse_semester('Summer') == str(date.today().year) + '05'
    assert parse_semester('sPrINg', 2015) == '201501'
    assert parse_semester('spring', 2013) == '201311'
    with pytest.raises(ValueError):
        parse_semester('winter')
    for error in ('spring', 1), ('Fall', -107), ('summer', 10000):
        with pytest.raises(ValueError, message=str(error)):
            parse_semester(*error)


def test_army_time():
    assert army_time('1:00 a.m') == '01:00'
    assert army_time('1:00 pm') == '13:00'
    assert army_time('11:59a.m.') == '11:59'
    assert army_time('12:00 p.m') == '12:00'
    assert army_time('12:00am') == '00:00'
    assert army_time('14:00') == '14:00'
    assert army_time('00:00') == '00:00'
    assert army_time('00:00\x01') == '00:00'
    assert army_time('10:00 a.\x01m.') == '10:00'


def test_get_season():
    assert get_season('201808') == 'Fall'
    assert get_season('201405') == 'Summer'
    assert get_season('201901') == 'Spring'
    with pytest.raises(ValueError):
        get_season('-2')
    with pytest.raises(ValueError):
        get_season('20')
    with pytest.raises(ValueError):
        get_season('2018808')
    with pytest.raises(ValueError):
        get_season('garbage')


def test_b_and_n_semester():
    assert b_and_n_semester('201808') == 'F18'
    assert b_and_n_semester('201801') == 'W18'
    assert b_and_n_semester('201805') == 'A18'
    assert b_and_n_semester(201505) == 'A15'
    with pytest.raises(ValueError):
        b_and_n_semester('201504')
    with pytest.raises(ValueError):
        b_and_n_semester('some garbage')
    with pytest.raises(ValueError):
        b_and_n_semester('-21505')
