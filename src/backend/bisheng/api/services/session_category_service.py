from typing import List, Tuple, Optional
from bisheng.api.services.user_service import UserPayload
from bisheng.database.base import session_getter
from bisheng.database.models.session_category import SessionCategoryDao, SessionCategoryRelationDao
from bisheng.database.models.session_category import SessionCategory, SessionCategoryRelation
from bisheng.api.errcode.http_error import NotFoundError, UnAuthorizedError


class SessionCategoryService:
    """会话分类服务类"""

    @staticmethod
    def create_category(request, user: UserPayload, name: str, description: Optional[str] = None) -> SessionCategory:
        """创建会话分类"""
       
        category = SessionCategory(
            name=name,
            description=description,
            user_id=user.user_id
        )
        return SessionCategoryDao.insert_one(category)

    @staticmethod
    def update_category(request, user: UserPayload, category_id: int, 
                      name: Optional[str] = None, description: Optional[str] = None) -> SessionCategory:
        """更新会话分类"""
        category = SessionCategoryDao.get_by_id( category_id)
        if not category:
            raise NotFoundError(f"分类ID {category_id} 不存在")
        
        # 检查权限，只有创建者可以修改
        if category.user_id != user.user_id and not user.is_admin():
            raise UnAuthorizedError("无权修改此分类")
        
        update_data = {}
        if name is not None:
            update_data['name'] = name
        if description is not None:
            update_data['description'] = description
        
        return SessionCategoryDao.update_category(category_id, update_data)

    @staticmethod
    def delete_category(request, user: UserPayload, category_id: int) -> None:
        """删除会话分类"""
        category = SessionCategoryDao.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"分类ID {category_id} 不存在")
        
        # 检查权限，只有创建者可以删除
        if category.user_id != user.user_id and not user.is_admin():
            raise UnAuthorizedError("无权删除此分类")
        
        # 先删除关联关系
        SessionCategoryRelationDao.remove_session_from_category(category_id)
        # 删除分类
        SessionCategoryDao.delete_category(category_id)

    @staticmethod
    def get_user_categories(request, user: UserPayload, keyword: Optional[str] = None, 
                           page: int = 0, limit: int = 10) -> Tuple[List[SessionCategory], int]:
        """获取用户的所有会话分类"""
        with session_getter() as db:
            categories, total = SessionCategoryDao.get_user_categories(
                db, user.user_id, keyword, page, limit
            )
            return categories, total

    @staticmethod
    def get_category_by_id(request, user: UserPayload, category_id: int) -> SessionCategory:
        """根据ID获取分类"""
        with session_getter() as db:
            category = SessionCategoryDao.get_by_id(db, category_id)
            if not category:
                raise NotFoundError(f"分类ID {category_id} 不存在")
            
            # 检查权限，只有创建者或管理员可以查看
            if category.user_id != user.user_id and not user.is_admin():
                raise UnAuthorizedError("无权查看此分类")
            
            return category

    @staticmethod
    def add_session_to_category(request, user: UserPayload, category_id: int, session_id: str) -> SessionCategoryRelation:
        """将会话添加到分类"""
        with session_getter() as db:
            # 验证分类是否存在且属于用户
            category = SessionCategoryDao.get_by_id(db, category_id)
            if not category:
                raise NotFoundError(f"分类ID {category_id} 不存在")
            
            if category.user_id != user.user_id and not user.is_admin():
                raise UnAuthorizedError("无权操作此分类")
            
            # 检查关联是否已存在
            existing = SessionCategoryRelationDao.get_by_category_and_session(db, category_id, session_id)
            if existing:
                return existing
            
            # 创建关联关系
            relation = SessionCategoryRelation(
                category_id=category_id,
                session_id=session_id
            )
            return SessionCategoryRelationDao.insert_one(db, relation)

    @staticmethod
    def remove_session_from_category(request, user: UserPayload, category_id: int, session_id: str) -> None:
        """将会话从分类中移除"""
        with session_getter() as db:
            # 验证分类是否存在且属于用户
            category = SessionCategoryDao.get_by_id(db, category_id)
            if not category:
                raise NotFoundError(f"分类ID {category_id} 不存在")
            
            if category.user_id != user.user_id and not user.is_admin():
                raise UnAuthorizedError("无权操作此分类")
            
            # 删除关联关系
            deleted = SessionCategoryRelationDao.delete_by_category_and_session(db, category_id, session_id)
            if not deleted:
                raise NotFoundError("会话与分类的关联不存在")

    @staticmethod
    def get_sessions_by_category(request, user: UserPayload, category_id: int) -> List[str]:
        """获取分类下的所有会话ID"""
        with session_getter() as db:
            # 验证分类是否存在且属于用户
            category = SessionCategoryDao.get_by_id(db, category_id)
            if not category:
                raise NotFoundError(f"分类ID {category_id} 不存在")
            
            if category.user_id != user.user_id and not user.is_admin():
                raise UnAuthorizedError("无权查看此分类")
            
            relations = SessionCategoryRelationDao.get_by_category_id(db, category_id)
            return [relation.session_id for relation in relations]

    @staticmethod
    def get_categories_by_session(request, user: UserPayload, session_id: str) -> List[SessionCategory]:
        """获取会话所属的所有分类"""
        with session_getter() as db:
            relations = SessionCategoryRelationDao.get_by_session_id(db, session_id)
            category_ids = [relation.category_id for relation in relations]
            
            if not category_ids:
                return []
            
            # 获取所有分类，并过滤只返回用户有权限查看的
            categories = SessionCategoryDao.get_by_ids(db, category_ids)
            return [cat for cat in categories if cat.user_id == user.user_id or user.is_admin()]