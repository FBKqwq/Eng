from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ContainerStatus(BaseModel):
    name: str
    service: str
    status: str = Field(description="Normalized status for frontend display: running, down, or unknown")
    raw_state: Optional[str] = None
    raw_status: Optional[str] = None
    image: Optional[str] = None
    container_id: Optional[str] = None
    ports: Optional[str] = None
    endpoint: Optional[str] = None
    cpu_percent: Optional[str] = None
    memory_usage: Optional[str] = None
    memory_percent: Optional[str] = None
    network_io: Optional[str] = None
    block_io: Optional[str] = None
    pids: Optional[str] = None
    detail: Optional[str] = None


class DockerStatusResponse(BaseModel):
    project: str
    available: bool
    error: Optional[str] = None
    containers: Dict[str, ContainerStatus] = Field(default_factory=dict)


class ElasticsearchHealthSnapshot(BaseModel):
    hosts: List[str]
    index_pattern: str
    available: bool
    cluster_status: str = Field(description="Elasticsearch cluster health: green, yellow, red, or unknown")
    cluster_name: Optional[str] = None
    node_name: Optional[str] = None
    version: Optional[str] = None
    number_of_nodes: Optional[int] = None
    number_of_data_nodes: Optional[int] = None
    active_shards: Optional[int] = None
    relocating_shards: Optional[int] = None
    initializing_shards: Optional[int] = None
    unassigned_shards: Optional[int] = None
    timed_out: Optional[bool] = None
    indices_count: Optional[int] = None
    docs_count: Optional[int] = None
    error: Optional[str] = None


class KafkaTopicSnapshot(BaseModel):
    name: str
    exists: bool
    partitions: Optional[int] = None
    replication_factor: Optional[int] = None


class KafkaStatusSnapshot(BaseModel):
    bootstrap_servers: List[str]
    topic: str
    available: bool
    brokers_count: Optional[int] = None
    topics_count: Optional[int] = None
    configured_topic: KafkaTopicSnapshot
    error: Optional[str] = None


class SystemStatusResponse(BaseModel):
    kafka_bootstrap_servers: str
    kafka_topic: str
    elasticsearch_hosts: str
    elasticsearch_index_pattern: str
    kafka: KafkaStatusSnapshot
    elasticsearch: ElasticsearchHealthSnapshot
    docker: DockerStatusResponse
    containers: Dict[str, ContainerStatus]
    services: Dict[str, ContainerStatus]
