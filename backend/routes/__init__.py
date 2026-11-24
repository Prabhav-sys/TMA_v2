def register_routes(app):
    from . import admin, auth, staff, user
    for module in (auth, admin, staff, user):
        app.register_blueprint(module.bp)
