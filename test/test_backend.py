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
from random import randint
import unittest
from unittest import mock

import pytest

from qiskit import transpile, QuantumCircuit
from qiskit.providers.exceptions import JobError
from requests.models import Response

from qiskit_aqt_provider import AQTProvider


def demo_circuit():
    qc = QuantumCircuit(3, 3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(0, 2)
    qc.barrier(range(3))
    qc.measure(range(3), range(3))
    return qc


TRANSPILED_DEMO_CIRCUIT = \
    [
        ['Y', 0.5, [0]],
        ['X', 0.5, [0]],
        ['X', 0.5, [0]],
        ['Y', -0.5, [0]],
        ['MS', -0.5, [0, 1]],
        ['X', 0.5, [0]],
        ['X', -0.5, [1]],
        ['MS', -0.5, [0, 2]],
        ['X', 0.5, [0]],
        ['Y', 0.5, [0]],
        ['X', -0.5, [2]]
    ]


# This method will be used by the mock to replace requests.put
def mock_api_factory(no_qubits, transpiled_circuit, samples):
    JOB_ID = f"job_{randint(1000, 2000)}"

    def mocked_api_response(*args, **kwargs):
        response = Response()
        response.status_code = 200

        url = args[0]
        assert url == 'https://gateway.aqt.eu/marmot/sim/'

        payload = kwargs['data']

        # API Call with invalid token
        access_token = payload['access_token']
        if access_token != "VALID_TOKEN":
            invalid_token_response = {
                'id': JOB_ID,
                'status': 'error'
            }

            response_content = json.dumps(invalid_token_response)
            response._content = str.encode(response_content)
            return response

        # API call to request the result
        if 'id' in payload:
            id = payload['id']
            access_token = payload['access_token']
            assert id == JOB_ID
            fake_response = {
                'id': JOB_ID,
                'no_qubits': 3,
                'received': transpiled_circuit,
                'repetitions': 100,
                'samples': samples,
                'status': 'finished'
            }

            response_content = json.dumps(fake_response)
            response._content = str.encode(response_content)
            return response

        # API call to submit a circuit
        circuit = json.loads(payload['data'])
        assert circuit == transpiled_circuit

        repetitions = payload['repetitions']
        assert repetitions == 100
        # circuit = payload['data']
        # assert circuit == TRANSPILED_TEST_CIRCUIT
        assert no_qubits == payload['no_qubits']

        queued_response = {
            'id': JOB_ID,
            'status': 'queued'
        }

        response_content = json.dumps(queued_response)
        response._content = str.encode(response_content)
        return response

    return mocked_api_response


class TestBackend(unittest.TestCase):

    @mock.patch(
        'qiskit_aqt_provider.aqt_backend.requests.put',
        side_effect=mock_api_factory(
            no_qubits=3,
            transpiled_circuit=TRANSPILED_DEMO_CIRCUIT,
            samples=50 * [0, 7]
        )
    )
    def test_backend(self, mock_get):
        aqt = AQTProvider("VALID_TOKEN")
        backend = aqt.backends.aqt_qasm_simulator

        qc = demo_circuit()
        trans_qc = transpile(qc, backend)

        job = backend.run(trans_qc)
        counts = job.get_counts()
        assert counts == {'000': 50, '111': 50}

    @mock.patch(
        'qiskit_aqt_provider.aqt_backend.requests.put',
        side_effect=mock_api_factory(
            no_qubits=3,
            transpiled_circuit=TRANSPILED_DEMO_CIRCUIT,
            samples=50 * [0, 7])
    )
    def test_backend_invalid_token(self, mock_get):
        aqt = AQTProvider("INVALID_TOKEN")
        backend = aqt.backends.aqt_qasm_simulator

        qc = demo_circuit()
        trans_qc = transpile(qc, backend)

        job = backend.run(trans_qc)
        with pytest.raises(JobError):
            job.get_counts()
