import os
from typing import Any, Dict

from loguru import logger

from bisheng.workflow.nodes.base import BaseNode


class FileWriteNode(BaseNode):
    """文件写入节点，将接受到的内容写入到文件中"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化节点参数
        self._file_path = self.node_params.get('file_path', '')
        self._content = self.node_params.get('content', '')
        self._encoding = self.node_params.get('encoding', 'utf-8')

    def _run(self, unique_id: str) -> Dict[str, Any]:
        """执行节点运行，将内容写入文件"""
        # 解析模板变量
        content, _ = self.parse_msg_with_variables(self._content)
        file_path, _ = self.parse_msg_with_variables(self._file_path)
        encoding, _ = self.parse_msg_with_variables(self._encoding)

        try:
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                logger.debug(f'Created directory: {dir_path}')

            # 写入文件
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            logger.info(f'Successfully wrote content to file: {file_path}')

            # 返回结果
            return {
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'success': True
            }
        except Exception as e:
            logger.exception(f'Failed to write file: {file_path}')
            raise Exception(f'Failed to write file: {str(e)}')