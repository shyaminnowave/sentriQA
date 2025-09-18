
class AuthRouter:

    def db_for_read(self, model, **hints):
        pass

    def db_for_write(self, model, **hints):
        pass

    def allow_syncdb(self, model, **hints):
        pass