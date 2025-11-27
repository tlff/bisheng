# 毕昇异步任务模块
# 知识库任务热重载
celery -A bisheng.worker.main worker -l info -c 10 -P threads -Q knowledge_celery -n knowledge@%h 

# 工作流任务热重载
celery -A bisheng.worker.main worker -l info -c 100 -P threads -Q workflow_celery -n workflow@%h 