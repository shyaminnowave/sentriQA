
class DatabaseRouter(object):
    route_app_labels = {
        'core': 'core',
    }

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.route_app_labels[model._meta.app_label]
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.route_app_labels[model._meta.app_label]
        return 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == self.route_app_labels[app_label]
        elif db in self.route_app_labels.values():
            return False
        return db == 'default'
