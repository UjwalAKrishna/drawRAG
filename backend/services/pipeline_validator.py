"""
Pipeline Validator - Handles pipeline configuration validation
"""

import logging
from typing import Dict, List, Any
from models import PipelineConfig, ComponentConfig, ComponentType

logger = logging.getLogger(__name__)


class PipelineValidator:
    """Validates pipeline configurations and components"""
    
    def __init__(self, plugin_manager):
        self.plugin_manager = plugin_manager
    
    async def validate_pipeline_config(self, config: PipelineConfig) -> bool:
        """Validate complete pipeline configuration"""
        try:
            if not config.components:
                raise ValueError("Pipeline must have at least one component")
            
            # Check for required component types
            component_types = {comp.type for comp in config.components}
            required_types = {ComponentType.DATASOURCE, ComponentType.VECTORDB, ComponentType.LLM}
            
            missing_types = required_types - component_types
            if missing_types:
                raise ValueError(f"Pipeline missing required components: {missing_types}")
            
            # Validate each component
            for component in config.components:
                if not await self.validate_component_config(component):
                    raise ValueError(f"Invalid configuration for component {component.id}")
            
            # Validate connections
            await self._validate_connections(config)
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline validation failed: {e}")
            return False
    
    async def validate_component_config(self, config: ComponentConfig) -> bool:
        """Validate component configuration"""
        try:
            return self.plugin_manager.validate_plugin_config(
                config.type, config.subtype, config.config
            )
        except Exception as e:
            logger.error(f"Component validation failed: {str(e)}")
            return False
    
    async def _validate_connections(self, config: PipelineConfig):
        """Validate pipeline connections"""
        # Create component lookup
        components = {comp.id: comp for comp in config.components}
        
        # Check that all connection endpoints exist
        for connection in config.connections:
            if connection.from_component not in components:
                raise ValueError(f"Connection source component not found: {connection.from_component}")
            
            if connection.to_component not in components:
                raise ValueError(f"Connection target component not found: {connection.to_component}")
        
        # Validate connection flow (datasource -> vectordb -> llm)
        await self._validate_connection_flow(config, components)
    
    async def _validate_connection_flow(self, config: PipelineConfig, components: Dict[str, ComponentConfig]):
        """Validate the logical flow of connections"""
        # Find components by type
        datasources = [comp for comp in config.components if comp.type == ComponentType.DATASOURCE]
        vectordbs = [comp for comp in config.components if comp.type == ComponentType.VECTORDB]
        llms = [comp for comp in config.components if comp.type == ComponentType.LLM]
        
        # Basic validation: ensure we have the pipeline flow
        if len(datasources) == 0:
            raise ValueError("Pipeline must have at least one data source")
        if len(vectordbs) == 0:
            raise ValueError("Pipeline must have at least one vector database")
        if len(llms) == 0:
            raise ValueError("Pipeline must have at least one LLM")
        
        logger.info(f"Pipeline validation passed: {len(datasources)} datasources, {len(vectordbs)} vectordbs, {len(llms)} llms")
    
    def check_component_compatibility(self, comp1: ComponentConfig, comp2: ComponentConfig) -> bool:
        """Check if two components are compatible for connection"""
        # Define compatibility rules
        compatibility_rules = {
            (ComponentType.DATASOURCE, ComponentType.VECTORDB): True,
            (ComponentType.VECTORDB, ComponentType.LLM): True,
            (ComponentType.DATASOURCE, ComponentType.LLM): True,  # Allow direct connection
        }
        
        return compatibility_rules.get((comp1.type, comp2.type), False)
    
    def get_validation_errors(self, config: PipelineConfig) -> List[str]:
        """Get detailed validation errors for a pipeline"""
        errors = []
        
        if not config.components:
            errors.append("Pipeline must have at least one component")
            return errors
        
        # Check for required component types
        component_types = {comp.type for comp in config.components}
        required_types = {ComponentType.DATASOURCE, ComponentType.VECTORDB, ComponentType.LLM}
        
        missing_types = required_types - component_types
        if missing_types:
            errors.append(f"Pipeline missing required components: {', '.join(missing_types)}")
        
        # Validate individual components
        for component in config.components:
            try:
                if not self.plugin_manager.get_plugin(component.type, component.subtype):
                    errors.append(f"Plugin not found for component {component.id}: {component.type}:{component.subtype}")
            except Exception as e:
                errors.append(f"Component {component.id} validation error: {str(e)}")
        
        return errors
    
    def get_pipeline_health_score(self, config: PipelineConfig) -> float:
        """Calculate a health score for the pipeline (0.0 to 1.0)"""
        try:
            total_checks = 0
            passed_checks = 0
            
            # Check if all required components exist
            total_checks += 1
            component_types = {comp.type for comp in config.components}
            required_types = {ComponentType.DATASOURCE, ComponentType.VECTORDB, ComponentType.LLM}
            if required_types.issubset(component_types):
                passed_checks += 1
            
            # Check component configurations
            for component in config.components:
                total_checks += 1
                try:
                    if self.plugin_manager.get_plugin(component.type, component.subtype):
                        passed_checks += 1
                except:
                    pass
            
            # Check connections
            if config.connections:
                total_checks += 1
                components = {comp.id: comp for comp in config.components}
                all_connections_valid = all(
                    conn.from_component in components and conn.to_component in components
                    for conn in config.connections
                )
                if all_connections_valid:
                    passed_checks += 1
            
            return passed_checks / total_checks if total_checks > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Health score calculation failed: {e}")
            return 0.0