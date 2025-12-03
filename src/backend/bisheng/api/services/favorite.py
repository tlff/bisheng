from typing import List, Optional, Dict, Any
from fastapi import Request
from loguru import logger

from bisheng.api.services.user_service import UserPayload
from bisheng.database.models.favorite import (
    Favorite,
    FavoriteDao,
    FavoriteResourceDao,
    FavoriteType,
    FavoriteResource,
)
from bisheng.api.errcode.favorite import (
    FavoriteNotFoundError,        # 15001 收藏不存在
    FavoriteAlreadyExistsError,   # 15002 资源已收藏
    FavoriteResourceNotFoundError, # 15003 收藏资源不存在
    FavoriteCreateError,          # 15010 创建收藏失败
    FavoriteDeleteError,          # 15011 删除收藏失败
    FavoriteCheckError,           # 15012 检查收藏状态失败
    FavoriteBatchCheckError,      # 15013 批量检查收藏状态失败
    FavoriteListError,            # 15014 获取收藏列表失败
)


class FavoriteApiService:
    """收藏夹API服务类"""

    @staticmethod
    def create_favorite(
        request: Request, login_user: UserPayload, resource_type: int, resource_id: str
    ) -> Favorite:
        """创建收藏"""
        try:
            # 检查是否已经收藏
            existing_favorites = FavoriteResourceDao.get_favorites_by_resource(
                resource_type, resource_id
            )
            user_favorite = None
            for fav_resource in existing_favorites:
                favorite = FavoriteDao.get_favorite(fav_resource.favorite_id)
                if favorite and favorite.user_id == login_user.user_id:
                    user_favorite = favorite
                    break

            if user_favorite:
                raise FavoriteAlreadyExistsError()

            # 创建收藏记录
            favorite = Favorite(
                user_id=login_user.user_id,
                name=f"收藏_{resource_type}_{resource_id}",
                description="",
                resource_type=resource_type,
                resource_id=resource_id,
            )
            favorite = FavoriteDao.create_favorite(favorite)

            # 创建收藏资源关联
            favorite_resource = FavoriteResource(
                favorite_id=favorite.id,
                resource_type=resource_type,
                resource_id=resource_id,
            )
            FavoriteResourceDao.add_resource(favorite_resource)

            logger.info(
                f"用户 {login_user.user_id} 收藏了 {resource_type}:{resource_id}"
            )
            return favorite

        except Exception as e:
            logger.error(f"创建收藏失败: {str(e)}")
            if isinstance(e, FavoriteAlreadyExistsError):
                raise e
            raise FavoriteCreateError(str(e))

    @staticmethod
    def delete_favorite(
        request: Request, login_user: UserPayload, resource_type: int, resource_id: str
    ) -> bool:
        """删除收藏"""
        try:
            # 查找用户对该资源的收藏
            existing_favorites = FavoriteResourceDao.get_favorites_by_resource(
                resource_type, resource_id
            )
            user_favorite = None
            for fav_resource in existing_favorites:
                favorite = FavoriteDao.get_favorite(fav_resource.favorite_id)
                if favorite and favorite.user_id == login_user.user_id:
                    user_favorite = favorite
                    break

            if not user_favorite:
                raise FavoriteNotFoundError()

            # 删除收藏资源关联
            FavoriteResourceDao.remove_resource(
                user_favorite.id, resource_type, resource_id
            )

            # 检查该收藏是否还有其他资源，如果没有则删除收藏记录
            remaining_resources = FavoriteResourceDao.get_resources_by_favorite(
                user_favorite.id
            )
            if not remaining_resources[0]:  # remaining_resources 是 (list, count) 元组
                FavoriteDao.delete_favorite(user_favorite.id)

            logger.info(
                f"用户 {login_user.user_id} 取消收藏了 {resource_type}:{resource_id}"
            )
            return True

        except Exception as e:
            logger.error(f"删除收藏失败: {str(e)}")
            if isinstance(e, FavoriteNotFoundError):
                raise e
            raise FavoriteDeleteError(str(e))

    @staticmethod
    def check_favorite(
        request: Request, login_user: UserPayload, resource_type: int, resource_id: str
    ) -> Dict[str, Any]:
        """检查是否已收藏"""
        try:
            # 查找用户对该资源的收藏
            existing_favorites = FavoriteResourceDao.get_favorites_by_resource(
                resource_type, resource_id
            )
            user_favorite = None
            for fav_resource in existing_favorites:
                favorite = FavoriteDao.get_favorite(fav_resource.favorite_id)
                if favorite and favorite.user_id == login_user.user_id:
                    user_favorite = favorite
                    break

            return {
                "is_favorite": user_favorite is not None,
                "favorite_id": user_favorite.id if user_favorite else None,
            }
        except Exception as e:
            logger.error(f"检查收藏状态失败: {str(e)}")
            raise FavoriteCheckError(str(e))

    @staticmethod
    def batch_check_favorites(
        request: Request,
        login_user: UserPayload,
        resource_type: int,
        resource_ids: List[int],
    ) -> Dict[str, Any]:
        """批量检查收藏状态"""
        try:
            # 获取该用户所有的收藏
            user_favorites, _ = FavoriteDao.get_favorites_by_user(login_user.user_id)
            user_favorite_ids = [f.id for f in user_favorites]

            # 获取所有相关资源的收藏关联
            all_favorite_resources = []
            for resource_id in resource_ids:
                favorite_resources = FavoriteResourceDao.get_favorites_by_resource(
                    resource_type, resource_id
                )
                all_favorite_resources.extend(favorite_resources)

            # 构建用户收藏状态映射
            favorite_map = {}
            for fav_resource in all_favorite_resources:
                if fav_resource.favorite_id in user_favorite_ids:
                    favorite_map[fav_resource.resource_id] = fav_resource.favorite_id

            result = {}
            for resource_id in resource_ids:
                result[str(resource_id)] = {
                    "is_favorite": resource_id in favorite_map,
                    "favorite_id": favorite_map.get(resource_id),
                }

            return {"check_results": result}

        except Exception as e:
            logger.error(f"批量检查收藏状态失败: {str(e)}")
            raise FavoriteBatchCheckError(str(e))

    @staticmethod
    def get_user_favorites(
        request: Request, login_user: UserPayload, page: int = 1, limit: int = 10
    ) -> Dict[str, Any]:
        """获取用户收藏列表"""
        try:
            # 获取用户的所有标签
            favorites, total = FavoriteDao.get_favorites_by_user(
                user_id=login_user.user_id,
                keyword=None,  # 可以扩展支持关键词搜索
                page=page,
                limit=limit,
            )

            # 获取收藏资源的详细信息
            favorite_list = []
            for favorite in favorites:
                favorite_data = favorite.to_dict()
                favorite_list.append(favorite_data)

            return {
                "items": favorite_list,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            }

        except Exception as e:
            logger.error(f"获取用户收藏列表失败: {str(e)}")
            raise FavoriteListError(str(e))

    @staticmethod
    def supplement_resource_info(favorite: FavoriteResource) -> dict:
        """补充收藏资源的详细信息"""
        resource_detail = None
        type = int(favorite.resource_type)
        if type == FavoriteType.ASSISTANT.value:
            # 查询助手信息
            from bisheng.database.models.assistant import AssistantDao

            assistant = AssistantDao.get_one_assistant(str(favorite.resource_id))
            if assistant:
                resource_detail = {
                    "type": FavoriteType.ASSISTANT.value,
                    "id": str(assistant.id),
                    "name": assistant.name,
                    "description": assistant.desc or "",
                    "logo": assistant.logo or "",
                    "status": assistant.status,
                    "create_time": (
                        assistant.create_time.isoformat()
                        if assistant.create_time
                        else None
                    ),
                    "update_time": (
                        assistant.update_time.isoformat()
                        if assistant.update_time
                        else None
                    ),
                }
        elif type == FavoriteType.FLOW.value:
            # 查询工作流信息
            from bisheng.database.models.flow import FlowDao

            flow = FlowDao.get_flow_by_id(str(favorite.resource_id))
            if flow:
                resource_detail = {
                    "type": FavoriteType.FLOW.value,
                    "id": str(flow.id),
                    "name": flow.name,
                    "description": flow.description or "",
                    "logo": flow.logo or "",
                    "status": flow.status,
                    "flow_type": flow.flow_type,
                    "create_time": (
                        flow.create_time.isoformat() if flow.create_time else None
                    ),
                    "update_time": (
                        flow.update_time.isoformat() if flow.update_time else None
                    ),
                }
        elif type == FavoriteType.MODEL.value:
            # 查询模型信息
            from bisheng.database.models.llm_server import LLMDao

            model = LLMDao.get_model_by_id(str(favorite.resource_id))
            if model:
                resource_detail = {
                    "type": FavoriteType.MODEL.value,
                    "id": str(model.id),
                    "name": model.name,
                    "model_name": model.model_name,
                    "model_type": model.model_type,
                    "description": model.description or "",
                    "status": model.status,
                    "create_time": (
                        model.create_time.isoformat() if model.create_time else None
                    ),
                    "update_time": (
                        model.update_time.isoformat() if model.update_time else None
                    ),
                }
        elif type == FavoriteType.SESSION.value:
            # 查询会话信息
            from bisheng.database.models.session import MessageSessionDao

            session = MessageSessionDao.get_one(str(favorite.resource_id))
            if session:
                resource_detail = {
                    "type": FavoriteType.SESSION.value,
                    "id": session.chat_id,
                    "name": session.flow_name,
                    "chat_id": session.chat_id,
                    "flow_id": session.flow_id,
                    "flow_name": session.flow_name,
                    "flow_description": session.flow_description or "",
                    "create_time": (
                        session.create_time.isoformat() if session.create_time else None
                    ),
                    "update_time": (
                        session.update_time.isoformat() if session.update_time else None
                    ),
                }

        return resource_detail

    @staticmethod
    def add_to_default_favorite(
        request: Request, login_user: UserPayload, resource_type: int, resource_id: str
    ) -> Favorite:
        """将资源添加到默认收藏夹，如果默认收藏夹不存在就创建一个"""
        try:
            # 获取用户的默认收藏夹
            default_favorite = FavoriteDao.get_favorite_default(login_user.user_id)

            # 检查资源是否已经在默认收藏夹中
            existing_resources = FavoriteResourceDao.get_resources_by_favorite(
                default_favorite.id
            )
            for resource in existing_resources[
                0
            ]:  # existing_resources 是 (list, count) 元组
                if (
                    resource.resource_type == resource_type
                    and resource.resource_id == resource_id
                ):
                    logger.info(f"资源 {resource_type}:{resource_id} 已在默认收藏夹中")
                    return default_favorite

            # 添加资源到默认收藏夹
            favorite_resource = FavoriteResource(
                favorite_id=default_favorite.id,
                resource_type=resource_type,
                resource_id=resource_id,
            )
            FavoriteResourceDao.add_resource(favorite_resource)

            logger.info(
                f"用户 {login_user.user_id} 将资源 {resource_type}:{resource_id} 添加到默认收藏夹"
            )
            return default_favorite

        except Exception as e:
            logger.error(f"添加到默认收藏夹失败: {str(e)}")
            raise FavoriteCreateError(f"添加到默认收藏夹失败: {str(e)}")

    @staticmethod
    def get_default_favorite_resources(
        request: Request,
        login_user: UserPayload,
        resource_type: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """获取默认收藏夹中的所有资源列表"""
        try:
            # 获取用户的默认收藏夹
            default_favorite = FavoriteDao.get_favorite_default(login_user.user_id)

            # 获取默认收藏夹中的所有资源
            all_resources, total = FavoriteResourceDao.get_resources_by_favorite(
                default_favorite.id, resource_type, page, limit
            )

            # 构建返回数据
            resource_list = []
            for resource in all_resources:
                resource_data = {
                    "id": resource.id,
                    "favorite_name": default_favorite.name,
                    "resource_type": resource.resource_type,
                    "resource_id": resource.resource_id,
                    "created_at": (
                        resource.create_time if resource.create_time else None
                    ),
                    "favorite_id": resource.favorite_id,
                }

                # 根据资源类型查询具体的资源信息
                resource_detail = None
                try:
                    resource_detail = FavoriteApiService.supplement_resource_info(
                        resource
                    )
                except Exception as detail_error:
                    logger.warning(
                        f"获取资源详情失败: {resource.resource_type}:{resource.resource_id}, 错误: {str(detail_error)}"
                    )

                # 添加资源详情到返回数据中
                if resource_detail:
                    resource_data["resource_detail"] = resource_detail

                resource_list.append(resource_data)

            return {
                "items": resource_list,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
                "favorite_info": {
                    "id": default_favorite.id,
                    "name": default_favorite.name,
                    "description": default_favorite.description,
                },
            }

        except Exception as e:
            logger.error(f"获取默认收藏夹资源列表失败: {str(e)}")
            raise FavoriteListError(f"获取默认收藏夹资源列表失败: {str(e)}")

    @staticmethod
    def remove_from_default_favorite(
        request: Request, login_user: UserPayload, resource_type: int, resource_id: str
    ) -> bool:
        """从默认收藏夹中删除资源"""
        try:
            # 获取用户的默认收藏夹
            default_favorite = FavoriteDao.get_favorite_default(login_user.user_id)

            # 删除资源关联
            FavoriteResourceDao.remove_resource(
                default_favorite.id, resource_type, resource_id
            )

            logger.info(
                f"用户 {login_user.user_id} 从默认收藏夹删除了资源 {resource_type}:{resource_id}"
            )
            return True

        except Exception as e:
            logger.error(f"从默认收藏夹删除资源失败: {str(e)}")
            raise FavoriteDeleteError(f"从默认收藏夹删除资源失败: {str(e)}")
