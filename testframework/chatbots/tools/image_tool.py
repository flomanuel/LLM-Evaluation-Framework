"""Dummy image generation tool."""
#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from langchain_core.tools import tool


@tool
def generate_image(image_description: str) -> str:
    """Generate an image based on the provided description.

    This is a dummy tool that returns the description unchanged.

    Args:
        image_description: A description of the image to generate.

    Returns:
        The image description, unchanged.
    """
    return image_description
