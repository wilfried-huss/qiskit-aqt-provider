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

TRANSPILED_TEST_CIRCUIT = \
    [
        ["Y", 0.5, [0]],
        ["X", 0.5, [0]],
        ["X", 0.5, [0]],
        ["Y", -0.5, [0]],
        ["MS", -0.5, [0, 1]],
        ["X", 0.5, [0]],
        ["X", -0.5, [1]],
        ["MS", -0.5, [0, 2]],
        ["X", 0.5, [0]],
        ["Y", 0.5, [0]],
        ["X", -0.5, [2]]
    ]


# This method will be used by the mock to replace requests.put
def mocked_api_response(*args, **kwargs):

    JOB_ID = "abc123"

    response = Response()
    response.status_code = 200

    url = args[0]
    assert url == 'https://gateway.aqt.eu/marmot/sim/'

    payload = kwargs['data']

    # API call to request the result
    if 'id' in payload:
        id = payload['id']
        assert id == JOB_ID
        fake_response = {
            'id': JOB_ID,
            'no_qubits': 2,
            'received': TRANSPILED_TEST_CIRCUIT,
            'repetitions': 100,
            'samples': 50 * [0, 7],
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
        #circuit = payload['data']
        #assert circuit == TRANSPILED_TEST_CIRCUIT
        no_qubits = payload['no_qubits']
        assert no_qubits == 3

        queued_response = {
            'id': JOB_ID,
            'status': 'queued'
        }

        response_content = json.dumps(queued_response)
        response._content = str.encode(response_content)
        return response

    # Invalid token
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

        qc = QuantumCircuit(3, 3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(0, 2)
        qc.barrier(range(3))
        qc.measure(range(3), range(3))

        trans_qc = transpile(qc, backend)

        job = backend.run(trans_qc)
        counts = job.get_counts()
        assert counts == {'000': 50, '111': 50}
