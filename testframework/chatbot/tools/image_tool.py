"""Dummy image generation tool."""
from langchain_core.tools import tool


@tool
def generate_image(image_description: str) -> str:
    """Generate an image based on the provided description.

    This is a dummy tool that returns the description unchanged.
    In a real implementation, this would call an image generation API.

    Args:
        image_description: A detailed description of the image to generate.

    Returns:
        The image description, unchanged.
    """
    return image_description
