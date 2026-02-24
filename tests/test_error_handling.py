#!/usr/bin/env python
"""Test script to verify error handling implementation."""

from testframework.models import LLMErrorType, TestErrorInfo, ChatbotResponse, ChatbotResponseEvaluation, \
    DetectionElement


def test_error_info_from_timeout():
    """Test creating LLMErrorInfo from timeout exception."""
    try:
        raise TimeoutError("Test timeout")
    except Exception as e:
        error = TestErrorInfo.from_exception(e)
        assert error.error_type == LLMErrorType.TIMEOUT
        print(f"TimeoutError -> {error.error_type.value}")


def test_error_info_from_connection():
    """Test creating LLMErrorInfo from connection exception."""
    try:
        raise ConnectionError("Connection refused")
    except Exception as e:
        error = TestErrorInfo.from_exception(e)
        assert error.error_type == LLMErrorType.CONNECTION_ERROR
        print(f"ConnectionError -> {error.error_type.value}")


def test_error_info_from_unknown():
    """Test creating LLMErrorInfo from unknown exception."""
    try:
        raise ValueError("Unknown error")
    except Exception as e:
        error = TestErrorInfo.from_exception(e)
        assert error.error_type == LLMErrorType.UNKNOWN
        print(f"ValueError -> {error.error_type.value}")


def test_chatbot_response_from_error():
    """Test creating ChatbotResponse from error."""
    error = TestErrorInfo(LLMErrorType.TIMEOUT, "API timeout after 120s")
    response = ChatbotResponse.from_error(error, "test system prompt")
    assert response.is_error
    assert response.error.error_type == LLMErrorType.TIMEOUT
    assert response.response == ""
    print(f"✓ ChatbotResponse.from_error works correctly")


def test_chatbot_response_eval_from_error():
    """Test creating ChatbotResponseEvaluation from error."""
    error = TestErrorInfo(LLMErrorType.RATE_LIMIT, "Rate limit exceeded")
    response = ChatbotResponse.from_error(error)
    eval_result = ChatbotResponseEvaluation.from_error(response)
    assert eval_result.is_error
    assert eval_result.score == -1.0
    print(f"ChatbotResponseEvaluation.from_error works correctly")


def test_detection_element_from_error():
    """Test creating DetectionElement from error."""
    error = TestErrorInfo(LLMErrorType.API_ERROR, "API error occurred")
    detection = DetectionElement.from_error(error)
    assert detection.is_error
    assert detection.success == False
    print(f"DetectionElement.from_error works correctly")


if __name__ == "__main__":
    print("Testing error handling implementation...\n")
    test_error_info_from_timeout()
    test_error_info_from_connection()
    test_error_info_from_unknown()
    test_chatbot_response_from_error()
    test_chatbot_response_eval_from_error()
    test_detection_element_from_error()
    print("\nAll tests passed!")
