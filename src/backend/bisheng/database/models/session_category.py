from datetime import datetime
from typing import Optional, List

from sqlmodel import Field, Column, DateTime, text, ForeignKey, select, func

from bisheng.database.base import session_getter, async_session_getter
from bisheng.database.models.base import SQLModelSerializable


class SessionCategoryBase(SQLModelSerializable):
    """ 会话分类表 """
    id: Optional[int] = Field(default=None, primary_key=True, description='分类ID')
    user_id: int = Field(index=True, description='所属用户ID')
    name: str = Field(index=True, description='分类名称')
    description: Optional[str] = Field(default=None, description='分类描述')
    color: Optional[str] = Field(default='#1890ff', description='分类颜色标识')
    icon: Optional[str] = Field(default=None, description='分类图标')
    sort_order: Optional[int] = Field(default=0, description='排序顺序')
    is_default: Optional[bool] = Field(default=False, description='是否默认分类')
    create_time: Optional[datetime] = Field(default=None, sa_column=Column(
        DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP')))
    update_time: Optional[datetime] = Field(default=None, sa_column=Column(
        DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'),
        onupdate=text('CURRENT_TIMESTAMP')))


class SessionCategory(SessionCategoryBase, table=True):
    __tablename__ = 'session_category'


class SessionCategoryRelationBase(SQLModelSerializable):
    """ 会话分类关联表 """
    id: Optional[int] = Field(default=None, primary_key=True, description='关联ID')
    category_id: int = Field(ForeignKey('session_category.id'), index=True, description='分类ID')
    chat_id: str = Field(index=True, description='会话ID')
    create_time: Optional[datetime] = Field(default=None, sa_column=Column(
        DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP')))


class SessionCategoryRelation(SessionCategoryRelationBase, table=True):
    __tablename__ = 'session_category_relation'


class SessionCategoryDao(SessionCategoryBase):
    """ 会话分类数据访问对象 """

    @classmethod
    def insert_one(cls, data: SessionCategory) -> SessionCategory:
        with session_getter() as session:
            session.add(data)
            session.commit()
            session.refresh(data)
            return data

    @classmethod
    async def async_insert_one(cls, data: SessionCategory) -> SessionCategory:
        async with async_session_getter() as session:
            session.add(data)
            await session.commit()
            await session.refresh(data)
            return data

    @classmethod
    def get_by_id(cls, category_id: int) -> SessionCategory | None:
        statement = select(SessionCategory).where(SessionCategory.id == category_id)
        with session_getter() as session:
            return session.exec(statement).first()

    @classmethod
    def get_user_categories(cls, user_id: int) -> List[SessionCategory]:
        statement = select(SessionCategory).where(
            SessionCategory.user_id == user_id
        ).order_by(SessionCategory.sort_order, SessionCategory.create_time)
        with session_getter() as session:
            return session.exec(statement).all()

    @classmethod
    def update_category(cls, category_id: int, update_data: dict):
        statement = select(SessionCategory).where(SessionCategory.id == category_id)
        with session_getter() as session:
            category = session.exec(statement).first()
            if category:
                for key, value in update_data.items():
                    if hasattr(category, key):
                        setattr(category, key, value)
                session.commit()
                session.refresh(category)
                return category
            return None

    @classmethod
    def delete_category(cls, category_id: int):
        with session_getter() as session:
            # 先删除关联关系
            relation_statement = select(SessionCategoryRelation).where(
                SessionCategoryRelation.category_id == category_id
            )
            relations = session.exec(relation_statement).all()
            for relation in relations:
                session.delete(relation)
            
            # 再删除分类
            category = session.exec(select(SessionCategory).where(
                SessionCategory.id == category_id
            )).first()
            if category:
                session.delete(category)
            session.commit()


class SessionCategoryRelationDao(SessionCategoryRelationBase):
    """ 会话分类关联数据访问对象 """

    @classmethod
    def add_session_to_category(cls, category_id: int, chat_id: str) -> SessionCategoryRelation:
        with session_getter() as session:
            # 检查是否已存在关联
            existing = session.exec(select(SessionCategoryRelation).where(
                SessionCategoryRelation.category_id == category_id,
                SessionCategoryRelation.chat_id == chat_id
            )).first()
            
            if existing:
                return existing
            
            relation = SessionCategoryRelation(category_id=category_id, chat_id=chat_id)
            session.add(relation)
            session.commit()
            session.refresh(relation)
            return relation

    @classmethod
    def remove_session_from_category_chat(cls, category_id: int, chat_id: str):
        with session_getter() as session:
            relation = session.exec(select(SessionCategoryRelation).where(
                SessionCategoryRelation.category_id == category_id,
                SessionCategoryRelation.chat_id == chat_id
            )).first()
            
            if relation:
                session.delete(relation)
                session.commit()
    @classmethod
    def remove_session_from_category(cls, category_id: int):
        with session_getter() as session:
            relation = session.exec(select(SessionCategoryRelation).where(
                SessionCategoryRelation.category_id == category_id
            )).first()
            
            if relation:
                session.delete(relation)
                session.commit()

    @classmethod
    def get_session_categories(cls, chat_id: str) -> List[int]:
        statement = select(SessionCategoryRelation.category_id).where(
            SessionCategoryRelation.chat_id == chat_id
        )
        with session_getter() as session:
            return [row[0] for row in session.exec(statement).all()]

    @classmethod
    def get_category_sessions(cls, category_id: int, page: int = 0, limit: int = 0) -> List[str]:
        statement = select(SessionCategoryRelation.chat_id).where(
            SessionCategoryRelation.category_id == category_id
        ).order_by(SessionCategoryRelation.create_time.desc())
        
        if page and limit:
            statement = statement.offset((page - 1) * limit).limit(limit)
            
        with session_getter() as session:
            return [row[0] for row in session.exec(statement).all()]

    @classmethod
    def get_category_session_count(cls, category_id: int) -> int:
        statement = select(func.count(SessionCategoryRelation.id)).where(
            SessionCategoryRelation.category_id == category_id
        )
        with session_getter() as session:
            return session.scalar(statement)

    @classmethod
    def update_session_categories(cls, chat_id: str, category_ids: List[int]):
        with session_getter() as session:
            # 删除现有关联
            existing_relations = session.exec(select(SessionCategoryRelation).where(
                SessionCategoryRelation.chat_id == chat_id
            )).all()
            for relation in existing_relations:
                session.delete(relation)
            
            # 添加新关联
            for category_id in category_ids:
                relation = SessionCategoryRelation(category_id=category_id, chat_id=chat_id)
                session.add(relation)
            
            session.commit()