class LoginForm:

    @staticmethod
    def validate(form):

        if not form.get("username"):
            return False, "Username wajib diisi"

        if not form.get("password"):
            return False, "Password wajib diisi"

        return True, "Valid"