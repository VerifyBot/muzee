from functools import wraps
import copy


def use_spotify(func):
    """
    Inject the Spotify Client object into the function
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        assert "ctx" in kwargs, "You must provide the ctx object in the kwargs"

        sc = await kwargs["ctx"].spotify.get_client(user=kwargs["ctx"].user)

        # inject the sc object as a parameter
        assert "ctx" in kwargs, "You must provide the ctx object in the kwargs"
        kwargs["ctx"] = copy.copy(kwargs["ctx"])
        kwargs["ctx"].sc = sc

        try:
            return await func(*args, **kwargs)
        finally:
            await sc.close()

    return wrapper
