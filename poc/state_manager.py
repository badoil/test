"""
State Manager Implementation for Hybrid Graph + DAG Runtime.

Supports multiple backends: Memory (PoC), Redis (Production), File (Development).

Reference: POC_SPEC.md - State Manager Interface
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone


class StateManager(ABC):
    """
    Abstract base class for State Manager.
    Defines the interface for state persistence and recovery.
    """

    @abstractmethod
    async def save_step_state(
        self,
        plan_id: str,
        step_id: str,
        state: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Save step state for recovery.

        Args:
            plan_id: Unique plan identifier
            step_id: Unique step identifier within plan
            state: Step state to persist
            ttl_seconds: Time-to-live in seconds (optional)

        Returns:
            bool: True if saved successfully, False otherwise
        """
        pass

    @abstractmethod
    async def get_step_state(
        self,
        plan_id: str,
        step_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve step state for recovery.

        Args:
            plan_id: Unique plan identifier
            step_id: Unique step identifier within plan

        Returns:
            Optional[Dict]: Step state if exists, None otherwise
        """
        pass

    @abstractmethod
    async def delete_plan_state(
        self,
        plan_id: str
    ) -> bool:
        """
        Delete all states for a plan (cleanup).

        Args:
            plan_id: Unique plan identifier

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    async def get_plan_status(
        self,
        plan_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get overall plan status (all step states).

        Args:
            plan_id: Unique plan identifier

        Returns:
            Optional[Dict]: Plan status with step states, None if not found
        """
        pass


class MemoryStateManager(StateManager):
    """
    In-memory State Manager implementation.

    Good for:
    - PoC development
    - Testing
    - Local single-process deployments

    Limitations:
    - No persistence across restarts
    - No distributed support
    """

    def __init__(self):
        """
        Initialize in-memory state storage.

        Structure:
        {
            "plan_id": {
                "step_id": {
                    "state": {...},
                    "ttl": datetime,
                    "updated_at": datetime
                }
            }
        }
        """
        self._storage: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def save_step_state(
        self,
        plan_id: str,
        step_id: str,
        state: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Save step state to memory.

        Args:
            plan_id: Unique plan identifier
            step_id: Unique step identifier within plan
            state: Step state to persist
            ttl_seconds: Time-to-live in seconds (optional)

        Returns:
            bool: True if saved successfully
        """
        async with self._lock:
            # Ensure plan exists
            if plan_id not in self._storage:
                self._storage[plan_id] = {}

            # Calculate expiry time if TTL is set
            ttl = None
            if ttl_seconds is not None:
                ttl = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

            # Save step state
            self._storage[plan_id][step_id] = {
                "state": state,
                "ttl": ttl,
                "updated_at": datetime.now(timezone.utc)
            }

            return True

    async def get_step_state(
        self,
        plan_id: str,
        step_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve step state from memory.

        Args:
            plan_id: Unique plan identifier
            step_id: Unique step identifier within plan

        Returns:
            Optional[Dict]: Step state if exists and not expired
        """
        async with self._lock:
            # Check if plan exists
            if plan_id not in self._storage:
                return None

            # Check if step exists
            if step_id not in self._storage[plan_id]:
                return None

            step_data = self._storage[plan_id][step_id]

            # Check if expired
            if step_data["ttl"] is not None:
                if datetime.now(timezone.utc) > step_data["ttl"]:
                    # Expired, delete it
                    del self._storage[plan_id][step_id]
                    return None

            return step_data["state"]

    async def delete_plan_state(
        self,
        plan_id: str
    ) -> bool:
        """
        Delete all states for a plan from memory.

        Args:
            plan_id: Unique plan identifier

        Returns:
            bool: True if deleted successfully
        """
        async with self._lock:
            if plan_id in self._storage:
                del self._storage[plan_id]
                return True
            return False

    async def get_plan_status(
        self,
        plan_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get overall plan status from memory.

        Args:
            plan_id: Unique plan identifier

        Returns:
            Optional[Dict]: Plan status with all step states
        """
        async with self._lock:
            if plan_id not in self._storage:
                return None

            # Filter expired steps
            plan_data = {}
            for step_id, step_data in self._storage[plan_id].items():
                if step_data["ttl"] is None or datetime.now(timezone.utc) <= step_data["ttl"]:
                    plan_data[step_id] = step_data["state"]

            return plan_data

    async def cleanup_expired(self):
        """
        Cleanup all expired states (maintenance).

        This should be called periodically to free memory.
        """
        async with self._lock:
            now = datetime.now(timezone.utc)

            for plan_id in list(self._storage.keys()):
                for step_id in list(self._storage[plan_id].keys()):
                    step_data = self._storage[plan_id][step_id]

                    # Check if expired
                    if step_data["ttl"] is not None and now > step_data["ttl"]:
                        del self._storage[plan_id][step_id]

                # Cleanup empty plans
                if len(self._storage[plan_id]) == 0:
                    del self._storage[plan_id]


class RedisStateManager(StateManager):
    """
    Redis-based State Manager implementation.

    Good for:
    - Production deployments
    - Distributed systems
    - Horizontal scaling

    Features:
    - Distributed state storage
    - TTL support (native)
    - Persistence across restarts

    Note: Requires redis-py package
    """

    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        """
        Initialize Redis State Manager.

        Args:
            redis_host: Redis server host
            redis_port: Redis server port
        """
        try:
            import redis.asyncio as aioredis
        except ImportError:
            raise ImportError("redis-py package required. Install with: pip install redis")

        self._redis = aioredis.from_url(
            f"redis://{redis_host}:{redis_port}",
            encoding="utf-8",
            decode_responses=True
        )

    async def _get_key(self, plan_id: str, step_id: str) -> str:
        """Generate Redis key for step state."""
        return f"state:{plan_id}:{step_id}"

    async def _get_plan_key(self, plan_id: str) -> str:
        """Generate Redis key for plan status."""
        return f"plan:{plan_id}"

    async def save_step_state(
        self,
        plan_id: str,
        step_id: str,
        state: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Save step state to Redis.

        Args:
            plan_id: Unique plan identifier
            step_id: Unique step identifier within plan
            state: Step state to persist
            ttl_seconds: Time-to-live in seconds (optional)

        Returns:
            bool: True if saved successfully
        """
        try:
            import json

            key = await self._get_key(plan_id, step_id)
            value = json.dumps(state)

            if ttl_seconds:
                await self._redis.setex(key, ttl_seconds, value)
            else:
                await self._redis.set(key, value)

            return True
        except Exception as e:
            # Log error in production
            print(f"[RedisStateManager] Error saving state: {e}")
            return False

    async def get_step_state(
        self,
        plan_id: str,
        step_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve step state from Redis.

        Args:
            plan_id: Unique plan identifier
            step_id: Unique step identifier within plan

        Returns:
            Optional[Dict]: Step state if exists
        """
        try:
            import json

            key = await self._get_key(plan_id, step_id)
            value = await self._redis.get(key)

            if value is None:
                return None

            return json.loads(value)
        except Exception as e:
            print(f"[RedisStateManager] Error getting state: {e}")
            return None

    async def delete_plan_state(
        self,
        plan_id: str
    ) -> bool:
        """
        Delete all states for a plan from Redis.

        Args:
            plan_id: Unique plan identifier

        Returns:
            bool: True if deleted successfully
        """
        try:
            # Delete all keys matching pattern
            pattern = f"state:{plan_id}:*"
            keys = await self._redis.keys(pattern)

            if keys:
                await self._redis.delete(*keys)

            return True
        except Exception as e:
            print(f"[RedisStateManager] Error deleting state: {e}")
            return False

    async def get_plan_status(
        self,
        plan_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get overall plan status from Redis.

        Args:
            plan_id: Unique plan identifier

        Returns:
            Optional[Dict]: Plan status with all step states
        """
        try:
            pattern = f"state:{plan_id}:*"
            keys = await self._redis.keys(pattern)

            if not keys:
                return None

            # Extract step_ids from keys
            step_states = {}
            for key in keys:
                # key format: state:{plan_id}:{step_id}
                parts = key.split(":")
                if len(parts) >= 3:
                    step_id = parts[2]
                    value = await self._redis.get(key)
                    if value:
                        import json
                        step_states[step_id] = json.loads(value)

            return step_states
        except Exception as e:
            print(f"[RedisStateManager] Error getting plan status: {e}")
            return None


class FileStateManager(StateManager):
    """
    File-based State Manager implementation.

    Good for:
    - Development and debugging
    - Simple deployments
    - No external dependencies

    Limitations:
    - Slower than Memory/Redis
    - File system dependencies
    """

    def __init__(self, base_dir: str = "./state"):
        """
        Initialize File State Manager.

        Args:
            base_dir: Directory to store state files
        """
        import os
        import json

        self.base_dir = base_dir
        self._lock = asyncio.Lock()

        # Create base directory if not exists
        os.makedirs(base_dir, exist_ok=True)

    def _get_file_path(self, plan_id: str, step_id: str) -> str:
        """Generate file path for step state."""
        import os
        return os.path.join(self.base_dir, f"{plan_id}_{step_id}.json")

    def _get_plan_dir(self, plan_id: str) -> str:
        """Generate directory path for plan."""
        import os
        return os.path.join(self.base_dir, plan_id)

    async def save_step_state(
        self,
        plan_id: str,
        step_id: str,
        state: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Save step state to file.

        Args:
            plan_id: Unique plan identifier
            step_id: Unique step identifier within plan
            state: Step state to persist
            ttl_seconds: Time-to-live in seconds (optional)

        Returns:
            bool: True if saved successfully
        """
        try:
            import json
            from datetime import datetime, timedelta

            async with self._lock:
                file_path = self._get_file_path(plan_id, step_id)

                # Add metadata
                data = {
                    "state": state,
                    "ttl": ttl_seconds,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }

                if ttl_seconds:
                    data["expires_at"] = (
                        datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
                    ).isoformat()

                # Write to file
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2)

                return True
        except Exception as e:
            print(f"[FileStateManager] Error saving state: {e}")
            return False

    async def get_step_state(
        self,
        plan_id: str,
        step_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve step state from file.

        Args:
            plan_id: Unique plan identifier
            step_id: Unique step identifier within plan

        Returns:
            Optional[Dict]: Step state if exists and not expired
        """
        try:
            import json
            from datetime import datetime

            file_path = self._get_file_path(plan_id, step_id)

            async with self._lock:
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                except FileNotFoundError:
                    return None

                # Check if expired
                if "expires_at" in data:
                    expires_at = datetime.fromisoformat(data["expires_at"])
                    if datetime.now(timezone.utc) > expires_at:
                        # Expired, delete it
                        import os
                        os.remove(file_path)
                        return None

                return data.get("state")
        except Exception as e:
            print(f"[FileStateManager] Error getting state: {e}")
            return None

    async def delete_plan_state(
        self,
        plan_id: str
    ) -> bool:
        """
        Delete all states for a plan from file system.

        Args:
            plan_id: Unique plan identifier

        Returns:
            bool: True if deleted successfully
        """
        try:
            import os
            import glob

            pattern = self._get_file_path(plan_id, "*")

            files = glob.glob(pattern)
            for file_path in files:
                os.remove(file_path)

            return True
        except Exception as e:
            print(f"[FileStateManager] Error deleting state: {e}")
            return False

    async def get_plan_status(
        self,
        plan_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get overall plan status from file system.

        Args:
            plan_id: Unique plan identifier

        Returns:
            Optional[Dict]: Plan status with all step states
        """
        try:
            import os
            import glob
            import json
            from datetime import datetime

            pattern = self._get_file_path(plan_id, "*")
            files = glob.glob(pattern)

            step_states = {}
            for file_path in files:
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)

                    # Check if expired
                    if "expires_at" in data:
                        expires_at = datetime.fromisoformat(data["expires_at"])
                        if datetime.now(timezone.utc) > expires_at:
                            continue

                    # Extract step_id from filename
                    filename = os.path.basename(file_path)
                    parts = filename.replace(".json", "").split("_")
                    if len(parts) >= 2:
                        step_id = parts[-1]
                        step_states[step_id] = data.get("state")
                except Exception:
                    continue

            return step_states if step_states else None
        except Exception as e:
            print(f"[FileStateManager] Error getting plan status: {e}")
            return None


def create_state_manager(
    backend: str = "memory",
    **kwargs
) -> StateManager:
    """
    Factory function to create State Manager instance.

    Args:
        backend: Backend type ("memory", "redis", "file")
        **kwargs: Backend-specific configuration
            - redis_host: Redis host (default: "localhost")
            - redis_port: Redis port (default: 6379)
            - base_dir: Base directory for file backend (default: "./state")

    Returns:
        StateManager: Configured State Manager instance

    Raises:
        ValueError: If backend is invalid
    """
    if backend == "memory":
        return MemoryStateManager()
    elif backend == "redis":
        redis_host = kwargs.get("redis_host", "localhost")
        redis_port = kwargs.get("redis_port", 6379)
        return RedisStateManager(redis_host, redis_port)
    elif backend == "file":
        base_dir = kwargs.get("base_dir", "./state")
        return FileStateManager(base_dir)
    else:
        raise ValueError(
            f"Invalid backend: {backend}. "
            "Must be 'memory', 'redis', or 'file'"
        )


# Usage example
if __name__ == "__main__":
    import asyncio

    async def main():
        # Create Memory State Manager
        sm = create_state_manager("memory")

        # Save state
        await sm.save_step_state("plan-001", "s1", {"count": 3}, ttl_seconds=3600)

        # Retrieve state
        state = await sm.get_step_state("plan-001", "s1")
        print(f"Retrieved state: {state}")

        # Get plan status
        status = await sm.get_plan_status("plan-001")
        print(f"Plan status: {status}")

        # Cleanup
        await sm.delete_plan_state("plan-001")

    asyncio.run(main())
