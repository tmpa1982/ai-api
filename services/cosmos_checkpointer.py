import json
import logging
from typing import Any, AsyncIterator, Dict, Optional, Sequence, Tuple

from azure.cosmos import CosmosClient
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.core.exceptions import AzureError
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    SerializerProtocol,
)
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

logger = logging.getLogger(__name__)

class CosmosDBSaver(BaseCheckpointSaver):
    """A checkpoint saver that stores checkpoints in Azure Cosmos DB."""

    def __init__(
        self,
        container,
        serializer: Optional[SerializerProtocol] = None,
    ):
        super().__init__(serde=serializer or JsonPlusSerializer())
        self.container = container

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict[str, Any],
    ) -> RunnableConfig:
        """Save a checkpoint to the database asynchronously."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        
        # Determine user_id from thread_id or metadata
        # Assuming thread_id format "thread_{user_email}" or "thread_{uuid}"
        # And partition key is /UserId. 
        # We will use thread_id as UserId for simplicity and uniqueness per thread if not explicitly provided.
        # However, user specified partition key is /UserId.
        # If we want to group by user, we should extract user_id. 
        # But for now, let's use thread_id as the partition key value to ensure we can retrieve it easily by thread_id.
        # Wait, if partition key is /UserId, we must provide it.
        # Let's try to extract user_email from thread_id if possible, otherwise use thread_id.
        if thread_id.startswith("thread_"):
            user_id = thread_id[7:]
        else:
            user_id = thread_id

        parent_checkpoint_id = config["configurable"].get("checkpoint_id")
        
        # Prepare the document
        doc = {
            "id": checkpoint["id"],
            "UserId": user_id,
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint": self.serde.dumps(checkpoint).decode("utf-8"),
            "metadata": self.serde.dumps(metadata).decode("utf-8"),
            "parent_checkpoint_id": parent_checkpoint_id,
        }

        try:
            await self.container.upsert_item(doc)
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to save checkpoint to Cosmos DB: {e}")
            # Handle 429 (Too Many Requests) or other errors if needed
            raise e

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Get a checkpoint tuple from the database asynchronously."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        if thread_id.startswith("thread_"):
            user_id = thread_id[7:]
        else:
            user_id = thread_id

        if checkpoint_id:
            # Get specific checkpoint
            try:
                item = await self.container.read_item(item=checkpoint_id, partition_key=user_id)
                return self._parse_item(item, config)
            except CosmosHttpResponseError as e:
                if e.status_code == 404:
                    return None
                logger.error(f"Failed to read checkpoint from Cosmos DB: {e}")
                raise e
        else:
            # Get latest checkpoint
            # Query for the latest checkpoint for this thread
            query = "SELECT * FROM c WHERE c.thread_id = @thread_id ORDER BY c._ts DESC OFFSET 0 LIMIT 1"
            parameters = [{"name": "@thread_id", "value": thread_id}]
            
            try:
                items = self.container.query_items(
                    query=query,
                    parameters=parameters,
                    partition_key=user_id
                )
                
                # query_items returns an async iterator
                async for item in items:
                    return self._parse_item(item, config)
                
                return None
            except CosmosHttpResponseError as e:
                logger.error(f"Failed to query latest checkpoint from Cosmos DB: {e}")
                raise e

    def _parse_item(self, item: dict, config: RunnableConfig) -> CheckpointTuple:
        checkpoint = self.serde.loads(item["checkpoint"].encode("utf-8"))
        metadata = self.serde.loads(item["metadata"].encode("utf-8"))
        parent_checkpoint_id = item.get("parent_checkpoint_id")
        
        return CheckpointTuple(
            config,
            checkpoint,
            metadata,
            (
                {
                    "configurable": {
                        "thread_id": config["configurable"]["thread_id"],
                        "checkpoint_ns": config["configurable"].get("checkpoint_ns", ""),
                        "checkpoint_id": parent_checkpoint_id,
                    }
                }
                if parent_checkpoint_id
                else None
            ),
        )

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """List checkpoints from the database asynchronously."""
        thread_id = config["configurable"]["thread_id"]
        if thread_id.startswith("thread_"):
            user_id = thread_id[7:]
        else:
            user_id = thread_id
            
        query = "SELECT * FROM c WHERE c.thread_id = @thread_id"
        parameters = [{"name": "@thread_id", "value": thread_id}]

        if before:
            query += " AND c._ts < @before_ts"
            # This is tricky because we don't have the timestamp of 'before' readily available unless we fetch it.
            # Assuming 'before' config has checkpoint_id, we might need to fetch it first to get its timestamp.
            # For simplicity, let's ignore 'before' optimization for now or implement if strictly needed.
            # Alternatively, if checkpoint IDs are time-ordered (like UUID v7 or similar), we could use that.
            # But standard UUIDs are not. LangGraph uses UUIDs.
            # Cosmos DB has _ts (timestamp).
            pass

        query += " ORDER BY c._ts DESC"
        
        if limit:
            query += f" OFFSET 0 LIMIT {limit}"

        try:
            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            )
            async for item in items:
                yield self._parse_item(item, config)
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to list checkpoints from Cosmos DB: {e}")
            raise e

    # Sync methods are required by abstract base class but we can leave them NotImplemented or implement simple wrappers if needed.
    # Since we are using this in an async context (FastAPI), we primarily need async methods.
    # However, BaseCheckpointSaver might require sync methods to be defined.
    
    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: dict[str, Any]) -> RunnableConfig:
        raise NotImplementedError("Use aput for async CosmosDB operations")

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        raise NotImplementedError("Use aget_tuple for async CosmosDB operations")

    def list(self, config: Optional[RunnableConfig], *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) ->AsyncIterator[CheckpointTuple]:
        raise NotImplementedError("Use alist for async CosmosDB operations")
