from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Query, Body
from bisheng.api.services.session_category_service import SessionCategoryService
from bisheng.api.services.user_service import UserPayload, get_login_user
from bisheng.api.v1.schemas import UnifiedResponseModel, resp_200
from bisheng.api.v1.schema.session_category_schema import (
    SessionCategoryCreate,
    SessionCategoryUpdate,
    SessionCategoryResponse,
    SessionCategoryRelationRequest,
    SessionWithCategories
)

router = APIRouter(prefix='/session/category', tags=['Session Category'])


@router.get('')
def get_user_categories(
    request: Request,
    login_user: UserPayload = Depends(get_login_user),
    keyword: Optional[str] = Query(default=None, description='搜索关键字'),
    page: int = Query(default=0, description='页码'),
    limit: int = Query(default=10, description='每页条数')
):
    """
    获取用户的所有会话分类
    """
    categories, total = SessionCategoryService.get_user_categories(request, login_user, keyword, page, limit)
    # 转换为响应模型
    category_responses = [
        SessionCategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            user_id=cat.user_id,
            created_at=cat.created_at.isoformat() if cat.created_at else None,
            updated_at=cat.updated_at.isoformat() if cat.updated_at else None
        ) for cat in categories
    ]
    return resp_200(data={
        'categories': category_responses,
        'total': total
    })


@router.get('/{category_id}')
def get_category(
    request: Request,
    category_id: int,
    login_user: UserPayload = Depends(get_login_user)
):
    """
    根据ID获取分类详情
    """
    category = SessionCategoryService.get_category_by_id(request, login_user, category_id)
    return resp_200(data=SessionCategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        user_id=category.user_id,
        created_at=category.created_at.isoformat() if category.created_at else None,
        updated_at=category.updated_at.isoformat() if category.updated_at else None
    ))


@router.post('')
def create_category(
    request: Request,
    category_data: SessionCategoryCreate = Body(..., description='创建分类的数据'),
    login_user: UserPayload = Depends(get_login_user)
):
    """
    创建新的会话分类
    """
    category = SessionCategoryService.create_category(
        request, login_user, category_data.name, category_data.description
    )
    return resp_200(data=SessionCategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        user_id=category.user_id,
        created_at=category.create_time.isoformat() if category.create_time else None,
        updated_at=category.update_time.isoformat() if category.update_time else None
    ))


@router.put('')
def update_category(
    request: Request,
    category_data: SessionCategoryUpdate = Body(..., description='更新分类的数据'),
    login_user: UserPayload = Depends(get_login_user)
):
    """
    更新会话分类信息
    """
    category = SessionCategoryService.update_category(
        request, login_user, category_data.category_id,
        category_data.name, category_data.description
    )
    return resp_200(data=SessionCategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        user_id=category.user_id,
        created_at=category.create_time.isoformat() if category.create_time else None,
        updated_at=category.update_time.isoformat() if category.update_time else None
    ))


@router.delete('/{category_id}')
def delete_category(
    request: Request,
    category_id: int,
    login_user: UserPayload = Depends(get_login_user)
):
    """
    删除会话分类
    """
    SessionCategoryService.delete_category(request, login_user, category_id)
    return resp_200()


@router.post('/relation')
def add_session_to_category(
    request: Request,
    relation_data: SessionCategoryRelationRequest = Body(..., description='关联数据'),
    login_user: UserPayload = Depends(get_login_user)
):
    """
    将会话添加到分类
    """
    relation = SessionCategoryService.add_session_to_category(
        request, login_user, relation_data.category_id, relation_data.session_id
    )
    return resp_200(data={
        'category_id': relation.category_id,
        'session_id': relation.session_id
    })


@router.delete('/relation')
def remove_session_from_category(
    request: Request,
    category_id: int = Query(..., description='分类ID'),
    session_id: str = Query(..., description='会话ID'),
    login_user: UserPayload = Depends(get_login_user)
):
    """
    将会话从分类中移除
    """
    SessionCategoryService.remove_session_from_category(request, login_user, category_id, session_id)
    return resp_200()


@router.get('/{category_id}/sessions')
def get_sessions_by_category(
    request: Request,
    category_id: int,
    login_user: UserPayload = Depends(get_login_user)
):
    """
    获取分类下的所有会话ID
    """
    session_ids = SessionCategoryService.get_sessions_by_category(request, login_user, category_id)
    return resp_200(data={'session_ids': session_ids})


@router.get('/session/{session_id}/categories')
def get_categories_by_session(
    request: Request,
    session_id: str,
    login_user: UserPayload = Depends(get_login_user)
):
    """
    获取会话所属的所有分类
    """
    categories = SessionCategoryService.get_categories_by_session(request, login_user, session_id)
    # 转换为响应模型
    category_responses = [
        SessionCategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            user_id=cat.user_id,
            created_at=cat.created_at.isoformat() if cat.created_at else None,
            updated_at=cat.updated_at.isoformat() if cat.updated_at else None
        ) for cat in categories
    ]
    return resp_200(data=SessionWithCategories(
        session_id=session_id,
        categories=category_responses
    ))