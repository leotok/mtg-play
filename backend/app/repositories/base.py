from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

# Generic type for model classes
ModelType = TypeVar('ModelType')

class BaseRepository(Generic[ModelType], ABC):
    """Base repository with common CRUD operations"""
    
    def __init__(self, db: Session, model_class: type[ModelType]):
        self.db = db
        self.model_class = model_class
    
    def get_by_id(self, id: Union[int, str]) -> Optional[ModelType]:
        """Get a record by ID (supports int and string primary keys)"""
        # Try to determine the primary key column
        pk_column = self.model_class.__table__.primary_key.columns[0]
        return self.db.query(self.model_class).filter(pk_column == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination"""
        return self.db.query(self.model_class).offset(skip).limit(limit).all()
    
    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record"""
        db_obj = self.model_class(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """Update an existing record"""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: int) -> ModelType:
        """Delete a record by ID"""
        obj = self.get_by_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj
    
    def count(self) -> int:
        """Count total records"""
        return self.db.query(self.model_class).count()
    
    def exists(self, **criteria) -> bool:
        """Check if a record exists with given criteria"""
        return self.db.query(self.model_class).filter_by(**criteria).first() is not None
    
    def find_by_criteria(self, **criteria) -> Optional[ModelType]:
        """Find first record matching criteria"""
        return self.db.query(self.model_class).filter_by(**criteria).first()
    
    def find_all_by_criteria(self, **criteria) -> List[ModelType]:
        """Find all records matching criteria"""
        return self.db.query(self.model_class).filter_by(**criteria).all()
    
    def filter_by(self, *filters, **criteria) -> List[ModelType]:
        """Filter records by SQLAlchemy filters and criteria"""
        query = self.db.query(self.model_class)
        
        if filters:
            query = query.filter(*filters)
        
        if criteria:
            query = query.filter_by(**criteria)
        
        return query.all()
