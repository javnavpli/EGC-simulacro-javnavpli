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

    def relativa(self, opts):
        out= []
        numvotos=0
        for opt in options:
            numvotos=opt['votes']+numvotos
            out.append({
                **opt,
                'postproc':opt['votes']
            })

        while len(out)>1:
            if(max(cocientes)>0.5):
                cocientes = []
                for i in range(len(out)):
                    cocientes.append(out[i]['votes']/numvotos)
                    perdedor=cocientes.index(min(cocientes))
                    del cocientes[perdedor]
            else:
                out.sort(key=lambda x:-x['votes'])
                return Response(out)

    def post(self, request):
        """
         * type: IDENTITY | EQUALITY | WEIGHT
         * options: [
            {
             option: str,
             number: int,
             votes: int,
             ...extraparams
            }
           ]
        """

        t = request.data.get('type')
        opts = request.data.get('options', [])

        if t == 'IDENTITY':
            return self.identity(opts)
        elif t == 'RELATIVA':
            return self.relativa(opts)
        return Response({})
