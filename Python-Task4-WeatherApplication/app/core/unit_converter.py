"""Conversions retain precision; formatting belongs to presentation."""
from .validator import number


def celsius_to_fahrenheit(value):
    return number(number(value, "temperature") * 9 / 5 + 32, "converted temperature")


def fahrenheit_to_celsius(value):
    return number((number(value, "temperature") - 32) * 5 / 9, "converted temperature")
