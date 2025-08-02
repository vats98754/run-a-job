"""Base repository class with common database operations."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar
from datetime import datetime

from sqlalchemy import create_engine, MetaData, select, insert, update, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel

from run_a_job.config.settings import settings
from run_a_job.config.logging import get_logger


logger = get_logger(__name__)

# Type variable for models
T = TypeVar('T', bound=BaseModel)

# Database setup
Base = declarative_base()
metadata = MetaData()


class BaseRepository(Generic[T], ABC):
    """Base repository class with common CRUD operations."""
    
    def __init__(self, model_class: type[T]):
        """Initialize repository with model class.
        
        Args:
            model_class: Pydantic model class
        """
        self.model_class = model_class
        self.engine = create_async_engine(settings.database_url)
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
    @abstractmethod
    def _get_table(self):
        """Get the SQLAlchemy table for this repository."""
        pass
        
    @abstractmethod
    def _model_to_dict(self, model: T) -> Dict[str, Any]:
        """Convert model to dictionary for database storage."""
        pass
        
    @abstractmethod
    def _dict_to_model(self, data: Dict[str, Any]) -> T:
        """Convert dictionary from database to model."""
        pass
        
    async def create(self, model: T) -> T:
        """Create a new record.
        
        Args:
            model: Model instance to create
            
        Returns:
            Created model instance
        """
        try:
            async with self.session_factory() as session:
                table = self._get_table()
                data = self._model_to_dict(model)
                
                # Add timestamps
                data['created_at'] = datetime.utcnow()
                data['updated_at'] = datetime.utcnow()
                
                stmt = insert(table).values(data)
                await session.execute(stmt)
                await session.commit()
                
                logger.debug(f"Created {self.model_class.__name__} with ID: {data.get('id')}")
                return model
                
        except Exception as e:
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise
            
    async def get(self, id: str) -> Optional[T]:
        """Get a record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Model instance or None if not found
        """
        try:
            async with self.session_factory() as session:
                table = self._get_table()
                stmt = select(table).where(table.c.id == id)
                result = await session.execute(stmt)
                row = result.fetchone()
                
                if row:
                    data = dict(row._mapping)
                    return self._dict_to_model(data)
                    
                return None
                
        except Exception as e:
            logger.error(f"Error getting {self.model_class.__name__} {id}: {e}")
            raise
            
    async def update(self, model: T) -> T:
        """Update an existing record.
        
        Args:
            model: Model instance to update
            
        Returns:
            Updated model instance
        """
        try:
            async with self.session_factory() as session:
                table = self._get_table()
                data = self._model_to_dict(model)
                
                # Update timestamp
                data['updated_at'] = datetime.utcnow()
                
                stmt = update(table).where(table.c.id == data['id']).values(data)
                result = await session.execute(stmt)
                await session.commit()
                
                if result.rowcount == 0:
                    raise ValueError(f"{self.model_class.__name__} {data['id']} not found")
                    
                logger.debug(f"Updated {self.model_class.__name__} {data['id']}")
                return model
                
        except Exception as e:
            logger.error(f"Error updating {self.model_class.__name__}: {e}")
            raise
            
    async def delete(self, id: str) -> bool:
        """Delete a record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            async with self.session_factory() as session:
                table = self._get_table()
                stmt = delete(table).where(table.c.id == id)
                result = await session.execute(stmt)
                await session.commit()
                
                deleted = result.rowcount > 0
                if deleted:
                    logger.debug(f"Deleted {self.model_class.__name__} {id}")
                else:
                    logger.warning(f"{self.model_class.__name__} {id} not found for deletion")
                    
                return deleted
                
        except Exception as e:
            logger.error(f"Error deleting {self.model_class.__name__} {id}: {e}")
            raise
            
    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters
    ) -> List[T]:
        """List records with optional filtering.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            **filters: Filter conditions
            
        Returns:
            List of model instances
        """
        try:
            async with self.session_factory() as session:
                table = self._get_table()
                stmt = select(table)
                
                # Apply filters
                for key, value in filters.items():
                    if value is not None and hasattr(table.c, key):
                        stmt = stmt.where(getattr(table.c, key) == value)
                        
                # Apply pagination
                stmt = stmt.offset(offset).limit(limit)
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                models = []
                for row in rows:
                    data = dict(row._mapping)
                    models.append(self._dict_to_model(data))
                    
                return models
                
        except Exception as e:
            logger.error(f"Error listing {self.model_class.__name__}: {e}")
            raise
            
    async def count(self, **filters) -> int:
        """Count records with optional filtering.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            Number of matching records
        """
        try:
            async with self.session_factory() as session:
                table = self._get_table()
                stmt = select(table).count()
                
                # Apply filters
                for key, value in filters.items():
                    if value is not None and hasattr(table.c, key):
                        stmt = stmt.where(getattr(table.c, key) == value)
                        
                result = await session.execute(stmt)
                return result.scalar()
                
        except Exception as e:
            logger.error(f"Error counting {self.model_class.__name__}: {e}")
            raise
            
    async def create_tables(self) -> None:
        """Create database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(metadata.create_all)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
            
    async def close(self) -> None:
        """Close database connections."""
        try:
            await self.engine.dispose()
            logger.debug("Database connections closed")
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
            
    def _serialize_json_field(self, value: Any) -> str:
        """Serialize a value to JSON string for database storage."""
        if value is None:
            return None
        return json.dumps(value)
        
    def _deserialize_json_field(self, value: str) -> Any:
        """Deserialize a JSON string from database."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value