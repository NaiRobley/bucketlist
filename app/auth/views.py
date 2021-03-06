import re
from flask.views import MethodView
from flask import make_response, request, jsonify
from flask_bcrypt import Bcrypt

from . import auth_blueprint
from app.models import User


class RegistrationView(MethodView):
    """
    Class to register a new user
    """
    def post(self):
        """
        Handle POST request from /auth/register/
        """
        if request.data["username"].strip(" ") and len(request.data["password"]) >= 6:
            # Check if user exists
            user = User.query.filter_by(
                username=request.data["username"]).first()

            user_email = User.query.filter_by(
                        email=request.data["email"]).first()

            match=re.search(r"^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", 
                        request.data['email'])

            if not user and not user_email and match:
                try:
                    post_data = request.data

                    username = post_data["username"]
                    email = post_data["email"]
                    password = post_data["password"]
                    user = User(username=username, password=password,
                                email=email)
                    user.save()

                    response = {
                        "message": "You registered successfully. Log in."
                    }

                    return make_response(jsonify(response)), 201

                except Exception as e:
                    response = {
                        "message": str(e)
                    }

                    return make_response(jsonify(response)), 401

            elif not user and not match:
                response = {
                    "message": "Invalid email. Please try again"
                }

                return make_response(jsonify(response)), 400

            elif not user and user_email:
                response = {
                    "message": "Email is already registered. try again"
                }
                return make_response(jsonify(response)), 409
            # If user exists
            else:
                response = {
                    "message": "User already exists. Please login"
                }

                return make_response(jsonify(response)), 409

        elif request.data["username"].strip(" ") and 0 < len(request.data["password"]) < 6:
            # Either username or password is not provided
            response = {
                "message": "Error. The password should be at least 6 characters"
            }

            return make_response(jsonify(response)), 400
            
        else:
            # Either username or password is not provided
            response = {
                "message": "Error. The username or password cannot be empty"
            }

            return make_response(jsonify(response)), 400


class LoginView(MethodView):
    """
    Class to handle login
    """
    def post(self):
        """Handle POST request for /auth/login/"""
        try:
            if request.data["username"].strip(" ") and request.data["password"]:
                user = User.query.filter_by(
                    username=request.data["username"]).first()

                # Authenticate the user using the password
                if user and user.check_password(request.data["password"]):
                    # Generate the access token which will be used
                    # as the authorization header
                    access_token = user.generate_token(user.id)
                    if access_token:
                        response = {
                            "message": "You logged in successfully.",
                            "access_token": access_token.decode(),
                            "username": user.username,
                            "email": user.email
                        }

                        return make_response(jsonify(response)), 200

                else:
                    # If the user does not exist or password is wrong
                    response = {
                        "message": "Invalid username or password. "
                                   "Please try again."
                    }

                    return make_response(jsonify(response)), 401
            else:
                # Either username or password is not provided
                response = {
                    "message": "Error. The username or password "
                               "cannot be empty"
                }

                return make_response(jsonify(response)), 400

        except Exception as e:
            response = {
                "message": str(e)
            }

            # Return 500(Internal Server Error)
            return make_response(jsonify(response)), 500

class UserView(MethodView):
    """
    Class to handle updating of details
    """
    def put(self):
        """Handle POST request for /auth/user/"""
        try:
            if request.data["username"].strip(" ") and request.data["password"]:
                user = User.query.filter_by(
                        username=request.data["username"]).first()
                all_usernames = [user.username for user in User.query.all()]
                all_emails = [user.email for user in User.query.all()]

                # Authenticate the user using the password
                if user and user.check_password(request.data["password"]):
                    new_username = request.data.get("new_username", "")
                    new_password = request.data.get("new_password", "")
                    new_email = request.data.get("new_email", "")
                    # Modify their details
                    if new_username:
                        if new_username not in all_usernames:
                            user.username = request.data["new_username"].strip(" ")
                            user.save()
                            response = {
                                "message": "Username changed successfully",
                                "username": new_username
                                }

                            return make_response(jsonify(response)), 201
                        else:
                            response = {
                                "message": "Username already taken. Try another one"
                            }
                            return make_response(jsonify(response)), 409

                    elif new_email:
                        match = re.search(r"^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", 
                                request.data['new_email'])

                        if new_email not in all_emails and match:
                            user.email = request.data["new_email"]
                            user.save()
                            response = {
                                "message": "Email changed successfully",
                                "email": new_email
                                }

                            return make_response(jsonify(response)), 201

                        elif new_email not in all_emails and not match:
                            response = {
                                    "message": "Invalid email. Please try again"
                                    }
                            return make_response(jsonify(response)), 400

                        else:
                            response = {
                                "message": "Email already registered. Try another one"
                            }
                            return make_response(jsonify(response)), 409

                    elif new_password:
                        if user.check_password(request.data["new_password"]):
                            response = {
                                "message": "Password cannot be the same as the old one. Try again"
                            }
                            return make_response(jsonify(response)), 409
                        
                        elif len(new_password) < 6:
                            response = {
                                "message": "Error. The password should be at least 6 characters"
                            }
                            return make_response(jsonify(response)), 400

                        else:
                            user.password = Bcrypt().generate_password_hash(request.data["new_password"]).decode()
                            # user.password = request.data["new_password"]
                            user.save()
                            response = {
                                "message": "Password changed successfully"
                                }
                            return make_response(jsonify(response)), 201
                    else:
                        response = {
                            "message": "All fields cannot be empty"
                        }
                        return make_response(jsonify(response)), 400

                else:
                    # If the user does not exist or password is wrong
                    response = {
                        "message": "Invalid username or password. "
                                   "Please try again."
                    }

                    return make_response(jsonify(response)), 401
            else:
                # Either username or password is not provided
                response = {
                    "message": "Error. The username or password "
                               "cannot be empty"
                }

                return make_response(jsonify(response)), 400

        except Exception as e:
            response = {
                "message": str(e)
            }

            # Return 500(Internal Server Error)
            return make_response(jsonify(response)), 500


# Define API resource
registration_view = RegistrationView.as_view("register_view")
login_view = LoginView.as_view("login_view")
user_view = UserView.as_view("user_view")

# Define the rule for the registration URL /auth/register/
# add rule to blueprint
auth_blueprint.add_url_rule("/auth/register/", view_func=registration_view,
                            methods=["POST"])

# Define rule for login URL /auth/login/
# add rule to blueprint
auth_blueprint.add_url_rule("/auth/login/", view_func=login_view,
                            methods=["POST"])

# Define rule for URL /auth/user/
# add rule to blueprint
auth_blueprint.add_url_rule("/auth/user/", view_func=user_view,
                            methods=["PUT"])
