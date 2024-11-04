from flask import jsonify

def handle_404(error=None, error_msg="Resource not found"):
    return jsonify({"error": error_msg}), 404

def handle_400(error=None, error_msg="Bad request"):
    return jsonify({"error": error_msg}), 400

def handle_401(error=None, error_msg="Unauthorized"):
    return jsonify({"error": error_msg}), 401

def handle_403(error=None, error_msg="Forbidden"):
    return jsonify({"error": error_msg}), 403

def handle_500(error=None, error_msg="Internal server error"):
    return jsonify({"error": error_msg}), 500

def handle_413(error=None, error_msg="File is too large. Maximum allowed size is 16 MB."):
    return jsonify({"error": error_msg}), 413