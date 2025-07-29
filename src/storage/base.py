"""
베이스 리포지토리 클래스
공통 CRUD 작업 제공
"""

import logging
from typing import TypeVar, Generic, Type, List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import and_, or_, desc, asc
from pydantic import BaseModel

from src.storage.models import Base
from src.core.exceptions import DatabaseError, NotFoundError, ConflictError

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """베이스 리포지토리 클래스"""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
        self.logger = logging.getLogger(f"repository.{model.__name__}")
    
    def get(self, id: Union[UUID, str]) -> Optional[ModelType]:
        """ID로 엔티티 조회"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting {self.model.__name__} by id {id}: {e}")
            raise DatabaseError(f"Failed to get {self.model.__name__}")
    
    def get_or_404(self, id: Union[UUID, str]) -> ModelType:
        """ID로 엔티티 조회 (없으면 예외)"""
        entity = self.get(id)
        if not entity:
            raise NotFoundError(f"{self.model.__name__} with id {id} not found")
        return entity
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[ModelType]:
        """모든 엔티티 조회"""
        try:
            query = self.db.query(self.model)
            
            # 정렬
            if order_by and hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                query = query.order_by(desc(order_column) if order_desc else asc(order_column))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting all {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to get {self.model.__name__} list")
    
    def count(self, **filters) -> int:
        """엔티티 개수 조회"""
        try:
            query = self.db.query(self.model)
            query = self._apply_filters(query, filters)
            return query.count()
        except SQLAlchemyError as e:
            self.logger.error(f"Error counting {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to count {self.model.__name__}")
    
    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """엔티티 생성"""
        try:
            # Pydantic 모델을 dict로 변환
            if isinstance(obj_in, BaseModel):
                obj_data = obj_in.model_dump(exclude_unset=True)
            else:
                obj_data = obj_in
            
            # 모델 인스턴스 생성
            db_obj = self.model(**obj_data)
            
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            
            self.logger.info(f"Created {self.model.__name__} with id {db_obj.id}")
            return db_obj
            
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"Integrity error creating {self.model.__name__}: {e}")
            raise ConflictError(f"Duplicate or constraint violation for {self.model.__name__}")
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Error creating {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to create {self.model.__name__}")
    
    def update(
        self,
        id: Union[UUID, str],
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Optional[ModelType]:
        """엔티티 업데이트"""
        try:
            db_obj = self.get_or_404(id)
            
            # 업데이트 데이터 준비
            if isinstance(obj_in, BaseModel):
                update_data = obj_in.model_dump(exclude_unset=True)
            else:
                update_data = obj_in
            
            # 필드 업데이트
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            # updated_at 자동 갱신 (있는 경우)
            if hasattr(db_obj, 'updated_at'):
                db_obj.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(db_obj)
            
            self.logger.info(f"Updated {self.model.__name__} with id {id}")
            return db_obj
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Error updating {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to update {self.model.__name__}")
    
    def delete(self, id: Union[UUID, str]) -> bool:
        """엔티티 삭제"""
        try:
            db_obj = self.get_or_404(id)
            self.db.delete(db_obj)
            self.db.commit()
            
            self.logger.info(f"Deleted {self.model.__name__} with id {id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Error deleting {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to delete {self.model.__name__}")
    
    def find_by(self, **filters) -> List[ModelType]:
        """필터로 엔티티 검색"""
        try:
            query = self.db.query(self.model)
            query = self._apply_filters(query, filters)
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error finding {self.model.__name__} by filters: {e}")
            raise DatabaseError(f"Failed to find {self.model.__name__}")
    
    def find_one_by(self, **filters) -> Optional[ModelType]:
        """필터로 단일 엔티티 검색"""
        try:
            query = self.db.query(self.model)
            query = self._apply_filters(query, filters)
            return query.first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error finding one {self.model.__name__} by filters: {e}")
            raise DatabaseError(f"Failed to find {self.model.__name__}")
    
    def exists(self, **filters) -> bool:
        """엔티티 존재 여부 확인"""
        try:
            query = self.db.query(self.model)
            query = self._apply_filters(query, filters)
            return query.first() is not None
        except SQLAlchemyError as e:
            self.logger.error(f"Error checking existence of {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to check existence of {self.model.__name__}")
    
    def bulk_create(self, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """여러 엔티티 일괄 생성"""
        try:
            db_objs = []
            for obj_in in objs_in:
                if isinstance(obj_in, BaseModel):
                    obj_data = obj_in.model_dump(exclude_unset=True)
                else:
                    obj_data = obj_in
                
                db_obj = self.model(**obj_data)
                db_objs.append(db_obj)
            
            self.db.bulk_save_objects(db_objs)
            self.db.commit()
            
            self.logger.info(f"Bulk created {len(db_objs)} {self.model.__name__} objects")
            return db_objs
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to bulk create {self.model.__name__}")
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """여러 엔티티 일괄 업데이트"""
        try:
            updated_count = 0
            for update in updates:
                id = update.pop('id', None)
                if id and self.update(id, update):
                    updated_count += 1
            
            self.logger.info(f"Bulk updated {updated_count} {self.model.__name__} objects")
            return updated_count
            
        except Exception as e:
            self.logger.error(f"Error bulk updating {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to bulk update {self.model.__name__}")
    
    def _apply_filters(self, query: Query, filters: Dict[str, Any]) -> Query:
        """쿼리에 필터 적용"""
        for key, value in filters.items():
            if hasattr(self.model, key):
                column = getattr(self.model, key)
                
                # 특수 필터 처리
                if key.endswith('__in') and isinstance(value, list):
                    actual_key = key[:-4]
                    if hasattr(self.model, actual_key):
                        column = getattr(self.model, actual_key)
                        query = query.filter(column.in_(value))
                elif key.endswith('__gte'):
                    actual_key = key[:-5]
                    if hasattr(self.model, actual_key):
                        column = getattr(self.model, actual_key)
                        query = query.filter(column >= value)
                elif key.endswith('__lte'):
                    actual_key = key[:-5]
                    if hasattr(self.model, actual_key):
                        column = getattr(self.model, actual_key)
                        query = query.filter(column <= value)
                elif key.endswith('__like'):
                    actual_key = key[:-6]
                    if hasattr(self.model, actual_key):
                        column = getattr(self.model, actual_key)
                        query = query.filter(column.like(f"%{value}%"))
                elif value is None:
                    query = query.filter(column.is_(None))
                else:
                    query = query.filter(column == value)
        
        return query
    
    def paginate(
        self,
        page: int = 1,
        size: int = 20,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        **filters
    ) -> Dict[str, Any]:
        """페이지네이션된 결과 반환"""
        try:
            # 전체 개수
            total = self.count(**filters)
            
            # 페이지 계산
            pages = (total + size - 1) // size
            offset = (page - 1) * size
            
            # 쿼리 생성
            query = self.db.query(self.model)
            query = self._apply_filters(query, filters)
            
            # 정렬
            if order_by and hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                query = query.order_by(desc(order_column) if order_desc else asc(order_column))
            
            # 페이지네이션
            items = query.offset(offset).limit(size).all()
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "pages": pages
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error paginating {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to paginate {self.model.__name__}")
    
    def refresh(self, obj: ModelType) -> ModelType:
        """객체 새로고침"""
        try:
            self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.logger.error(f"Error refreshing {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to refresh {self.model.__name__}")