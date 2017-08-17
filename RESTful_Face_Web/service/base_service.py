class BaseService:
    def is_valid_input_data(self, data=None):
        raise NotImplementedError("is_valid_input_data() Not Implement yet!")

    def execute(self, *args, **kwargs):
        raise NotImplementedError("execute() Not Implemented yet !")
