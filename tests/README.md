Follow these instructions:

`virtualenv /tmp/test-lamnfyc`

`/tmp/test-lamnfyc/bin/pip install -r tests/requirements.txt`

`/tmp/test-lamnfyc/bin/nosetests`

To test PEP8-ness

`/tmp/test-lamnfyc/bin/flake8 lamnfyc`

And when you're done testing:

`rm -rf /tmp/test-lamnfyc`
