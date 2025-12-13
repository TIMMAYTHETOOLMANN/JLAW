"""
Tests for Hash Service with BLAKE2b Support
"""

import pytest
from src.core.evidence_chain.hash_service import HashService, HashResult


def test_compute_hash():
    """Test computing hash from bytes."""
    data = b"test data"
    result = HashService.compute_hash(data)
    
    assert isinstance(result, HashResult)
    assert result.sha256 is not None
    assert result.sha3_512 is not None
    assert result.blake2b is not None
    assert result.input_size == len(data)


def test_compute_hash_from_string():
    """Test computing hash from string."""
    text = "test string"
    result = HashService.compute_hash_from_string(text)
    
    assert isinstance(result, HashResult)
    assert result.sha256 is not None
    assert result.blake2b is not None


def test_hash_determinism():
    """Test that same input produces same hash."""
    data = b"test data"
    
    result1 = HashService.compute_hash(data)
    result2 = HashService.compute_hash(data)
    
    assert result1.sha256 == result2.sha256
    assert result1.sha3_512 == result2.sha3_512
    assert result1.blake2b == result2.blake2b


def test_hash_uniqueness():
    """Test that different inputs produce different hashes."""
    result1 = HashService.compute_hash(b"data1")
    result2 = HashService.compute_hash(b"data2")
    
    assert result1.sha256 != result2.sha256
    assert result1.sha3_512 != result2.sha3_512
    assert result1.blake2b != result2.blake2b


def test_hash_result_to_dict():
    """Test HashResult to_dict method."""
    result = HashService.compute_hash(b"test")
    result_dict = result.to_dict()
    
    assert "sha256" in result_dict
    assert "sha3_512" in result_dict
    assert "blake2b" in result_dict
    assert "input_size" in result_dict
    assert "computed_at" in result_dict


def test_hash_result_verify():
    """Test HashResult verification."""
    data = b"test data"
    
    result1 = HashService.compute_hash(data)
    result2 = HashService.compute_hash(data)
    
    assert result1.verify(result2)


def test_verify_integrity():
    """Test data integrity verification."""
    data = b"test data"
    expected_hash = HashService.compute_hash(data)
    
    # Should verify successfully
    assert HashService.verify_integrity(data, expected_hash)
    
    # Should fail with different data
    assert not HashService.verify_integrity(b"different data", expected_hash)


def test_compute_hash_from_dict():
    """Test computing hash from dictionary."""
    data_dict = {
        "key1": "value1",
        "key2": 123,
        "key3": ["a", "b", "c"]
    }
    
    result = HashService.compute_hash_from_dict(data_dict)
    
    assert isinstance(result, HashResult)
    assert result.sha256 is not None


def test_dict_hash_determinism():
    """Test that same dict produces same hash (with key sorting)."""
    dict1 = {"b": 2, "a": 1, "c": 3}
    dict2 = {"a": 1, "c": 3, "b": 2}  # Different order
    
    result1 = HashService.compute_hash_from_dict(dict1)
    result2 = HashService.compute_hash_from_dict(dict2)
    
    # Should be the same due to key sorting
    assert result1.sha256 == result2.sha256
    assert result1.blake2b == result2.blake2b


def test_create_chain_link():
    """Test creating hash chain link."""
    data = b"current data"
    previous_hash = "previous_hash_value"
    
    link = HashService.create_chain_link(data, previous_hash)
    
    assert "current_hash" in link
    assert "previous_hash" in link
    assert link["previous_hash"] == previous_hash
    assert "timestamp" in link


def test_create_genesis_link():
    """Test creating genesis (first) chain link."""
    data = b"genesis data"
    
    link = HashService.create_chain_link(data, None)
    
    assert link["previous_hash"] is None
    assert "current_hash" in link
