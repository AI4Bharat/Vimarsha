from vimarsha.io import parse_lattice
from vimarsha.lattice import build_lattice, format_lattice


def test_builds_candidate_variants():
    lattice = build_lattice(
        [
            "कम रेट पर मिल सकता है",
            "कम रेट पे मिल सकता है",
            "कम रेट पे मिल सकता है।",
        ],
        "hindi",
    )

    assert ["पर", "पे"] in lattice
    assert lattice[0] == ["कम"]
    assert format_lattice(lattice).startswith("{कम} {रेट}")


def test_parses_serialized_lattice():
    assert parse_lattice("{कम} {पर | पे}") == [["कम"], ["पर", "पे"]]
