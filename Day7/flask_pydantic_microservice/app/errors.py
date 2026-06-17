from flask import jsonify


def register_error_handlers(app):

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not Found",
            "message": "The requested URL was not found."
        }), 404

    @app.errorhandler(422)
    def validation_error(error):
        return jsonify({
            "error": "Validation Error",
            "message": "Invalid request payload."
        }), 422

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal Server Error",
            "message": "Something went wrong."
        }), 500