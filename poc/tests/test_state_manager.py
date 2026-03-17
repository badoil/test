"""
Unit tests for State Manager.

Tests cover:
- Basic save/get/delete operations
- TTL (time-to-live) functionality
- Plan status retrieval
- Multiple backend support

Reference: POC_SPEC.md - Phase 0 Tasks
"""

import pytest
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from poc.state_manager import (
    MemoryStateManager,
    create_state_manager
)


class TestMemoryStateManager:
    """Test suite for Memory State Manager."""

    @pytest.fixture
    def state_manager(self):
        """Create fresh State Manager for each test."""
        sm = MemoryStateManager()
        yield sm
        # Cleanup not needed for Memory State Manager (in-memory)

    @pytest.mark.asyncio
    async def test_save_and_get_step_state(self, state_manager):
        """Test basic save and get operations."""
        # Save state
        state = {"count": 3, "items": ["a", "b", "c"]}
        result = await state_manager.save_step_state(
            "test-plan", "step-1", state
        )

        assert result is True, "Save operation should succeed"

        # Retrieve state
        retrieved = await state_manager.get_step_state("test-plan", "step-1")

        assert retrieved is not None, "Retrieved state should not be None"
        assert retrieved["count"] == 3, "Count should match"
        assert retrieved["items"] == ["a", "b", "c"], "Items should match"

    @pytest.mark.asyncio
    async def test_get_nonexistent_step(self, state_manager):
        """Test retrieving non-existent step."""
        retrieved = await state_manager.get_step_state(
            "test-plan", "nonexistent"
        )

        assert retrieved is None, "Non-existent step should return None"

    @pytest.mark.asyncio
    async def test_multiple_steps_in_plan(self, state_manager):
        """Test saving multiple steps for a plan."""
        # Save multiple steps
        await state_manager.save_step_state("test-plan", "step-1", {"count": 1})
        await state_manager.save_step_state("test-plan", "step-2", {"count": 2})
        await state_manager.save_step_state("test-plan", "step-3", {"count": 3})

        # Retrieve all steps
        status = await state_manager.get_plan_status("test-plan")

        assert status is not None, "Plan status should not be None"
        assert len(status) == 3, "Should have 3 steps"
        assert status["step-1"]["count"] == 1
        assert status["step-2"]["count"] == 2
        assert status["step-3"]["count"] == 3

    @pytest.mark.asyncio
    async def test_delete_plan_state(self, state_manager):
        """Test deleting all states for a plan."""
        # Save steps
        await state_manager.save_step_state("test-plan", "step-1", {"count": 1})
        await state_manager.save_step_state("test-plan", "step-2", {"count": 2})

        # Delete plan
        result = await state_manager.delete_plan_state("test-plan")

        assert result is True, "Delete should succeed"

        # Verify deletion
        status = await state_manager.get_plan_status("test-plan")

        assert status is None, "Plan status should be None after deletion"

    @pytest.mark.asyncio
    async def test_ttl_basic(self, state_manager):
        """Test basic TTL functionality."""
        # Save state with 1 second TTL
        await state_manager.save_step_state(
            "test-plan", "step-1", {"count": 1}, ttl_seconds=1
        )

        # Should exist immediately
        retrieved = await state_manager.get_step_state("test-plan", "step-1")
        assert retrieved is not None, "State should exist immediately"

        # Wait for expiry
        await asyncio.sleep(1.1)

        # Should be expired
        retrieved = await state_manager.get_step_state("test-plan", "step-1")
        assert retrieved is None, "State should be None after TTL expiry"

    @pytest.mark.asyncio
    async def test_ttl_different_expiries(self, state_manager):
        """Test multiple steps with different TTLs."""
        # Save steps with different TTLs
        await state_manager.save_step_state(
            "test-plan", "step-1", {"id": 1}, ttl_seconds=1
        )
        await state_manager.save_step_state(
            "test-plan", "step-2", {"id": 2}, ttl_seconds=3
        )

        # Both should exist initially
        status = await state_manager.get_plan_status("test-plan")
        assert len(status) == 2, "Both steps should exist initially"

        # Wait for step-1 to expire
        await asyncio.sleep(1.1)

        status = await state_manager.get_plan_status("test-plan")
        assert len(status) == 1, "Only step-2 should remain"
        assert "step-2" in status, "step-2 should still exist"

        # Wait for step-2 to expire
        await asyncio.sleep(2)

        status = await state_manager.get_plan_status("test-plan")
        assert status == {} or status is None, "All steps should be expired"

    @pytest.mark.asyncio
    async def test_no_ttl(self, state_manager):
        """Test that state without TTL persists indefinitely."""
        # Save state without TTL
        await state_manager.save_step_state("test-plan", "step-1", {"count": 1})

        # Wait a bit
        await asyncio.sleep(0.5)

        # Should still exist
        retrieved = await state_manager.get_step_state("test-plan", "step-1")
        assert retrieved is not None, "State without TTL should persist"

    @pytest.mark.asyncio
    async def test_update_existing_state(self, state_manager):
        """Test updating existing step state."""
        # Save initial state
        await state_manager.save_step_state(
            "test-plan", "step-1", {"count": 1}
        )

        # Update state
        await state_manager.save_step_state(
            "test-plan", "step-1", {"count": 2, "updated": True}
        )

        # Retrieve updated state
        retrieved = await state_manager.get_step_state("test-plan", "step-1")

        assert retrieved["count"] == 2, "Count should be updated"
        assert retrieved["updated"] is True, "Updated flag should be present"

    @pytest.mark.asyncio
    async def test_separate_plans(self, state_manager):
        """Test that separate plans don't interfere."""
        # Save steps for different plans
        await state_manager.save_step_state(
            "plan-1", "step-1", {"plan": 1}
        )
        await state_manager.save_step_state(
            "plan-2", "step-1", {"plan": 2}
        )

        # Retrieve separate plan states
        plan1_status = await state_manager.get_plan_status("plan-1")
        plan2_status = await state_manager.get_plan_status("plan-2")

        assert plan1_status is not None, "Plan 1 should exist"
        assert plan2_status is not None, "Plan 2 should exist"
        assert plan1_status["step-1"]["plan"] == 1
        assert plan2_status["step-1"]["plan"] == 2

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, state_manager):
        """Test cleanup of expired states."""
        # Save states with different TTLs
        await state_manager.save_step_state(
            "test-plan", "step-1", {"id": 1}, ttl_seconds=1
        )
        await state_manager.save_step_state(
            "test-plan", "step-2", {"id": 2}, ttl_seconds=3
        )

        # Wait for step-1 to expire
        await asyncio.sleep(1.1)

        # Cleanup expired
        await state_manager.cleanup_expired()

        # Verify only step-2 remains
        status = await state_manager.get_plan_status("test-plan")
        assert len(status) == 1, "Only step-2 should remain after cleanup"
        assert "step-2" in status, "step-2 should exist"


