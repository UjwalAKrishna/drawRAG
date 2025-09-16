"""
Core Pipeline Engine - Orchestrates plugin execution in pipelines
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from .plugin_framework import PluginFramework, PluginInterface

logger = logging.getLogger(__name__)


class PipelineNode:
    """Represents a node in the pipeline"""
    
    def __init__(self, node_id: str, plugin_id: str, config: Dict[str, Any]):
        self.node_id = node_id
        self.plugin_id = plugin_id
        self.config = config
        self.connections: List[str] = []  # Connected node IDs
    
    def add_connection(self, target_node_id: str):
        """Add connection to another node"""
        if target_node_id not in self.connections:
            self.connections.append(target_node_id)


class Pipeline:
    """Core pipeline data structure"""
    
    def __init__(self, pipeline_id: str, name: str = None):
        self.pipeline_id = pipeline_id
        self.name = name or f"Pipeline-{pipeline_id}"
        self.nodes: Dict[str, PipelineNode] = {}
        self.created_at = datetime.now()
        self.status = "created"
        self.metadata: Dict[str, Any] = {}
    
    def add_node(self, node_id: str, plugin_id: str, config: Dict[str, Any]):
        """Add a node to the pipeline"""
        node = PipelineNode(node_id, plugin_id, config)
        self.nodes[node_id] = node
        return node
    
    def connect_nodes(self, source_node_id: str, target_node_id: str):
        """Connect two nodes in the pipeline"""
        if source_node_id in self.nodes:
            self.nodes[source_node_id].add_connection(target_node_id)
    
    def get_execution_order(self) -> List[str]:
        """Get nodes in execution order (topological sort)"""
        # Simple implementation - can be enhanced with proper topological sort
        visited = set()
        result = []
        
        def dfs(node_id: str):
            if node_id in visited or node_id not in self.nodes:
                return
            visited.add(node_id)
            result.append(node_id)
            
            # Visit connected nodes
            for connected_id in self.nodes[node_id].connections:
                dfs(connected_id)
        
        # Start DFS from nodes with no incoming connections
        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id)
        
        return result


class PipelineEngine:
    """Core engine for executing pipelines"""
    
    def __init__(self, plugin_framework: PluginFramework):
        self.plugin_framework = plugin_framework
        self.pipelines: Dict[str, Pipeline] = {}
        self.active_executions: Dict[str, Dict[str, Any]] = {}
    
    def create_pipeline(self, name: str = None) -> str:
        """Create a new pipeline"""
        pipeline_id = str(uuid.uuid4())
        pipeline = Pipeline(pipeline_id, name)
        self.pipelines[pipeline_id] = pipeline
        
        logger.info(f"Created pipeline: {pipeline_id}")
        return pipeline_id
    
    def add_pipeline_node(self, pipeline_id: str, node_id: str, 
                         plugin_id: str, config: Dict[str, Any]) -> bool:
        """Add a node to a pipeline"""
        if pipeline_id not in self.pipelines:
            logger.error(f"Pipeline not found: {pipeline_id}")
            return False
        
        pipeline = self.pipelines[pipeline_id]
        pipeline.add_node(node_id, plugin_id, config)
        
        logger.info(f"Added node {node_id} to pipeline {pipeline_id}")
        return True
    
    def connect_pipeline_nodes(self, pipeline_id: str, source_node_id: str, 
                              target_node_id: str) -> bool:
        """Connect two nodes in a pipeline"""
        if pipeline_id not in self.pipelines:
            return False
        
        pipeline = self.pipelines[pipeline_id]
        pipeline.connect_nodes(source_node_id, target_node_id)
        
        logger.info(f"Connected {source_node_id} -> {target_node_id} in pipeline {pipeline_id}")
        return True
    
    async def execute_pipeline(self, pipeline_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a pipeline with input data"""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
        
        pipeline = self.pipelines[pipeline_id]
        execution_id = str(uuid.uuid4())
        
        # Track execution
        self.active_executions[execution_id] = {
            "pipeline_id": pipeline_id,
            "started_at": datetime.now(),
            "status": "running",
            "current_node": None
        }
        
        try:
            result = await self._execute_pipeline_internal(pipeline, input_data, execution_id)
            
            # Update execution status
            self.active_executions[execution_id]["status"] = "completed"
            self.active_executions[execution_id]["completed_at"] = datetime.now()
            
            return result
            
        except Exception as e:
            self.active_executions[execution_id]["status"] = "failed"
            self.active_executions[execution_id]["error"] = str(e)
            logger.error(f"Pipeline execution failed: {e}")
            raise
        
        finally:
            # Cleanup execution tracking after some time
            # In production, this would be handled by a cleanup service
            pass
    
    async def _execute_pipeline_internal(self, pipeline: Pipeline, 
                                       input_data: Dict[str, Any], 
                                       execution_id: str) -> Dict[str, Any]:
        """Internal pipeline execution logic"""
        execution_order = pipeline.get_execution_order()
        current_data = input_data.copy()
        node_outputs = {}
        
        for node_id in execution_order:
            node = pipeline.nodes[node_id]
            
            # Update execution tracking
            self.active_executions[execution_id]["current_node"] = node_id
            
            # Get plugin instance
            plugin = self.plugin_framework.get_plugin(node.plugin_id)
            if not plugin:
                raise RuntimeError(f"Plugin not found: {node.plugin_id}")
            
            # Execute node
            try:
                node_output = await self._execute_node(plugin, node, current_data, node_outputs)
                node_outputs[node_id] = node_output
                
                # Update current data for next nodes
                if isinstance(node_output, dict):
                    current_data.update(node_output)
                
                logger.debug(f"Node {node_id} executed successfully")
                
            except Exception as e:
                logger.error(f"Node {node_id} execution failed: {e}")
                raise RuntimeError(f"Node {node_id} failed: {str(e)}")
        
        return {
            "status": "completed",
            "pipeline_id": pipeline.pipeline_id,
            "execution_id": execution_id,
            "node_outputs": node_outputs,
            "final_output": current_data
        }
    
    async def _execute_node(self, plugin: PluginInterface, node: PipelineNode, 
                           input_data: Dict[str, Any], 
                           previous_outputs: Dict[str, Any]) -> Any:
        """Execute a single node"""
        # This is where plugin-specific execution logic would go
        # For now, we'll define a simple interface that plugins can implement
        
        if hasattr(plugin, 'execute'):
            return await plugin.execute(input_data, node.config, previous_outputs)
        elif hasattr(plugin, 'process'):
            return await plugin.process(input_data)
        else:
            logger.warning(f"Plugin {plugin.plugin_id} has no execute/process method")
            return input_data
    
    def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """Get pipeline by ID"""
        return self.pipelines.get(pipeline_id)
    
    def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all pipelines"""
        return [
            {
                "pipeline_id": p.pipeline_id,
                "name": p.name,
                "node_count": len(p.nodes),
                "created_at": p.created_at,
                "status": p.status
            }
            for p in self.pipelines.values()
        ]
    
    def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete a pipeline"""
        if pipeline_id in self.pipelines:
            del self.pipelines[pipeline_id]
            logger.info(f"Deleted pipeline: {pipeline_id}")
            return True
        return False
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status"""
        return self.active_executions.get(execution_id)
    
    def list_active_executions(self) -> List[Dict[str, Any]]:
        """List all active executions"""
        return list(self.active_executions.values())