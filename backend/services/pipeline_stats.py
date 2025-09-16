"""
Pipeline Stats - Handles pipeline statistics and analytics
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class PipelineStatsManager:
    """Manages pipeline statistics and analytics"""
    
    def __init__(self, storage, validator):
        self.storage = storage
        self.validator = validator
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics"""
        storage_stats = self.storage.get_storage_stats()
        
        # Add health score stats
        pipelines = self.storage.list_pipelines()
        if pipelines:
            health_scores = [self.validator.get_pipeline_health_score(p) for p in pipelines]
            storage_stats["health_scores"] = {
                "average": sum(health_scores) / len(health_scores),
                "min": min(health_scores),
                "max": max(health_scores)
            }
            
            # Add component type statistics
            storage_stats["component_stats"] = self._get_component_type_stats(pipelines)
            storage_stats["complexity_stats"] = self._get_complexity_stats(pipelines)
            
        else:
            storage_stats["health_scores"] = {"average": 0.0, "min": 0.0, "max": 0.0}
            storage_stats["component_stats"] = {}
            storage_stats["complexity_stats"] = {}
            
        return storage_stats
    
    def _get_component_type_stats(self, pipelines: List[Any]) -> Dict[str, int]:
        """Get statistics about pipeline component types"""
        stats = {}
        
        for pipeline in pipelines:
            for component in pipeline.components:
                comp_type = f"{component.type}_{component.subtype}"
                stats[comp_type] = stats.get(comp_type, 0) + 1
        
        return stats
    
    def _get_complexity_stats(self, pipelines: List[Any]) -> Dict[str, Any]:
        """Get pipeline complexity statistics"""
        if not pipelines:
            return {}
        
        component_counts = [len(p.components) for p in pipelines]
        connection_counts = [len(p.connections) for p in pipelines]
        
        return {
            "avg_components_per_pipeline": sum(component_counts) / len(component_counts),
            "max_components": max(component_counts),
            "min_components": min(component_counts),
            "avg_connections_per_pipeline": sum(connection_counts) / len(connection_counts),
            "max_connections": max(connection_counts),
            "min_connections": min(connection_counts)
        }
    
    def get_pipeline_performance_metrics(self, pipeline_id: str) -> Dict[str, Any]:
        """Get performance metrics for a specific pipeline"""
        config = self.storage.get_pipeline(pipeline_id)
        if not config:
            return {"error": "Pipeline not found"}
        
        return {
            "pipeline_id": pipeline_id,
            "health_score": self.validator.get_pipeline_health_score(config),
            "component_count": len(config.components),
            "connection_count": len(config.connections),
            "is_active": self.storage.is_pipeline_active(pipeline_id),
            "validation_errors": self.validator.get_validation_errors(config),
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }
    
    def get_system_health_overview(self) -> Dict[str, Any]:
        """Get overall system health overview"""
        pipelines = self.storage.list_pipelines()
        active_count = self.storage.get_active_pipeline_count()
        
        if not pipelines:
            return {
                "status": "no_pipelines",
                "message": "No pipelines configured",
                "recommendations": ["Create your first pipeline to get started"]
            }
        
        health_scores = [self.validator.get_pipeline_health_score(p) for p in pipelines]
        avg_health = sum(health_scores) / len(health_scores)
        
        # Determine system status
        if avg_health >= 0.8:
            status = "healthy"
            message = "System is operating well"
        elif avg_health >= 0.6:
            status = "warning"
            message = "Some pipelines need attention"
        else:
            status = "critical"
            message = "Multiple pipeline issues detected"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(pipelines, health_scores)
        
        return {
            "status": status,
            "message": message,
            "overall_health_score": avg_health,
            "total_pipelines": len(pipelines),
            "active_pipelines": active_count,
            "inactive_pipelines": len(pipelines) - active_count,
            "recommendations": recommendations
        }
    
    def _generate_recommendations(self, pipelines: List[Any], health_scores: List[float]) -> List[str]:
        """Generate system recommendations based on pipeline analysis"""
        recommendations = []
        
        # Check for low health scores
        low_health_count = sum(1 for score in health_scores if score < 0.6)
        if low_health_count > 0:
            recommendations.append(f"Review and fix {low_health_count} pipeline(s) with low health scores")
        
        # Check for inactive pipelines
        inactive_count = len(pipelines) - self.storage.get_active_pipeline_count()
        if inactive_count > len(pipelines) * 0.5:
            recommendations.append("Consider activating more pipelines or removing unused ones")
        
        # Check for missing component types
        all_component_types = set()
        for pipeline in pipelines:
            for component in pipeline.components:
                all_component_types.add(component.type)
        
        if len(all_component_types) < 3:
            recommendations.append("Ensure pipelines have all required component types (datasource, vectordb, llm)")
        
        # Performance recommendations
        if len(pipelines) > 10:
            recommendations.append("Consider organizing pipelines into categories for better management")
        
        if not recommendations:
            recommendations.append("System is running well - continue monitoring pipeline health")
        
        return recommendations
    
    def export_stats_report(self) -> Dict[str, Any]:
        """Export comprehensive statistics report"""
        stats = self.get_comprehensive_stats()
        health_overview = self.get_system_health_overview()
        
        return {
            "report_generated_at": str(self.storage.get_storage_stats().get("newest_pipeline", "N/A")),
            "system_overview": health_overview,
            "detailed_stats": stats,
            "summary": {
                "total_pipelines": stats.get("total_pipelines", 0),
                "active_pipelines": stats.get("active_pipelines", 0),
                "average_health_score": health_overview.get("overall_health_score", 0.0),
                "system_status": health_overview.get("status", "unknown")
            }
        }