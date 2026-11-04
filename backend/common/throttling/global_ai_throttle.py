from rest_framework.throttling import SimpleRateThrottle


class GlobalAiThrottle(SimpleRateThrottle):
    """
    One shared daily limit on AI calls, across all users and IPs.

    The per-user limits can be dodged by a visitor who forges the X-Forwarded-For header on
    the public AI search. This cap can't be: it has one counter, so it limits what a public
    demo can spend on Claude in a day.
    """

    scope = "ai_global"

    def get_cache_key(self, request, view):
        return "throttle_ai_global"
