import os
import tempfile

import pytest

@pytest.fixture
def client():
    print "Hello Test"