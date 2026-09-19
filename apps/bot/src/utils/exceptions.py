class AppError(Exception):
    pass

class ConfigError(AppError):
    pass

class EnvVarMissingError(ConfigError):
    def __init__(self, var_name: str):
        self.var_name = var_name
        super().__init__(f"Variable {var_name} is not specified")
