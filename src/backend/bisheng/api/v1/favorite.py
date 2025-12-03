from typing import Optional, List
from fastapi import APIRouter, Request, Depends, Query, Body

from bisheng.api.services.favorite import FavoriteApiService
from bisheng.api.services.user_service import UserPayload, get_login_user
from bisheng.api.v1.schemas import resp_200
from bisheng.database.models.favorite import FavoriteType

router = APIRouter(prefix='/favorite', tags=['Favorite'])


# @router.post('')
def create_favorite(request: Request,
                   login_user: UserPayload = Depends(get_login_user),
                   resource_type: int = Body(..., embed=True, description='资源类型'),
                   resource_id: str = Body(..., embed=True, description='资源ID')):
    """创建收藏"""
    result = FavoriteApiService.create_favorite(request, login_user, resource_type, resource_id)
    return resp_200(result)


# @router.delete('')
def delete_favorite(request: Request,
                   login_user: UserPayload = Depends(get_login_user),
                   resource_type: int = Body(..., embed=True, description='资源类型'),
                   resource_id: str = Body(..., embed=True, description='资源ID')):
    """删除收藏"""
    result = FavoriteApiService.delete_favorite(request, login_user, resource_type, resource_id)
    return resp_200(result)


# @router.get('/check')
def check_favorite(request: Request,
                  login_user: UserPayload = Depends(get_login_user),
                  resource_type: int = Query(..., description='资源类型'),
                  resource_id: str = Query(..., description='资源ID')):
    """检查是否已收藏"""
    result = FavoriteApiService.check_favorite(request, login_user, resource_type, resource_id)
    return resp_200(result)


# @router.post('/batch/check')
def batch_check_favorites(request: Request,
                         login_user: UserPayload = Depends(get_login_user),
                         resource_type: int = Body(..., embed=True, description='资源类型'),
                         resource_ids: List[str] = Body(..., embed=True, description='资源ID列表')):
    """批量检查收藏状态"""
    result = FavoriteApiService.batch_check_favorites(request, login_user, resource_type, resource_ids)
    return resp_200(result)


# @router.get('')
def get_user_favorites(request: Request,
                      login_user: UserPayload = Depends(get_login_user),
                      resource_type: Optional[str] = Query(None, description='资源类型'),
                      page: int = Query(default=1, description='页码'),
                      limit: int = Query(default=10, description='每页条数')):
    """获取用户收藏列表"""
    result = FavoriteApiService.get_user_favorites(request, login_user, resource_type, page, limit)
    return resp_200(result)


# 默认收藏夹相关接口

@router.post('/default')
def add_to_default_favorite(request: Request,
                           login_user: UserPayload = Depends(get_login_user),
                           resource_type: int = Body(..., embed=True, description='资源类型'),
                           resource_id: str = Body(..., embed=True, description='资源ID')):
    """将资源添加到默认收藏夹，如果默认收藏夹不存在就创建一个"""
    result = FavoriteApiService.add_to_default_favorite(request, login_user, resource_type, resource_id)
    return resp_200(result)


@router.delete('/default')
def remove_from_default_favorite(request: Request,
                              login_user: UserPayload = Depends(get_login_user),
                              resource_type: int = Body(..., embed=True, description='资源类型'),
                              resource_id: str = Body(..., embed=True, description='资源ID')):
    """从默认收藏夹中删除资源"""
    result = FavoriteApiService.remove_from_default_favorite(request, login_user, resource_type, resource_id)
    return resp_200(result)


@router.get('/default')
def get_default_favorite_resources(request: Request,
                                  login_user: UserPayload = Depends(get_login_user),
                                  resource_type: Optional[str] = Query(None, description='资源类型'),
                                  page: int = Query(default=1, description='页码'),
                                  limit: int = Query(default=10, description='每页条数')):
    """获取默认收藏夹中的所有资源列表"""
    result = FavoriteApiService.get_default_favorite_resources(request, login_user, resource_type, page, limit)
    return resp_200(result)