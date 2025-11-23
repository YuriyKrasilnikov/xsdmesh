"""Test package version and basic imports."""

import xsdmesh


def test_version_exists() -> None:
    """Test that __version__ is defined."""
    assert hasattr(xsdmesh, "__version__")
    assert isinstance(xsdmesh.__version__, str)
    assert xsdmesh.__version__ == "0.1.0"


def test_package_imports() -> None:
    """Test that package can be imported."""
    import xsdmesh.graph
    import xsdmesh.loader
    import xsdmesh.parser
    import xsdmesh.types
    import xsdmesh.utils
    import xsdmesh.validators
    import xsdmesh.xpath
    import xsdmesh.xsd11

    # Ensure imports don't raise
    assert xsdmesh.parser is not None
    assert xsdmesh.loader is not None
    assert xsdmesh.types is not None
