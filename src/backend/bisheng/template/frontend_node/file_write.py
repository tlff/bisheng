from bisheng.template.field.base import TemplateField
from bisheng.template.frontend_node.base import FrontendNode
from bisheng.template.template.base import Template


class FileWriteNode(FrontendNode):
    name: str = 'FileWriteNode'
    template: Template = Template(
        type_name='file_write',
        fields=[
            TemplateField(
                field_type='str',
                required=True,
                show=True,
                name='file_path',
                display_name='文件路径',
                placeholder='例如：/path/to/output.txt',
                description='要写入的文件完整路径',
            ),
            TemplateField(
                field_type='str',
                required=True,
                show=True,
                multiline=True,
                name='content',
                display_name='文件内容',
                placeholder='请输入要写入文件的内容',
                description='要写入到文件中的内容',
            ),
            TemplateField(
                field_type='str',
                required=False,
                show=True,
                name='encoding',
                display_name='编码格式',
                placeholder='utf-8',
                default='utf-8',
                description='文件编码格式，默认为utf-8',
            ),
        ],
    )
    description: str = '文件写入节点，将接受到的内容写入到指定文件中'
    base_classes: list[str] = ['file_write']
    output_types: list[str] = ['file_write']
    display_name: str = '文件写入'