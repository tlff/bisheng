from bisheng.api.errcode.base import BaseErrorCode


class FavoriteNotFoundError(BaseErrorCode):
    Code = 15001
    Msg = '收藏不存在'


class FavoriteAlreadyExistsError(BaseErrorCode):
    Code = 15002
    Msg = '资源已收藏'


class FavoriteResourceNotFoundError(BaseErrorCode):
    Code = 15003
    Msg = '收藏资源不存在'


class FavoriteCreateError(BaseErrorCode):
    Code = 15010
    Msg = '创建收藏失败'


class FavoriteDeleteError(BaseErrorCode):
    Code = 15011
    Msg = '删除收藏失败'


class FavoriteCheckError(BaseErrorCode):
    Code = 15012
    Msg = '检查收藏状态失败'


class FavoriteBatchCheckError(BaseErrorCode):
    Code = 15013
    Msg = '批量检查收藏状态失败'


class FavoriteListError(BaseErrorCode):
    Code = 15014
    Msg = '获取收藏列表失败'