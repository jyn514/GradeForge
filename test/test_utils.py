from datetime import date
from sys import path

import pytest

try:
    path.append('.')
    from src.utils import *
except ImportError:
    path.append('..')
    from src.utils import *
path = path[:-1]


def test_constants():
    assert len(DAYS) == 7
    assert len(set(DAYS)) == 7


def test_parse_semester():
    assert parse_semester('fall') == str(date.today().year) + '08'
    assert parse_semester('Summer') == str(date.today().year) + '05'
    assert parse_semester('sPrINg', 2015) == '201501'
    with pytest.raises(ValueError):
        parse_semester('winter')
    for e in ('spring', 1), ('Fall', -107), ('summer', 10000):
        with pytest.raises(ValueError, message=str(e)):
            parse_semester(*e)


def test_ReturnSame():
    assert ReturnSame(0)[0] == 0
    assert ReturnSame(1)[10] == 1
    assert ReturnSame(2)['Hi there!'] == 2
    assert ReturnSame(3, 5, 12)[None] == (3, 5, 12)
    assert ReturnSame([None, 'pi', 3.2])[date] == [None, 'pi', 3.2]
    l = lambda f: f.strip()  # python compares lambdas by memory address
    assert ReturnSame(l)[lambda y: y**2] == l


def test_army_time():
    assert army_time('1:00 a.m') == '1:00'
    assert army_time('1:00 pm') == '13:00'
    assert army_time('11:59a.m.') == '11:59'
    assert army_time('12:00 p.m') == '12:00'
    assert army_time('12:00am') == '0:00'
    assert army_time('14:00') == '14:00'
    with pytest.raises(ValueError):
        army_time('65:00 am')
    with pytest.raises(ValueError):
        army_time('-51:00 p.m')


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