class TestStateManagerFactory:
    """Test suite for State Manager factory."""

    @pytest.mark.asyncio
    async def test_create_memory_backend(self):
        """Test creating Memory backend."""
        sm = create_state_manager("memory")

        assert isinstance(sm, MemoryStateManager), "Should create MemoryStateManager"

        # Test basic operation
        await sm.save_step_state("test", "s1", {"count": 1})
        retrieved = await sm.get_step_state("test", "s1")
        assert retrieved is not None

    @pytest.mark.asyncio
    async def test_create_invalid_backend(self):
        """Test creating invalid backend raises error."""
        with pytest.raises(ValueError, match="Invalid backend"):
            create_state_manager("invalid")


class TestRedisStateManager:
    """Test suite for Redis State Manager (integration tests)."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("TEST_REDIS"),
        reason="Redis tests require TEST_REDIS environment variable"
    )
    async def test_redis_backend(self):
        """Test Redis backend (integration test)."""
        import os

        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))

        sm = create_state_manager("redis", redis_host=redis_host, redis_port=redis_port)

        # Save and retrieve
        await sm.save_step_state("test-plan", "step-1", {"count": 1})
        retrieved = await sm.get_step_state("test-plan", "step-1")

        assert retrieved is not None, "Redis save/get should work"
        assert retrieved["count"] == 1, "Data should match"

        # Cleanup
        await sm.delete_plan_state("test-plan")


class TestFileStateManager:
    """Test suite for File State Manager."""

    @pytest.mark.asyncio
    async def test_file_backend_basic(self):
        """Test File backend basic operations."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            sm = create_state_manager("file", base_dir=tmpdir)

            # Save and retrieve
            await sm.save_step_state("test-plan", "step-1", {"count": 1})
            retrieved = await sm.get_step_state("test-plan", "step-1")

            assert retrieved is not None, "File save/get should work"
            assert retrieved["count"] == 1, "Data should match"

            # Cleanup
            await sm.delete_plan_state("test-plan")

    @pytest.mark.asyncio
    async def test_file_backend_ttl(self):
        """Test File backend TTL functionality."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            sm = create_state_manager("file", base_dir=tmpdir)

            # Save with 1 second TTL
            await sm.save_step_state(
                "test-plan", "step-1", {"count": 1}, ttl_seconds=1
            )

            # Should exist immediately
            retrieved = await sm.get_step_state("test-plan", "step-1")
            assert retrieved is not None, "State should exist immediately"

            # Wait for expiry
            await asyncio.sleep(1.1)

            # Should be expired
            retrieved = await sm.get_step_state("test-plan", "step-1")
            assert retrieved is None, "State should be None after TTL expiry"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
