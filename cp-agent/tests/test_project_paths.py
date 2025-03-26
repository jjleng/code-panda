"""Tests for project_paths utility functions."""

import os
import tempfile
from pathlib import Path

import pytest

from cp_agent.utils.project_paths import find_project_paths


@pytest.mark.asyncio
async def test_non_existent_directory() -> None:
    """Test finding paths in a non-existent directory."""
    non_existent_path = Path("/non/existent/path")
    paths = await find_project_paths(non_existent_path)
    assert paths == ["/"]


@pytest.mark.asyncio
async def test_empty_directory() -> None:
    """Test finding paths in an empty directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        paths = await find_project_paths(Path(temp_dir))
        assert paths == ["/"]


@pytest.mark.asyncio
async def test_router_file_with_parameterized_routes() -> None:
    """Test finding paths in a directory with router file containing parameterized routes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        router_file_path = Path(temp_dir) / "router.js"

        # Create a router file with a mix of parameterized and non-parameterized routes
        with open(router_file_path, "w") as f:
            f.write(
                """
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/products" element={<Products />} />
            <Route path="/products/:id" element={<ProductDetail />} />
            <Route path="/users/*" element={<UserRoutes />} />
            <Route path="/blog" element={<Blog />} />
            <Route path="/blog/{slug}" element={<BlogPost />} />
            """
            )

        paths = await find_project_paths(Path(temp_dir))
        assert sorted(paths) == ["/", "/about", "/blog", "/products"]


@pytest.mark.asyncio
async def test_multiple_router_files() -> None:
    """Test finding paths with multiple router files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create App.js router file
        with open(temp_path / "App.js", "w") as f:
            f.write(
                """
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            """
            )

        # Create another router file in a subdirectory
        os.makedirs(temp_path / "src")
        with open(temp_path / "src" / "router.jsx", "w") as f:
            f.write(
                """
            <Route path="/contact" element={<Contact />} />
            <Route path="/services" element={<Services />} />
            <Route path="/services/:id" element={<ServiceDetail />} />
            """
            )

        paths = await find_project_paths(temp_path)
        assert sorted(paths) == ["/", "/about", "/contact", "/services"]


@pytest.mark.asyncio
async def test_path_formatting() -> None:
    """Test path formatting (adding leading slash, removing trailing slash)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        router_file_path = Path(temp_dir) / "router.js"

        # Create a router file with paths needing normalization
        with open(router_file_path, "w") as f:
            f.write(
                """
            <Route path="home" element={<Home />} />
            <Route path="about/" element={<About />} />
            <Route path="/contact/" element={<Contact />} />
            """
            )

        paths = await find_project_paths(Path(temp_dir))
        assert sorted(paths) == ["/", "/about", "/contact", "/home"]
