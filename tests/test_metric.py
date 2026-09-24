import pytest

from vimarsha.metric import compute_oiwer


def test_accepts_orthographic_variant():
    reference = [["कम"], ["रेट"], ["पर", "पे"], ["मिल"], ["सकता"], ["है"]]

    result = compute_oiwer("कम रेट पे मिल सकता है", reference, "hindi")

    assert result.score == 0
    assert result.operations == ("c", "c", "c", "c", "c", "c")


def test_reports_standard_error_types():
    result = compute_oiwer("मैं आज घर", [["मैं"], ["कल"], ["घर"]], "hi")

    assert result.errors == 1
    assert result.reference_words == 3
    assert result.score == pytest.approx(100 / 3)


def test_accepts_multiword_variant():
    result = compute_oiwer("हाँ तो इस का मतलब", [["हाँ तो इसका मतलब", "हाँ तो इस का मतलब"]], "hi")

    assert result.score == 0
    assert result.reference_words == 5


def test_rejects_unknown_language():
    with pytest.raises(ValueError, match="Unsupported language"):
        compute_oiwer("hello", [["hello"]], "unknown")
