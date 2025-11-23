"""Test package version and basic imports."""

import xsdmesh


def test_version_exists() -> None:
    """Test that __version__ is defined."""
    assert hasattr(xsdmesh, "__version__")
    assert isinstance(xsdmesh.__version__, str)
    assert xsdmesh.__version__ == "0.1.0"


def test_package_imports() -> None:
    """Test that package can be imported."""
    import xsdmesh.parser
    import xsdmesh.loader
    import xsdmesh.types
    import xsdmesh.xsd11
    import xsdmesh.xpath
    import xsdmesh.graph
    import xsdmesh.validators
    import xsdmesh.utils

    # Ensure imports don't raise
    assert xsdmesh.parser is not None
    assert xsdmesh.loader is not None
    assert xsdmesh.types is not None
