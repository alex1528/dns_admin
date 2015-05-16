# -*- coding: utf-8 -*-


def authenticate_decorator(func):
    def __authenticate_decorator(*args, **kwargs):
        user_email = self.get_secure_cookie("username")
        if user_email:
            fs = user_email.split("@")
            if fs[1] != "nosa.me":
                self.clear_cookie("username")
                self.write(
                    "You have to logout your current google account and login with your nosa.me account...")
                return
            else:
                apply(func, args, kwargs)
        else:
            self.redirect("/login")

    return __authenticate_decorator
