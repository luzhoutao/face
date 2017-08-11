from .base_service import BaseService

class QualityCheckService(BaseService):
    def execute(self, *args, **kwargs):
        return "good quality!"