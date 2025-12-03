from datetime import datetime
from typing import List, Optional
from enum import Enum
from sqlalchemy import Column, DateTime, func, text,UniqueConstraint
from sqlmodel import Field, select

from bisheng.database.base import session_getter, async_session_getter
from bisheng.database.models.base import SQLModelSerializable


# 收藏资源类型枚举
class FavoriteType(Enum):
    ASSISTANT = 5
    FLOW = 10
    MODEL = 1
    SESSION = 15

DEFAULT_FAVORITE_NAME = '默认收藏'
DEFAULT_FAVORITE_DESCRIPTION = '默认收藏'
DEFAULT_FAVORITE_IS_DEFAULT = 1

# 收藏表（只放收藏的基础信息）
class FavoriteBase(SQLModelSerializable):
    user_id: int = Field(index=True, description='收藏用户ID')
    name: str = Field(index=True, description='收藏名称')
    is_default: int = Field(default=0, description='是否默认收藏 0-否 1-是')
    description: Optional[str] = Field(default=None, description='收藏描述')
    create_time: Optional[datetime] = Field(default=None, sa_column=Column[datetime](
        DateTime, nullable=False, index=True, server_default=text('CURRENT_TIMESTAMP')))
    update_time: Optional[datetime] = Field(default=None, sa_column=Column[datetime](
        DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP')))


class Favorite(FavoriteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description='收藏ID')



# 收藏资源关联表（放收藏的资源和资源类型）
class FavoriteResourceBase(SQLModelSerializable):
    favorite_id: int = Field(index=True, description='收藏ID')
    resource_type: int = Field(index=True, description='资源类型')
    resource_id: str = Field(index=True, description='资源ID')
    create_time: Optional[datetime] = Field(default=None, sa_column=Column[datetime](
        DateTime, nullable=False, index=True, server_default=text('CURRENT_TIMESTAMP')))


class FavoriteResource(FavoriteResourceBase, table=True):
    __table_args__ = (UniqueConstraint('resource_id', 'resource_type', 'favorite_id', name='resource_tag_uniq'),)
    id: Optional[int] = Field(default=None, primary_key=True, description='收藏资源关联ID')










class FavoriteDao(FavoriteBase):
    """
    收藏数据访问对象
    """

    @classmethod
    def create_favorite(cls, favorite: Favorite) -> Favorite:
        """
        创建收藏
        """
        with session_getter() as session:
            session.add(favorite)
            session.commit()
            session.refresh(favorite)
            return favorite

    @classmethod
    def update_favorite(cls, favorite_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Favorite | None:
        """
        更新收藏
        """
        with session_getter() as session:
            statement = select(Favorite).where(Favorite.id == favorite_id)
            favorite = session.exec(statement).first()
            if favorite:
                if name:
                    favorite.name = name
                if description:
                    favorite.description = description
                session.commit()
                session.refresh(favorite)
                return favorite
            return None

    @classmethod
    def delete_favorite(cls, favorite_id: int) -> bool:
        """
        删除收藏
        """
        with session_getter() as session:
            # 删除收藏及其关联的资源
            statement = select(Favorite).where(Favorite.id == favorite_id)
            favorite = session.exec(statement).first()
            if favorite:
                # 删除关联的资源
                session.exec(select(FavoriteResource).where(FavoriteResource.favorite_id == favorite_id)).all()
                # 删除收藏
                session.delete(favorite)
                session.commit()
                return True
            return False

    @classmethod
    def get_favorite(cls, favorite_id: int) -> Favorite | None:
        """
        获取收藏
        """
        with session_getter() as session:
            statement = select(Favorite).where(Favorite.id == favorite_id)
            return session.exec(statement).first()
    @classmethod     
    def get_favorite_default(cls,user_id:int)->Favorite:
        """
        获取用户默认收藏
        """
        with session_getter() as session:
            statement = select(Favorite).where(Favorite.user_id == user_id,Favorite.is_default == DEFAULT_FAVORITE_IS_DEFAULT)
            data = session.exec(statement).first()
            if data:
                return data
            # 如果没有默认收藏，创建一个
            default_favorite = Favorite(
                user_id=user_id,
                name=DEFAULT_FAVORITE_NAME,
                description=DEFAULT_FAVORITE_DESCRIPTION,
                is_default=DEFAULT_FAVORITE_IS_DEFAULT
            )
            session.add(default_favorite)
            session.commit()
            session.refresh(default_favorite)
            return default_favorite
    
    @classmethod
    def get_favorites_by_user(cls, user_id: int, keyword: Optional[str] = None, page: int = 1, limit: int = 10) -> (List[Favorite], int):
        """
        获取用户收藏列表
        """
        statement = select(Favorite).where(Favorite.user_id == user_id)
        if keyword:
            statement = statement.where(Favorite.name.like(f'%{keyword}%'))
        count_statement = select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        if keyword:
            count_statement = count_statement.where(Favorite.name.like(f'%{keyword}%'))
        
        if page and limit:
            statement = statement.offset((page - 1) * limit).limit(limit)
        statement = statement.order_by(Favorite.create_time.desc())
        
        with session_getter() as session:
            return session.exec(statement).all(), session.scalar(count_statement)

    @classmethod
    def search_favorites(cls, user_id: int, keyword: str, page: int = 1, limit: int = 10) -> (List[Favorite], int):
        """
        搜索收藏
        """
        statement = select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.name.like(f'%{keyword}%')
        )
        count_statement = select(func.count(Favorite.id)).where(
            Favorite.user_id == user_id,
            Favorite.name.like(f'%{keyword}%')
        )
        
        if page and limit:
            statement = statement.offset((page - 1) * limit).limit(limit)
        statement = statement.order_by(Favorite.create_time.desc())
        
        with session_getter() as session:
            return session.exec(statement).all(), session.scalar(count_statement)

    @classmethod
    async def acreate_favorite(cls, favorite: Favorite) -> Favorite:
        """
        异步创建收藏
        """
        async with async_session_getter() as session:
            session.add(favorite)
            await session.commit()
            await session.refresh(favorite)
            return favorite

    @classmethod
    async def aupdate_favorite(cls, favorite_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Favorite | None:
        """
        异步更新收藏
        """
        async with async_session_getter() as session:
            statement = select(Favorite).where(Favorite.id == favorite_id)
            favorite = await session.exec(statement)
            favorite = favorite.first()
            if favorite:
                if name:
                    favorite.name = name
                if description:
                    favorite.description = description
                await session.commit()
                await session.refresh(favorite)
                return favorite
            return None

    @classmethod
    async def adelete_favorite(cls, favorite_id: int) -> bool:
        """
        异步删除收藏
        """
        async with async_session_getter() as session:
            # 删除收藏及其关联的资源
            statement = select(Favorite).where(Favorite.id == favorite_id)
            favorite = await session.exec(statement)
            favorite = favorite.first()
            if favorite:
                # 删除关联的资源
                await session.exec(select(FavoriteResource).where(FavoriteResource.favorite_id == favorite_id))
                # 删除收藏
                await session.delete(favorite)
                await session.commit()
                return True
            return False

    @classmethod
    async def aget_favorite(cls, favorite_id: int) -> Favorite | None:
        """
        异步获取收藏
        """
        async with async_session_getter() as session:
            statement = select(Favorite).where(Favorite.id == favorite_id)
            result = await session.exec(statement)
            return result.first()

    @classmethod
    async def aget_favorites_by_user(cls, user_id: int, keyword: Optional[str] = None, page: int = 1, limit: int = 10) -> (List[Favorite], int):
        """
        异步获取用户收藏列表
        """
        statement = select(Favorite).where(Favorite.user_id == user_id)
        if keyword:
            statement = statement.where(Favorite.name.like(f'%{keyword}%'))
        count_statement = select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        if keyword:
            count_statement = count_statement.where(Favorite.name.like(f'%{keyword}%'))
        
        if page and limit:
            statement = statement.offset((page - 1) * limit).limit(limit)
        statement = statement.order_by(Favorite.create_time.desc())
        
        async with async_session_getter() as session:
            result = await session.exec(statement)
            favorites = result.all()
            count = await session.scalar(count_statement)
            return favorites, count

    @classmethod
    async def asearch_favorites(cls, user_id: int, keyword: str, page: int = 1, limit: int = 10) -> (List[Favorite], int):
        """
        异步搜索收藏
        """
        statement = select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.name.like(f'%{keyword}%')
        )
        count_statement = select(func.count(Favorite.id)).where(
            Favorite.user_id == user_id,
            Favorite.name.like(f'%{keyword}%')
        )
        
        if page and limit:
            statement = statement.offset((page - 1) * limit).limit(limit)
        statement = statement.order_by(Favorite.create_time.desc())
        
        async with async_session_getter() as session:
            result = await session.exec(statement)
            favorites = result.all()
            count = await session.scalar(count_statement)
            return favorites, count


class FavoriteResourceDao(FavoriteResourceBase):
    """
    收藏资源关联数据访问对象
    """

    @classmethod
    def add_resource(cls, favorite_resource: FavoriteResource) -> FavoriteResource:
        """
        添加收藏资源
        """
        with session_getter() as session:
            session.add(favorite_resource)
            session.commit()
            session.refresh(favorite_resource)
            return favorite_resource

    @classmethod
    def remove_resource(cls, favorite_id: int, resource_type: int, resource_id: str) -> bool:
        """
        移除收藏资源
        """
        with session_getter() as session:
            statement = select(FavoriteResource).where(
                FavoriteResource.favorite_id == favorite_id,
                FavoriteResource.resource_type == resource_type,
                FavoriteResource.resource_id == resource_id
            )
            favorite_resource = session.exec(statement).first()
            if favorite_resource:
                session.delete(favorite_resource)
                session.commit()
                return True
            return False

    @classmethod
    def remove_resources_by_favorite(cls, favorite_id: int) -> bool:
        """
        移除收藏的所有资源
        """
        with session_getter() as session:
            session.exec(select(FavoriteResource).where(FavoriteResource.favorite_id == favorite_id)).all()
            session.commit()
            return True

    @classmethod
    def get_resources_by_favorite(cls, favorite_id: int, resource_type: Optional[str] = None, page: int = 1, limit: int = 10) -> (List[FavoriteResource], int):
        """
        获取收藏的资源列表
        """
        statement = select(FavoriteResource).where(FavoriteResource.favorite_id == favorite_id)
        if resource_type:
            statement = statement.where(FavoriteResource.resource_type == resource_type)
        count_statement = select(func.count(FavoriteResource.id)).where(FavoriteResource.favorite_id == favorite_id)
        if resource_type:
            count_statement = count_statement.where(FavoriteResource.resource_type == resource_type)
        
        if page and limit:
            statement = statement.offset((page - 1) * limit).limit(limit)
        statement = statement.order_by(FavoriteResource.create_time.desc())
        
        with session_getter() as session:
            return session.exec(statement).all(), session.scalar(count_statement)

    @classmethod
    def check_resource_in_favorite(cls, favorite_id: int, resource_type: int, resource_id: str) -> bool:
        """
        检查资源是否已在收藏中
        """
        with session_getter() as session:
            statement = select(FavoriteResource).where(
                FavoriteResource.favorite_id == favorite_id,
                FavoriteResource.resource_type == resource_type,
                FavoriteResource.resource_id == resource_id
            )
            favorite_resource = session.exec(statement).first()
            return favorite_resource is not None

    @classmethod
    def get_favorites_by_resource(cls, resource_type: int, resource_id: str) -> List[FavoriteResource]:
        """
        获取资源所在的所有收藏
        """
        with session_getter() as session:
            statement = select(FavoriteResource).where(
                FavoriteResource.resource_type == resource_type,
                FavoriteResource.resource_id == resource_id
            )
            return session.exec(statement).all()

    @classmethod
    async def aadd_resource(cls, favorite_resource: FavoriteResource) -> FavoriteResource:
        """
        异步添加收藏资源
        """
        async with async_session_getter() as session:
            session.add(favorite_resource)
            await session.commit()
            await session.refresh(favorite_resource)
            return favorite_resource

    @classmethod
    async def aremove_resource(cls, favorite_id: int, resource_type: int, resource_id: str) -> bool:
        """
        异步移除收藏资源
        """
        async with async_session_getter() as session:
            statement = select(FavoriteResource).where(
                FavoriteResource.favorite_id == favorite_id,
                FavoriteResource.resource_type == resource_type,
                FavoriteResource.resource_id == resource_id
            )
            favorite_resource = await session.exec(statement)
            favorite_resource = favorite_resource.first()
            if favorite_resource:
                await session.delete(favorite_resource)
                await session.commit()
                return True
            return False

    @classmethod
    async def aremove_resources_by_favorite(cls, favorite_id: int) -> bool:
        """
        异步移除收藏的所有资源
        """
        async with async_session_getter() as session:
            await session.exec(select(FavoriteResource).where(FavoriteResource.favorite_id == favorite_id))
            await session.commit()
            return True

    @classmethod
    async def aget_resources_by_favorite(cls, favorite_id: int, resource_type: Optional[str] = None, page: int = 1, limit: int = 10) -> (List[FavoriteResource], int):
        """
        异步获取收藏的资源列表
        """
        statement = select(FavoriteResource).where(FavoriteResource.favorite_id == favorite_id)
        if resource_type:
            statement = statement.where(FavoriteResource.resource_type == resource_type)
        count_statement = select(func.count(FavoriteResource.favorite_resource_id)).where(FavoriteResource.favorite_id == favorite_id)
        if resource_type:
            count_statement = count_statement.where(FavoriteResource.resource_type == resource_type)
        
        if page and limit:
            statement = statement.offset((page - 1) * limit).limit(limit)
        statement = statement.order_by(FavoriteResource.create_time.desc())
        
        async with async_session_getter() as session:
            result = await session.exec(statement)
            resources = result.all()
            count = await session.scalar(count_statement)
            return resources, count

    @classmethod
    async def acheck_resource_in_favorite(cls, favorite_id: int, resource_type: int, resource_id: str) -> bool:
        """
        异步检查资源是否已在收藏中
        """
        async with async_session_getter() as session:
            statement = select(FavoriteResource).where(
                FavoriteResource.favorite_id == favorite_id,
                FavoriteResource.resource_type == resource_type,
                FavoriteResource.resource_id == resource_id
            )
            favorite_resource = await session.exec(statement)
            favorite_resource = favorite_resource.first()
            return favorite_resource is not None

    @classmethod
    async def aget_favorites_by_resource(cls, resource_type: int, resource_id: str) -> List[FavoriteResource]:
        """
        异步获取资源所在的所有收藏
        """
        async with async_session_getter() as session:
            statement = select(FavoriteResource).where(
                FavoriteResource.resource_type == resource_type,
                FavoriteResource.resource_id == resource_id
            )
            result = await session.exec(statement)
            return result.all()