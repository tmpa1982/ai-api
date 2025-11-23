import json
import logging
import base64
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
        
        if thread_id.startswith("thread_"):
            user_id = thread_id[7:]
        else:
            user_id = thread_id

        parent_checkpoint_id = config["configurable"].get("checkpoint_id")
        
        # Serialize checkpoint and metadata
        cp_type, cp_bytes = self.serde.dumps_typed(checkpoint)
        md_type, md_bytes = self.serde.dumps_typed(metadata)

        # Prepare the document
        doc = {
            "id": checkpoint["id"],
            "UserId": user_id,
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_type": cp_type,
            "checkpoint_data": base64.b64encode(cp_bytes).decode("utf-8"),
            "metadata_type": md_type,
            "metadata_data": base64.b64encode(md_bytes).decode("utf-8"),
            "parent_checkpoint_id": parent_checkpoint_id,
        }

        try:
            await self.container.upsert_item(doc)
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to save checkpoint to Cosmos DB: {e}")
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
        cp_type = item["checkpoint_type"]
        cp_bytes = base64.b64decode(item["checkpoint_data"])
        checkpoint = self.serde.loads_typed((cp_type, cp_bytes))

        md_type = item["metadata_type"]
        md_bytes = base64.b64decode(item["metadata_data"])
        metadata = self.serde.loads_typed((md_type, md_bytes))
        
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

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Asynchronously store intermediate writes."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        if thread_id.startswith("thread_"):
            user_id = thread_id[7:]
        else:
            user_id = thread_id

        # We need to store these writes associated with the checkpoint/task
        # Since CosmosDB is a document store, we can store them as separate documents
        # or update the checkpoint document. 
        # LangGraph seems to treat writes as separate entities that might be retrieved later.
        # Let's store them as a separate document type "writes".
        
        for idx, (channel, value) in enumerate(writes):
            # Serialize value
            val_type, val_bytes = self.serde.dumps_typed(value)
            
            doc = {
                "id": f"writes_{thread_id}_{checkpoint_id}_{task_id}_{idx}",
                "UserId": user_id,
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
                "task_id": task_id,
                "task_path": task_path,
                "channel": channel,
                "type": "writes",
                "value_type": val_type,
                "value_data": base64.b64encode(val_bytes).decode("utf-8"),
                "idx": idx
            }
            
            try:
                await self.container.upsert_item(doc)
            except CosmosHttpResponseError as e:
                logger.error(f"Failed to save writes to Cosmos DB: {e}")
                raise e

    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: dict[str, Any]) -> RunnableConfig:
        raise NotImplementedError("Use aput for async CosmosDB operations")

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        raise NotImplementedError("Use aget_tuple for async CosmosDB operations")

    def list(self, config: Optional[RunnableConfig], *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) ->AsyncIterator[CheckpointTuple]:
        raise NotImplementedError("Use alist for async CosmosDB operations")
