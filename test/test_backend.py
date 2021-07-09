# -*- coding: utf-8 -*-
# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import json
import unittest
from unittest import mock

from qiskit import transpile, QuantumCircuit
from requests.models import Response

from qiskit_aqt_provider import AQTProvider

# This method will be used by the mock to replace requests.put
def mocked_api_response(*args, **kwargs):

    JOB_ID = "abc123"

    response = Response()
    response.status_code = 200

    url = args[0]
    assert url == 'https://gateway.aqt.eu/marmot/sim/'

    payload = kwargs['data']
    headers = kwargs['headers']

    # API call to request the result
    if 'id' in payload:
        id = payload['id']
        assert id == JOB_ID
        fake_response = {
            'id': JOB_ID,
            'no_qubits': 2,
            'received': '[["Y", 0.5, [0]]',
            'repetitions': 100,
            'samples': [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                        3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                        3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                        3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                        3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3,
                        3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                        3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                        3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                        3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                        3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                        3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                        3, 3],
            'status': 'finished'
        }

        response_content = json.dumps(fake_response)
        response._content = str.encode(response_content)
        return response

    # API call to submit a circuit

    #circuit = payload['data']
    #print(circuit)


    access_token = payload['access_token']
    if access_token == "VALID_TOKEN":
        repetitions = payload['repetitions']
        assert repetitions == 100
        #no_qubits = payload['no_qubits']


        queued_response = {
            'id': JOB_ID,
            'status': 'queued'
        }

        response_content = json.dumps(queued_response)
        response._content = str.encode(response_content)
        return response
    else:
        invalid_token_response = {
            'id': JOB_ID,
            'status': 'error'
        }

        response_content = json.dumps(invalid_token_response)
        response._content = str.encode(response_content)
        return response




class TestBackend(unittest.TestCase):

    @mock.patch('qiskit_aqt_provider.aqt_backend.requests.put', side_effect=mocked_api_response)
    def test_backend(self, mock_get):
        aqt = AQTProvider("VALID_TOKEN")
        backend = aqt.backends.aqt_qasm_simulator

        qc = QuantumCircuit(5, 4)
        qc.x(4)
        qc.h(range(5))
        qc.barrier()
        qc.cx([0, 1, 3], [4, 4, 4])
        qc.barrier()
        qc.h(range(4))
        qc.measure(range(4), range(4))

        trans_qc = transpile(qc, backend)

        job = backend.run(trans_qc)
        print(job.get_counts())
