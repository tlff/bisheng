from typing import Optional, List
from pydantic import BaseModel


class SessionCategoryCreate(BaseModel):
    """创建会话分类的请求模型"""
    name: str
    description: Optional[str] = None


class SessionCategoryUpdate(BaseModel):
    """更新会话分类的请求模型"""
    category_id: int
    name: Optional[str] = None
    description: Optional[str] = None


class SessionCategoryResponse(BaseModel):
    """会话分类的响应模型"""
    id: int
    name: str
    description: Optional[str] = None
    user_id: int
    created_at: str
    updated_at: str


class SessionCategoryRelationRequest(BaseModel):
    """关联会话和分类的请求模型"""
    category_id: int
    session_id: str


class SessionCategoryListResponse(BaseModel):
    """会话分类列表的响应模型"""
    categories: List[SessionCategoryResponse]
    total: int


class SessionWithCategories(BaseModel):
    """带有分类信息的会话响应模型"""
    session_id: str
    categories: List[SessionCategoryResponse]