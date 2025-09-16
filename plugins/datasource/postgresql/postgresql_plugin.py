"""
PostgreSQL Data Source Plugin - Real implementation
"""

import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional
import logging
import sys
from pathlib import Path

# Add backend to Python path for base plugin imports
backend_path = Path(__file__).parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from services.base_plugin import DataSourcePlugin

logger = logging.getLogger(__name__)

class PostgreSQLDataSourcePlugin(DataSourcePlugin):
    """Real PostgreSQL data source implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 5432)
        self.database = config.get("database")
        self.username = config.get("username")
        self.password = config.get("password")
        self.table_name = config.get("table_name")
        self.text_column = config.get("text_column")
        self.id_column = config.get("id_column", "id")
        self.metadata_columns = config.get("metadata_columns", [])
        
        self.connection = None
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate PostgreSQL configuration"""
        required_fields = ["host", "database", "username", "password", "table_name", "text_column"]
        if not all(field in config and config[field] for field in required_fields):
            return False
        
        # Validate port
        port = config.get("port", 5432)
        if not isinstance(port, int) or port <= 0 or port > 65535:
            return False
        
        return True
    
    async def initialize(self) -> bool:
        """Initialize PostgreSQL connection"""
        try:
            # Create connection string
            connection_string = (
                f"host={self.host} "
                f"port={self.port} "
                f"database={self.database} "
                f"user={self.username} "
                f"password={self.password}"
            )
            
            # Connect to PostgreSQL
            self.connection = psycopg2.connect(connection_string)
            
            # Test the connection
            await self.test_connection()
            
            self.initialized = True
            logger.info(f"PostgreSQL connection established to {self.host}:{self.port}/{self.database}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection: {e}")
            return False
    
    async def get_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve documents from PostgreSQL"""
        if not self.initialized or not self.connection:
            raise RuntimeError("Plugin not initialized")
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Build query
            columns = [self.id_column, self.text_column] + self.metadata_columns
            columns_str = ", ".join(columns)
            
            query = f"SELECT {columns_str} FROM {self.table_name}"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Format documents
            documents = []
            for row in rows:
                doc_id = str(row[self.id_column])
                content = row[self.text_column] or ""
                
                # Build metadata
                metadata = {"source": f"postgresql:{self.table_name}"}
                for col in self.metadata_columns:
                    if col in row and row[col] is not None:
                        metadata[col] = row[col]
                
                documents.append({
                    "id": doc_id,
                    "content": content,
                    "metadata": metadata
                })
            
            cursor.close()
            logger.info(f"Retrieved {len(documents)} documents from PostgreSQL")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to retrieve documents from PostgreSQL: {e}")
            return []
    
    async def get_document_count(self) -> int:
        """Get total number of documents"""
        if not self.initialized or not self.connection:
            return 0
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
            
        except Exception as e:
            logger.error(f"Failed to get document count from PostgreSQL: {e}")
            return 0
    
    async def test_connection(self) -> bool:
        """Test PostgreSQL connection"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            return result[0] == 1
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            return False
    
    async def get_table_info(self) -> Dict[str, Any]:
        """Get information about the table"""
        if not self.initialized or not self.connection:
            return {"columns": [], "row_count": 0, "status": "not_initialized"}
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get column information
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (self.table_name,))
            
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            row_count = cursor.fetchone()[0]
            
            cursor.close()
            
            return {
                "columns": [dict(col) for col in columns],
                "row_count": row_count,
                "status": "active",
                "table_name": self.table_name,
                "text_column": self.text_column,
                "id_column": self.id_column
            }
            
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL table info: {e}")
            return {"columns": [], "row_count": 0, "status": "error"}
    
    async def execute_custom_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a custom SQL query"""
        if not self.initialized or not self.connection:
            raise RuntimeError("Plugin not initialized")
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            cursor.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to execute custom query: {e}")
            raise
    
    async def cleanup(self):
        """Clean up PostgreSQL connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
        await super().cleanup()