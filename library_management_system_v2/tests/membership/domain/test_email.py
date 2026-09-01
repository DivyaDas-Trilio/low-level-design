from dataclasses import FrozenInstanceError

import pytest

from membership.domain.email import EmailAddress
from membership.domain.exceptions import InvalidEmailError


# ---------- valid: normalization ----------
def test_valid_email_is_normalized():
    e = EmailAddress("  Alice@Example.COM ")
    assert e.value == "alice@example.com"            # stripped + lowercased


def test_plain_valid_email():
    assert EmailAddress("divya.das@trilio.io").value == "divya.das@trilio.io"


# ---------- invalid: rejected at construction ----------
@pytest.mark.parametrize("bad", [
    "divya.das@",          # no domain
    "@trilio.io",          # no local part
    "not-an-email",        # no @
    "alice.example.com",   # missing @
    "a@b",                 # domain has no dot
    "a @b.cc",             # contains a space
    "",                    # empty
])
def test_invalid_email_raises(bad):
    with pytest.raises(InvalidEmailError):
        EmailAddress(bad)


# ---------- value-object semantics ----------
def test_equal_by_value_after_normalization():
    assert EmailAddress("a@b.cc") == EmailAddress("A@B.CC")   # normalized -> equal


def test_is_immutable():
    e = EmailAddress("a@b.cc")
    with pytest.raises(FrozenInstanceError):                  # frozen dataclass
        e.value = "x@y.cc"


def test_is_hashable_and_dedupes_equal_values():
    s = {EmailAddress("a@b.cc"), EmailAddress("A@B.CC")}
    assert s == {EmailAddress("a@b.cc")}                      # equal values collapse in a set


def test_str_returns_normalized_value():
    assert str(EmailAddress("A@B.CC")) == "a@b.cc"
