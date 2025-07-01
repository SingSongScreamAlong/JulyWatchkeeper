"""
Base CRUD Class for WATCHKEEPER

This module provides a generic CRUD class for database operations.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base
from src.schemas.common import PaginationParams

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for CRUD operations.
    
    Attributes:
        model: SQLAlchemy model class
    """
    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD with SQLAlchemy model.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """
        Get a record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            Record if found, None otherwise
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        pagination: PaginationParams,
        filters: Optional[List] = None
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and optional filters.
        
        Args:
            db: Database session
            pagination: Pagination parameters
            filters: Optional list of filter conditions
            
        Returns:
            List of records
        """
        skip = (pagination.page - 1) * pagination.page_size
        query = select(self.model)
        
        if filters:
            query = query.where(and_(*filters))
            
        query = query.offset(skip).limit(pagination.page_size)
        result = await db.execute(query)
        return result.scalars().all()

    async def count(
        self, 
        db: AsyncSession, 
        *, 
        filters: Optional[List] = None
    ) -> int:
        """
        Count records with optional filters.
        
        Args:
            db: Database session
            filters: Optional list of filter conditions
            
        Returns:
            Count of records
        """
        query = select(func.count()).select_from(self.model)
        
        if filters:
            query = query.where(and_(*filters))
            
        result = await db.execute(query)
        return result.scalar_one()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Create schema
            
        Returns:
            Created record
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            db: Database session
            db_obj: Record to update
            obj_in: Update schema or dictionary
            
        Returns:
            Updated record
        """
        obj_data = jsonable_encoder(db_obj)
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """
        Delete a record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            Deleted record if found, None otherwise
        """
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
