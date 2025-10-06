from rest_framework.renderers import JSONRenderer



class ResponseInfo:

    def __init__(self, user=None, **args):
        self.response = {
            "status": args.get('status', True),
            "status_code": args.get('status_code', ''),
            "data": args.get('data', {}),
            "message": args.get('message', '')
        }