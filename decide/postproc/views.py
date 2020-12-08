from rest_framework.views import APIView
from rest_framework.response import Response


class PostProcView(APIView):

    def identity(self, options):
        out = []

        for opt in options:
            out.append({
                **opt,
                'postproc': opt['votes'],
            });

        out.sort(key=lambda x: -x['postproc'])
        return Response(out)

    def post(self, request):
        """
         * type: IDENTITY | DHONT
         * options: [
            {
             option: str,
             number: int,
             votes: int,
             ...extraparams
            }
           ]
	 * seats: int
        """

        t = request.data.get('type')
        opts = request.data.get('options', [])
	s = request.data.get('seats')

        if t == 'IDENTITY':
            return self.identity(opts)

	elif t == 'DHONT':
	    return self.dhont(opts,s)

        return Response({})
