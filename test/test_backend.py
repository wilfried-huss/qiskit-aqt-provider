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

import os
import json
from random import randint

from requests.models import HTTPError, Response

from qiskit import QuantumCircuit, transpile
from qiskit_aqt_provider import AQTProvider

import pytest


# To run the test using the AQT-simulator set the environment variable
# ACCESS_TOKEN to a valid token for the AQT api.
USE_MOCK_API = not bool(os.environ.get("ACCESS_TOKEN", False))
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "VALID_MOCK_ACCESS_TOKEN")


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
        url = args[0]
        assert url == 'https://gateway.aqt.eu/marmot/sim/'

        status_code = 200

        payload = kwargs['data']

        # API Call with invalid token
        access_token = payload['access_token']
        if access_token != "VALID_MOCK_ACCESS_TOKEN":
            status_code = 401
            invalid_token_response = {
                'id': JOB_ID,
                'status': 'error'
            }

            response_content = json.dumps(invalid_token_response)
        elif 'id' in payload:
            # API call to request the result
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
        else:
            # API call to submit a circuit
            # circuit = json.loads(payload['data'])
            # assert circuit == transpiled_circuit

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

        response = Response()
        response.status_code = status_code
        response._content = str.encode(response_content)  # pylint: disable=protected-access
        return response

    return mocked_api_response


def test_backend(mocker):
    if USE_MOCK_API:
        mocker.patch(
            'qiskit_aqt_provider.aqt_backend.requests.put',
            side_effect=mock_api_factory(
                no_qubits=3,
                transpiled_circuit=TRANSPILED_DEMO_CIRCUIT,
                samples=50 * [0, 7]
            )
        )

    aqt = AQTProvider(ACCESS_TOKEN)
    backend = aqt.get_backend('aqt_qasm_simulator')

    qc = demo_circuit()
    trans_qc = transpile(qc, backend)

    job = backend.run(trans_qc)
    counts = job.get_counts()
    assert counts['000'] + counts['111'] == 100


def test_backend_invalid_token(mocker):
    if USE_MOCK_API:
        mocker.patch(
            'qiskit_aqt_provider.aqt_backend.requests.put',
            side_effect=mock_api_factory(
                no_qubits=3,
                transpiled_circuit=TRANSPILED_DEMO_CIRCUIT,
                samples=50 * [0, 7]
            )
        )

    aqt = AQTProvider("INVALID_TOKEN")
    backend = aqt.get_backend('aqt_qasm_simulator')

    qc = demo_circuit()
    trans_qc = transpile(qc, backend)

    with pytest.raises(HTTPError):
        backend.run(trans_qc)
