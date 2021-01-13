from functools import wraps

def shib_meta_to_user(view_func):
    """
    Decorator that adds shib_meta dict from request.session to request.user
    This could also be done in the middleware, but just sometimes need to access the attributes; and request.session is usually the better place
    We use this, so we do not need to pass around a request to all the backend deposit functions that only care about the user
    """
    @wraps(view_func)
    def inner(request, *args, **kwargs):
        request.user.shib = request.session.get('shib', {})
        return view_func(request, *args, **kwargs)
    return inner
