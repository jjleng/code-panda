"""
Module for handling project-related functionality.
"""

from .manager import BaseProjectManager, LocalProjectManager, get_project_manager

__all__ = ["BaseProjectManager", "LocalProjectManager", "get_project_manager"]
